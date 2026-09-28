"""Speech system for Colen.

Real-time text-to-speech backed by a local PocketTTS server
(http://localhost:8000 by default).

By default Colen speaks with the *built-in* PocketTTS voice ``mary`` (sent as
the ``voice_url`` form field), which removes the need to upload a voice-clone
reference and therefore cuts request latency dramatically.  Set the
``COLEN_VOICE_NAME`` environment variable to an empty string or ``file`` to
fall back to cloning the single audio file kept inside the ``/voices``
directory (``voice_wav``).

Usage
-----
    # Speak a piece of text (plays through the system speakers)
    python -m colen.speech "Good evening, Sir."

    # Pipe text over stdin
    echo "Hello" | python -m colen.speech

    # Programmatic use
    from colen.speech import speak
    audio = speak("Good evening, Sir.")   # returns the generated WAV bytes

The module never touches the existing Colen CLI code; it is fully additive.
"""

from __future__ import annotations

import os
import sys
import glob
import hashlib
import io
import wave
import struct
import time
import tempfile
import threading
import warnings
from pathlib import Path
from typing import Iterator, Optional, Tuple

# PocketTTS endpoint (can be overridden with the COLEN_TTS_URL env var).
TTS_URL = os.environ.get("COLEN_TTS_URL", "http://localhost:8000/tts")

# Built-in PocketTTS voice used by default (a server-side preset name such as
# "mary").  Using a built-in voice avoids uploading the /voices reference
# file, which removes a large POST payload and greatly reduces latency.
# Set COLEN_VOICE_NAME to "" or "file" to clone from the /voices file instead.
DEFAULT_VOICE_NAME = os.environ.get("COLEN_VOICE_NAME", "mary")

# How much audio (seconds) is buffered before playback starts while
# streaming.  A small head start keeps the output stream fed even if the
# server's generation briefly dips below real time.
STREAMING_MIN_START_SECONDS = 1.0

# Upper bound (seconds) for the *adaptive* start buffer: when the server
# produces slower than real time, playback is delayed until this much audio
# is buffered so it never stalls mid-sentence.
STREAMING_MAX_START_SECONDS = 5.0

# The ``/voices`` directory.  We resolve it relative to the project root that
# contains this package, but allow an explicit override via COLEN_VOICES_DIR.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
VOICES_DIR = Path(os.environ.get("COLEN_VOICES_DIR", _PROJECT_ROOT / "voices"))

# Cache directory for generated clips.  Fixed phrases (e.g. the startup and
# exit greetings) are spoken identically every time, so a cache hit removes
# *all* synthesis latency — the clip is played straight from disk.
CACHE_DIR = Path(os.environ.get("COLEN_CACHE_DIR", _PROJECT_ROOT / ".colen_cache"))


def _resolve_voices_dir() -> Path:
    """Resolve the active voices directory, honouring a runtime env override."""
    env_dir = os.environ.get("COLEN_VOICES_DIR")
    if env_dir:
        return Path(env_dir)
    return VOICES_DIR

# File extensions we recognise as a voice reference.  PocketTTS accepts
# WAV/MP3/FLAC/OGG/M4A/AAC/WMA, but a WAV is always preferred when present.
AUDIO_EXTENSIONS = ("*.wav", "*.mp3", "*.flac", "*.ogg", "*.m4a", "*.aac", "*.wma")

# Preferred reference format ordering (lower index == preferred).
_EXT_PRIORITY = {".wav": 0, ".mp3": 1, ".flac": 2, ".ogg": 3, ".m4a": 4, ".aac": 5, ".wma": 6}

_REQUESTS_AVAILABLE = False
try:
    import requests  # type: ignore

    _REQUESTS_AVAILABLE = True
except Exception:  # pragma: no cover - exercised only when requests is missing
    requests = None  # type: ignore


def _require_requests() -> None:
    """Raise a helpful error if the ``requests`` dependency is unavailable."""
    if not _REQUESTS_AVAILABLE:
        raise ImportError(
            "The 'requests' package is required for Colen speech. "
            "Install it with:  pip install requests"
        )


# Reusable HTTP session (keep-alive).  Re-opening a TCP connection for every
# utterance costs tens of milliseconds; a session avoids that entirely.
_HTTP_SESSION = requests.Session() if _REQUESTS_AVAILABLE else None


# --------------------------------------------------------------------------- #
# Voice reference discovery
# --------------------------------------------------------------------------- #
def find_voice_file(voices_dir: Optional[os.PathLike] = None) -> Path:
    """Return the single audio file stored inside the voices directory.

    The folder is expected to contain *exactly one* audio file.  The file name
    is never assumed; instead every audio extension is scanned and the only
    matching file is returned.

    Raises:
        FileNotFoundError: if the directory does not exist or contains no
            audio file.
        ValueError: if more than one audio file is present.
    """
    voices_dir = Path(voices_dir) if voices_dir is not None else _resolve_voices_dir()

    if not voices_dir.is_dir():
        raise FileNotFoundError(
            f"Voices directory does not exist: {voices_dir}\n"
            "Place a single audio file (wav/mp3/flac/ogg/m4a/aac/wma) in it."
        )

    candidates: list[Path] = []
    for pattern in AUDIO_EXTENSIONS:
        candidates.extend(voices_dir.glob(pattern))
        # Also catch extensions written in upper/mixed case, since Path.glob
        # on some platforms is case-sensitive.
        candidates.extend(voices_dir.glob(pattern.upper()))
        candidates.extend(voices_dir.glob(pattern.swapcase()))

    # De-duplicate (glob can match the same file via overlapping patterns).
    unique: list[Path] = []
    seen = set()
    for path in candidates:
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        if path.is_file():
            unique.append(path)

    if not unique:
        raise FileNotFoundError(
            f"No audio file found in the voices directory: {voices_dir}\n"
            "Place a single audio file (wav/mp3/flac/ogg/m4a/aac/wma) in it."
        )

    if len(unique) == 1:
        return unique[0]

    # More than one file: fall back to the most recently modified one, but warn
    # loudly so the misconfiguration is obvious.
    unique.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    chosen = unique[0]
    warnings.warn(
        f"Multiple audio files found in {voices_dir}: {[p.name for p in unique]}. "
        f"Using the most recently modified one: {chosen.name}. "
        "The voices folder should contain a single audio file.",
        RuntimeWarning,
        stacklevel=2,
    )
    return chosen


# --------------------------------------------------------------------------- #
# WAV header helpers
# --------------------------------------------------------------------------- #
def _parse_wav_header(header: bytes) -> Tuple[int, int, int, int]:
    """Parse the 44-byte standard WAV header.

    Returns ``(sample_rate, num_channels, bits_per_sample, byte_rate)``.
    """
    if len(header) < 44 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
        raise ValueError("Not a valid WAV stream (RIFF/WAVE header missing).")

    sample_rate = struct.unpack_from("<I", header, 24)[0]
    num_channels = struct.unpack_from("<H", header, 22)[0]
    bits_per_sample = struct.unpack_from("<H", header, 34)[0]
    byte_rate = struct.unpack_from("<I", header, 28)[0]
    return sample_rate, num_channels, bits_per_sample, byte_rate


def _find_wav_data_offset(blob: bytes) -> int:
    """Return the byte offset where the PCM payload of a WAV begins.

    Walks the RIFF chunk tree so extra chunks (fact, list, ...) placed before
    ``data`` are handled correctly.  Falls back to the standard 44-byte
    header layout if no ``data`` chunk is found.
    """
    offset = 12  # skip "RIFF" + size + "WAVE"
    while offset + 8 <= len(blob):
        chunk_id = blob[offset : offset + 4]
        # struct.unpack_from is safe here because we checked bounds above.
        chunk_size = struct.unpack_from("<I", blob, offset + 4)[0]
        if chunk_id == b"data":
            return offset + 8
        # Stop early if a chunk claims an absurd size (streamed placeholder).
        if chunk_size > len(blob) - (offset + 8):
            offset += 8
            continue
        offset += 8 + chunk_size
    return 44  # fallback: standard 44-byte header


def _normalize_wav(wav_bytes: bytes) -> bytes:
    """Return a clean, fully-formed copy of *wav_bytes*.

    PocketTTS streams a WAV whose ``data`` chunk size is a placeholder
    (``2000000000``) because the real size is only known once streaming
    completes.  Many players (notably ``winsound`` and the ``wave`` module)
    trust that field and break as a result.  This rebuilds the WAV with
    correct RIFF/data sizes computed from the actual byte count.
    """
    sample_rate, num_channels, bits_per_sample, _ = _parse_wav_header(wav_bytes[:44])
    bytes_per_sample = bits_per_sample // 8
    bytes_per_frame = num_channels * bytes_per_sample

    data_offset = _find_wav_data_offset(wav_bytes)
    pcm = wav_bytes[data_offset:]
    nframes = len(pcm) // bytes_per_frame

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(num_channels)
        wf.setsampwidth(bytes_per_sample)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm[: nframes * bytes_per_frame])
    return buf.getvalue()


def _wav_duration_seconds(wav_bytes: bytes) -> Optional[float]:
    """Best-effort duration (seconds) of a WAV byte string.

    Duration is derived from the *actual* PCM byte count rather than the
    (possibly placeholder) size stored in the header, so streamed WAVs are
    reported correctly.
    """
    try:
        sample_rate, num_channels, bits_per_sample, _ = _parse_wav_header(wav_bytes[:44])
        if sample_rate <= 0:
            return None
        bytes_per_sample = bits_per_sample // 8
        bytes_per_frame = num_channels * bytes_per_sample
        if bytes_per_frame <= 0:
            return None
        data_offset = _find_wav_data_offset(wav_bytes)
        pcm_len = len(wav_bytes) - data_offset
        nframes = pcm_len // bytes_per_frame
        return nframes / sample_rate
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# PocketTTS client
# --------------------------------------------------------------------------- #
def _resolve_voice_request(
    voice: Optional[str],
    voice_file: Optional[os.PathLike],
) -> Tuple[dict, Optional[Path]]:
    """Build the ``(data, files)`` payload for the ``/tts`` endpoint.

    A built-in voice *name* (e.g. ``"mary"``) is sent as ``voice_url`` and no
    file upload is needed at all.  When no name is configured (or it is set
    to ``"file"``) the single file from the ``/voices`` directory is used as
    ``voice_wav`` (voice cloning).
    """
    name = voice if voice is not None else DEFAULT_VOICE_NAME
    if name and name.strip().lower() != "file":
        return {"voice_url": name}, None

    path = Path(voice_file) if voice_file is not None else find_voice_file()
    if not path.is_file():
        raise FileNotFoundError(f"Voice reference file not found: {path}")
    return {}, path


def stream_speech(
    text: str,
    voice_file: Optional[os.PathLike] = None,
    tts_url: str = TTS_URL,
    timeout: float = 60.0,
    voice: Optional[str] = None,
) -> Iterator[bytes]:
    """Stream speech from PocketTTS for *text*.

    The voice is the built-in PocketTTS preset named by
    :data:`DEFAULT_VOICE_NAME` (default ``mary``) unless *voice* overrides it
    or built-in voices are disabled (``COLEN_VOICE_NAME=""``), in which case
    the single file in the ``/voices`` directory is uploaded as the
    voice-cloning reference (``voice_wav``).  The server response is a
    streamed WAV file; this generator yields the raw bytes as they arrive so
    callers can start playing audio long before the whole utterance has been
    synthesised.

    Yields:
        Chunks of the generated WAV audio (bytes).
    """
    _require_requests()

    data, upload = _resolve_voice_request(voice, voice_file)
    data = {"text": text, **data}

    files = None
    fh = None
    if upload is not None:
        fh = upload.open("rb")
        files = {"voice_wav": (upload.name, fh, "application/octet-stream")}

    try:
        resp = _HTTP_SESSION.post(
            tts_url,
            data=data,
            files=files,
            stream=True,
            timeout=timeout,
        )

        if resp.status_code != 200:
            body = resp.text[:500]
            raise RuntimeError(
                f"PocketTTS request failed (HTTP {resp.status_code}): {body}"
            )

        # Small chunks: the sooner bytes arrive, the sooner the first segment
        # can be handed to the audio backend and played.
        for chunk in resp.iter_content(chunk_size=1024):
            if chunk:
                yield chunk
    finally:
        if fh is not None:
            fh.close()


def generate_speech(
    text: str,
    voice_file: Optional[os.PathLike] = None,
    tts_url: str = TTS_URL,
    timeout: float = 60.0,
) -> bytes:
    """Generate speech for *text* and return the complete WAV audio.

    This is a thin convenience wrapper around :func:`stream_speech` that
    buffers the streamed response.  It is what callers usually want when they
    need the whole audio clip at once (e.g. to cache or play).
    """
    buf = io.BytesIO()
    for chunk in stream_speech(text, voice_file, tts_url, timeout=timeout):
        buf.write(chunk)
    # PocketTTS streams a WAV with a placeholder ``data`` size; rewrite the
    # chunk sizes from the real byte count so the result plays everywhere.
    return _normalize_wav(buf.getvalue())


# --------------------------------------------------------------------------- #
# Playback
# --------------------------------------------------------------------------- #
def _play_wav_winsound(wav_bytes: bytes) -> bool:
    """Play a WAV byte string using the Windows stdlib ``winsound``.

    Returns ``True`` if playback was started, ``False`` if winsound was
    unavailable or refused the data.
    """
    try:
        import winsound  # Windows-only stdlib
    except ImportError:
        return False

    try:
        # SND_MEMORY plays directly from the in-memory WAV buffer.  SND_ASYNC
        # returns immediately so the CLI stays interactive.
        winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_ASYNC)
        return True
    except Exception:
        # Fall back to writing a temp file (some formats need a filename).
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
                tf.write(wav_bytes)
                tmp_path = tf.name
            winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_ASYNC)

            # Clean up the temp file once playback has had time to finish.
            duration = _wav_duration_seconds(wav_bytes) or 0.0
            threading.Thread(
                target=_delayed_unlink, args=(tmp_path, duration + 0.5), daemon=True
            ).start()
            return True
        except Exception:
            return False


def _delayed_unlink(path: str, delay: float) -> None:
    """Remove *path* after sleeping *delay* seconds."""
    import time

    time.sleep(delay)
    try:
        os.unlink(path)
    except OSError:
        pass


def _play_wav_sounddevice(wav_bytes: bytes) -> bool:
    """Play a WAV byte string using ``sounddevice`` (real-time streaming).

    Only used when the optional ``sounddevice`` package is installed; it
    allows true low-latency, chunk-by-chunk playback.  Returns ``True`` if it
    handled playback.
    """
    try:
        import sounddevice as sd  # type: ignore
        import numpy as np  # type: ignore
    except ImportError:
        return False

    try:
        rate, channels, bits, _ = _parse_wav_header(wav_bytes[:44])
    except Exception:
        return False

    if bits != 16:
        return False  # Only 16-bit PCM is supported by this path.

    # Build a numpy array from the PCM body (skipping the WAV header).
    # Only 16-bit PCM is supported by this path.
    data_offset = _find_wav_data_offset(wav_bytes)
    pcm = np.frombuffer(wav_bytes[data_offset:], dtype="<i2")
    if channels > 1:
        pcm = pcm.reshape(-1, channels)

    # Play in a background thread so the caller isn't blocked.
    threading.Thread(target=sd.play, args=(pcm,), kwargs={"samplerate": rate}, daemon=True).start()
    return True


def _play_wav_external(wav_bytes: bytes) -> bool:
    """Last-resort playback by launching the platform's default player."""
    try:
        import subprocess

        suffix = ".wav"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tf:
            tf.write(wav_bytes)
            tmp_path = tf.name

        if sys.platform == "darwin":
            subprocess.Popen(["afplay", tmp_path])  # noqa: S603
        elif os.name == "nt":
            os.startfile(tmp_path)  # noqa: PYL-W1514
        else:
            subprocess.Popen(["aplay", tmp_path])  # noqa: S603
        duration = _wav_duration_seconds(wav_bytes) or 0.0
        threading.Thread(
            target=_delayed_unlink, args=(tmp_path, duration + 0.5), daemon=True
        ).start()
        return True
    except Exception:
        return False


def play_audio(wav_bytes: bytes) -> bool:
    """Play a generated WAV byte string through the system.

    The playback backend is selected automatically (in order of preference):

    1. ``sounddevice``  - real-time streaming playback (optional, best).
    2. ``winsound``     - Windows stdlib (always available on Windows).
    3. Platform default player (afplay/aplay/os.startfile) - last resort.

    Returns ``True`` if some backend accepted the audio.
    """
    if not wav_bytes:
        return False

    # Validate that we actually have a WAV stream.
    try:
        _parse_wav_header(wav_bytes[:44])
    except Exception:
        warnings.warn("play_audio received non-WAV data; cannot play safely.", RuntimeWarning)
        return False

    for backend in (_play_wav_sounddevice, _play_wav_winsound, _play_wav_external):
        try:
            if backend(wav_bytes):
                return True
        except Exception:
            continue
    return False


# --------------------------------------------------------------------------- #
# Low-latency streaming playback
# --------------------------------------------------------------------------- #
# Serialises audio playback so concurrent utterances (e.g. the startup
# greeting and the exit farewell) are heard one after the other instead of
# cutting each other off (winsound allows only a single sound at a time).
_PLAYBACK_LOCK = threading.Lock()


def _play_stream_sounddevice(q, _DONE) -> bool:
    """Play a queued PCM stream *as it is generated* via ``sounddevice``.

    ``numpy``/``sounddevice`` must be installed (``pip install sounddevice``);
    this is the preferred low-latency, *gapless* playback path: audio is
    written to an open output stream while the utterance is still being
    generated, so speech starts early and never pauses mid-sentence.  The
    ``q`` queue carries raw chunks of the streamed WAV; ``_DONE`` is a
    sentinel marking the end of the stream (errors arrive as exceptions).

    Returns ``True`` when the stream was handed to the audio backend, and
    ``False`` when the caller should fall back to buffered playback.
    """
    try:
        import sounddevice as sd
    except Exception:
        return False

    header_buf = bytearray()
    prefix = b""
    pcm = bytearray()
    sample_rate = 0
    num_channels = 0
    bytes_per_sec = 0
    start_bytes = 1
    t_first_pcm = None
    stream = None
    started = False

    with _PLAYBACK_LOCK:
        try:
            while True:
                item = q.get()
                if item is _DONE:
                    break
                if isinstance(item, BaseException):
                    raise item

                if not prefix:
                    # Accumulate until the WAV header (and its ``data`` chunk
                    # offset) has fully arrived.
                    header_buf.extend(item)
                    # Reject non-WAV payloads early (a cached clip can arrive
                    # as a single large chunk, so no size cap is used here —
                    # the RIFF magic is the reliable guard).
                    if len(header_buf) >= 12 and bytes(header_buf[:4]) != b"RIFF":
                        return False  # not a WAV stream after all
                    try:
                        sample_rate, num_channels, bits, _ = _parse_wav_header(
                            bytes(header_buf[:44])
                        )
                    except Exception:
                        continue  # header not complete yet
                    if b"data" not in bytes(header_buf):
                        continue  # wait for the data chunk header
                    if bits != 16 or sample_rate <= 0 or num_channels <= 0:
                        return False  # only 16-bit PCM is supported here
                    data_offset = _find_wav_data_offset(bytes(header_buf))
                    prefix = bytes(header_buf[:data_offset])
                    pcm.extend(header_buf[data_offset:])
                    bytes_per_sec = max(1, sample_rate * num_channels * 2)
                    start_bytes = max(1, int(bytes_per_sec * STREAMING_MIN_START_SECONDS))
                else:
                    pcm.extend(item)

                if stream is None:
                    now = time.time()
                    if t_first_pcm is None:
                        t_first_pcm = now
                    audio_secs = len(pcm) / bytes_per_sec
                    if audio_secs < STREAMING_MIN_START_SECONDS:
                        continue  # buffer a little before opening the device
                    # Adaptive start: measure how fast the server produces
                    # audio.  If it is slower than real time, wait until we
                    # have enough buffered to play through without a gap.
                    if now - t_first_pcm > 0.25:
                        rate = audio_secs / (now - t_first_pcm)
                        if rate < 1.0:
                            needed = min(
                                STREAMING_MAX_START_SECONDS,
                                audio_secs / max(rate, 0.05) + 0.5,
                            )
                            if audio_secs < needed:
                                continue
                    stream = sd.RawOutputStream(
                        samplerate=sample_rate,
                        channels=num_channels,
                        dtype="int16",
                        blocksize=0,
                        # A generous device-side buffer so a brief dip in
                        # generation speed below real time can never drain
                        # the output and cause an audible gap.
                        latency="high",
                    )
                    stream.start()
                    started = True
                # write() blocks while the device buffer is full, pacing
                # playback to (at most) real time while the reader thread
                # keeps the queue fed in parallel.
                stream.write(bytes(pcm))
                pcm.clear()

            if stream is not None:
                if pcm:
                    stream.write(bytes(pcm))
                    pcm.clear()
                # Pa_StopStream: blocks until everything buffered has played.
                stream.stop()
            elif prefix and pcm:
                # Very short clip: the device was never opened (the stream
                # ended before the start buffer filled) — play the remainder
                # synchronously so it is still heard.
                _play_buffered_blocking(_normalize_wav(prefix + bytes(pcm)))
                pcm.clear()
                started = True
            return started
        except Exception:
            # Never let a playback hiccup crash the shell; report whether we
            # managed to start at all so the caller can fall back if not.
            return started
        finally:
            if stream is not None:
                try:
                    if stream.active:
                        stream.abort()
                except Exception:
                    pass
                try:
                    stream.close()
                except Exception:
                    pass


def _play_buffered_blocking(wav_bytes: bytes) -> None:
    """Play a complete WAV *synchronously* (blocks until it has finished).

    Used as fallback when the streaming sounddevice path is unavailable.
    Blocking matters for the exit farewell: a non-blocking play would be cut
    short the moment the process exits.
    """
    try:
        import winsound  # Windows-only stdlib
    except ImportError:
        play_audio(wav_bytes)
        return
    tmp_path = None
    try:
        # SND_SYNC from memory has a large fixed overhead on some systems;
        # a temp file + SND_SYNC is dependable and blocks exactly until the
        # clip has finished.
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tf:
            tf.write(wav_bytes)
            tmp_path = tf.name
        winsound.PlaySound(tmp_path, winsound.SND_FILENAME | winsound.SND_SYNC)
    except Exception:
        play_audio(wav_bytes)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def get_voice_file() -> Path:
    """Public accessor for the active voice-cloning reference file."""
    return find_voice_file()


# --------------------------------------------------------------------------- #
# Generated-clip cache (zero latency for fixed phrases)
# --------------------------------------------------------------------------- #
def _cache_key(
    text: str,
    voice: Optional[str] = None,
    voice_file: Optional[os.PathLike] = None,
) -> str:
    """Stable cache key for a (voice, text) pair.

    Built-in voice names key on the name; cloned voices additionally key on
    the reference file's identity (name, size, mtime) so an updated voice
    file naturally invalidates its entries.
    """
    name = voice if voice is not None else DEFAULT_VOICE_NAME
    h = hashlib.sha1()
    if name and name.strip().lower() != "file":
        h.update(b"builtin:" + name.encode("utf-8"))
    else:
        h.update(b"clone:")
        try:
            path = Path(voice_file) if voice_file is not None else find_voice_file()
            st = path.stat()
            h.update(f"{path.name}|{st.st_size}|{st.st_mtime_ns}".encode("utf-8"))
        except (OSError, FileNotFoundError):
            h.update(b"novoice")
    h.update(b"\x00")
    h.update(text.encode("utf-8"))
    return h.hexdigest()


def _cache_get(key: str) -> Optional[bytes]:
    """Return the cached WAV for *key*, or ``None`` on a miss."""
    path = CACHE_DIR / (key + ".wav")
    try:
        if path.is_file():
            data = path.read_bytes()
            if data:
                return data
    except OSError:
        return None
    return None


def _cache_put(key: str, wav_bytes: bytes) -> None:
    """Store *wav_bytes* under *key* (best-effort, atomic replace)."""
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = CACHE_DIR / (key + ".wav")
        tmp = CACHE_DIR / f"{key}.{os.getpid()}.tmp"
        tmp.write_bytes(wav_bytes)
        os.replace(tmp, path)
    except OSError:
        pass  # caching must never break speech


def clear_voice_cache() -> int:
    """Delete every cached clip; returns how many entries were removed."""
    removed = 0
    try:
        if CACHE_DIR.is_dir():
            for path in CACHE_DIR.glob("*.wav"):
                try:
                    path.unlink()
                    removed += 1
                except OSError:
                    pass
    except OSError:
        pass
    return removed


def _play_clip(wav_bytes: bytes) -> None:
    """Play a complete WAV clip with minimal latency (blocks until done).

    Preferred path feeds the whole clip through the gapless sounddevice
    player; falls back to the synchronous winsound/file path when
    ``sounddevice`` is unavailable.
    """
    import queue as _queue

    _DONE = object()
    q: "_queue.Queue" = _queue.Queue()
    q.put(wav_bytes)
    q.put(_DONE)
    if _play_stream_sounddevice(q, _DONE):
        return
    _play_buffered_blocking(wav_bytes)


def speak_streaming(
    text: str,
    voice_file: Optional[os.PathLike] = None,
    tts_url: str = TTS_URL,
    timeout: float = 60.0,
    voice: Optional[str] = None,
) -> Optional[bytes]:
    """Generate and play *text* with minimum latency (streaming playback).

    The generated WAV is played *while it is still being synthesised* (via
    ``sounddevice`` when available), so the first words are heard well under
    a second after the request and the playback is gapless from start to
    finish.  A dedicated reader thread keeps pulling from the network even
    while audio is playing, so playback can never starve the socket.

    Returns the complete generated WAV (useful for caching/inspection), or
    ``None`` when streaming playback could not be used and the caller should
    fall back to buffered playback.
    """
    import queue as _queue

    _DONE = object()
    q: "_queue.Queue" = _queue.Queue()
    collected: list[bytes] = []

    def _reader() -> None:
        """Pull chunks off the network without ever blocking on playback."""
        try:
            for chunk in stream_speech(
                text, voice_file, tts_url, timeout=timeout, voice=voice
            ):
                collected.append(chunk)
                q.put(chunk)
        except BaseException as exc:  # propagate to the player thread
            q.put(exc)
        finally:
            q.put(_DONE)

    threading.Thread(target=_reader, daemon=True).start()

    if _play_stream_sounddevice(q, _DONE):
        return _normalize_wav(b"".join(collected)) if collected else b""
    return None


def speak(
    text: str,
    voice_file: Optional[os.PathLike] = None,
    tts_url: str = TTS_URL,
    play: bool = True,
    voice: Optional[str] = None,
) -> bytes:
    """Speak *text* through Colen's voice in real time.

    Steps:
        1. Fixed-phrase cache: if this (voice, text) pair was spoken before,
           play the cached WAV straight from disk (zero synthesis latency).
        2. Resolve the voice: the built-in PocketTTS preset (``mary`` by
           default, sent as ``voice_url``) or, when built-in voices are
           disabled, the single audio file in ``/voices`` (``voice_wav``).
        3. Stream the generated WAV and start playing it as soon as the first
           fraction of a second of audio is available (low latency, gapless).
        4. Fall back to fully-buffered synchronous playback if streaming is
           unavailable (e.g. on platforms without ``sounddevice``).

    Args:
        text: The utterance to synthesise.
        voice_file: Optional explicit override for the voice reference file
            (only used when cloning from ``/voices``).
        tts_url: PocketTTS endpoint URL.
        play: If ``True`` (default) attempt to play the audio immediately.
        voice: Optional explicit built-in voice name (e.g. ``"mary"``).

    Returns:
        The generated WAV audio as bytes.

    Raises:
        FileNotFoundError: if no voice file is present in ``/voices``.
        RuntimeError: if the PocketTTS request fails.
    """
    if not play:
        return generate_speech(text, voice_file=voice_file, tts_url=tts_url)

    # Fixed-phrase cache: greetings are spoken identically every time, so a
    # cache hit removes all synthesis latency — the clip plays from disk.
    cache_key = _cache_key(text, voice=voice, voice_file=voice_file)
    cached = _cache_get(cache_key)
    if cached is not None:
        _play_clip(cached)
        return cached

    # Preferred path: start playback while the utterance is still being
    # generated (the first audio is heard in well under a second on a warm
    # server, and playback is gapless from start to finish).
    audio = speak_streaming(text, voice_file=voice_file, tts_url=tts_url, voice=voice)
    if audio is not None:
        _cache_put(cache_key, audio)
        return audio

    # Fallback (no sounddevice available): buffer the entire utterance, then
    # play it synchronously so it is never chopped off mid-sentence.
    audio = generate_speech(text, voice_file=voice_file, tts_url=tts_url)
    _play_buffered_blocking(audio)
    _cache_put(cache_key, audio)
    return audio


# --------------------------------------------------------------------------- #
# CLI entry point (python -m colen.speech)
# --------------------------------------------------------------------------- #
def _read_text_arg(argv: list[str]) -> str:
    """Read the text to speak from argv or stdin."""
    if len(argv) > 1:
        return " ".join(argv[1:])
    return sys.stdin.read().strip()


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point: ``python -m colen.speech "some text"``."""
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] in ("-h", "--help"):
        print(
            "Usage: python -m colen.speech \"text to speak\"\n"
            "   or: echo text | python -m colen.speech\n"
            "\n"
            "Reads the single audio file from the /voices directory and uses it\n"
            f"as the voice reference for PocketTTS at {TTS_URL}."
        )
        return 0

    if argv and argv[0] == "--voice":
        # Allow pointing at an alternative voices dir (handy for testing).
        os.environ["COLEN_VOICES_DIR"] = argv[1]
        argv = argv[2:]

    text = " ".join(argv) if argv else sys.stdin.read()
    text = text.strip()
    if not text:
        print("Error: no text supplied. Pass text as an argument or via stdin.", file=sys.stderr)
        return 2

    try:
        speak(text)
        print(f"Spoken: {text!r}")
        return 0
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except ImportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
