"""Colen Voice Assistant — instant Groq answers, spoken with PocketTTS.

Type a question; Colen streams the answer from Groq's ``llama-3.1-8b-instant``
and speaks it aloud through the local PocketTTS server while the answer is
still being generated.  Sentences are pipelined (LLM -> TTS -> playback run
concurrently) so the first word is heard in roughly a second and the answer
never pauses mid-sentence.

Usage
-----
    python -m colen.assistant               # interactive chat
    python -m colen.assistant "question"    # one-shot answer (also spoken)

Environment
-----------
    GROQ_API_KEY   Groq API key — set it in a .env file (see .env.example).
    COLEN_TTS_URL  PocketTTS endpoint (default http://localhost:8000/tts).
"""
from __future__ import annotations

import json
import os
import queue
import re
import sys
import threading
import time
from typing import Iterator, List, Optional

import click
import requests
from rich.console import Console

from colen.speech import (
    _find_wav_data_offset,
    _parse_wav_header,
    generate_speech,
    speak,
    stream_speech,
)

console = Console()

# Groq (llama-3.1-8b-instant) — extremely low time-to-first-token.
GROQ_URL = os.environ.get(
    "COLEN_GROQ_URL", "https://api.groq.com/openai/v1/chat/completions"
)
# The key lives in a .env file (git-ignored) — see .env.example for the
# template; load_env() in colen/__init__.py reads it into the environment.
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
# Groq LLM model selection:
# User requested `llama-3.1-8b-instant`.  On some Groq accounts / regions,
# that model ID is not permissioned or decommissioned, so we automatically
# fall back to the fastest available chat model on the account
# (`openai/gpt-oss-20b` or `qwen/qwen3.8-27b`) if llama returns 404.
DEFAULT_MODEL = "llama-3.1-8b-instant"
FALLBACK_MODELS = ("openai/gpt-oss-20b", "qwen/qwen3.8-27b")
GROQ_MODEL = os.environ.get("COLEN_LLM_MODEL", DEFAULT_MODEL)

_SYSTEM_PROMPT = (
    "You are Colen, a concise Jarvis-style assistant. Answer directly and "
    "correctly in at most 2-3 short sentences. Plain text only - no markdown, "
    "no lists, no emojis."
)

_SESSION = requests.Session()

_SENT_END = re.compile(r"([.!?])(?:\s+|$)")
_CLAUSE_PUNCT = re.compile(r"([,;:\-—])\s+")
_MD_STRIP = re.compile(r"[*_`#>~]+")


def _post_chat(messages: List[dict], model: str) -> requests.Response:
    """Send a streaming chat-completion request to Groq."""
    return _SESSION.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": 0.6,
            "max_tokens": 250,
        },
        stream=True,
        timeout=(5, 60),
    )


def stream_llm(messages: List[dict]) -> Iterator[str]:
    """Yield answer tokens from Groq as they arrive.

    Tries the requested ``GROQ_MODEL`` (default ``llama-3.1-8b-instant``).
    If the account lacks access to that model (HTTP 404), seamlessly falls
    back to the fastest available chat model on the account.
    """
    global GROQ_MODEL

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and put your "
            "Groq API key there, or export GROQ_API_KEY in your shell."
        )

    candidates = [GROQ_MODEL] + [m for m in FALLBACK_MODELS if m != GROQ_MODEL]
    resp = None
    for model in candidates:
        r = _post_chat(messages, model)
        if r.status_code == 200:
            if model != GROQ_MODEL:
                GROQ_MODEL = model  # remember working model for the session
            resp = r
            break
        if r.status_code != 404:
            # Fatal error (e.g. 401 invalid key, 429 rate limit) — don't retry.
            body = r.text[:200]
            r.close()
            raise RuntimeError(f"Groq request failed (HTTP {r.status_code}): {body}")
        r.close()

    if resp is None:
        raise RuntimeError(
            f"None of the candidate models {candidates} are accessible on this Groq key."
        )
    try:
        for raw in resp.iter_lines():
            if not raw:
                continue
            line = raw.decode("utf-8", "replace")
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                delta = json.loads(payload)["choices"][0]["delta"].get("content")
            except Exception:
                continue
            if delta:
                yield delta
    finally:
        resp.close()


def sentence_chunks(
    tokens: Iterator[str],
    min_chars: int = 50,
    max_chars: int = 120,
) -> Iterator[str]:
    """Group a token stream into natural, balanced phrases for TTS pipelining.

    Synthesising long sentences (150+ chars) all at once introduces significant
    latency and causes pauses between sentences. Splitting at natural sentence
    boundaries or clause punctuation (commas, semicolons, dashes) ensures:
      1. Synthesis starts on the first phrase almost immediately (~0.5s).
      2. Subsequent phrases keep the playback buffer continuously filled,
         so speech flows without any interruption.
    """
    buf = ""
    for tok in tokens:
        buf += tok
        while True:
            # Check sentence punctuation (. ! ?)
            m = _SENT_END.search(buf)
            if m:
                chunk, buf = buf[: m.end()].strip(), buf[m.end():]
                if chunk:
                    yield chunk
                continue

            # If buffer has grown past max_chars, split at natural clause punctuation
            if len(buf) >= max_chars:
                matches = list(_CLAUSE_PUNCT.finditer(buf[:max_chars]))
                chosen = None
                for cm in reversed(matches):
                    if cm.end() >= min_chars:
                        chosen = cm
                        break
                if chosen:
                    chunk, buf = buf[: chosen.end()].strip(), buf[chosen.end():]
                    if chunk:
                        yield chunk
                    continue

                # If no clause punctuation, split at word boundary
                cut = buf.rfind(" ", 0, max_chars)
                if cut > min_chars // 2:
                    chunk, buf = buf[:cut].strip(), buf[cut:]
                    if chunk:
                        yield chunk
                    continue
            break
    if buf.strip():
        yield buf.strip()


class ContinuousPlayer:
    """One continuous audio output stream for the whole answer (gapless).

    A single PortAudio stream is opened for the entire reply; every
    sentence's PCM is written into it, so sentences join seamlessly with no
    per-clip device overhead and no mid-sentence stalls.
    """

    def __init__(self) -> None:
        self._stream = None

    def ensure(self, sample_rate: int, channels: int) -> None:
        if self._stream is not None:
            return
        import sounddevice as sd

        self._stream = sd.RawOutputStream(
            samplerate=sample_rate,
            channels=channels,
            dtype="int16",
            blocksize=0,
            latency="high",
        )
        self._stream.start()

    def write(self, pcm: bytes) -> None:
        if self._stream is not None:
            # Blocks while the device buffer is full: paces playback to real
            # time without gaps.
            self._stream.write(pcm)

    def finish(self) -> None:
        """Drain and close (blocks until everything buffered has played)."""
        if self._stream is None:
            return
        try:
            self._stream.stop()
        finally:
            try:
                self._stream.close()
            except Exception:
                pass
            self._stream = None


def answer(
    question: str,
    history: Optional[List[dict]] = None,
    play: bool = True,
) -> str:
    """Ask Groq and speak the answer sentence-by-sentence while it streams.

    Pipeline: the LLM streams tokens -> completed sentences are handed to a
    TTS worker -> finished clips are written into one continuous output
    stream.  Generation, synthesis and playback therefore overlap, so the
    first word is heard as early as possible and the answer is gapless.

    Returns the full answer text.
    """
    messages: List[dict] = [{"role": "system", "content": _SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": question})

    text_parts: List[str] = []
    sentences: "queue.Queue" = queue.Queue()
    pcm_queue: "queue.Queue" = queue.Queue()
    _END = object()
    tts_error: List[Exception] = []
    player = ContinuousPlayer()
    t_first_pcm = None
    t0 = time.time()

    def tts_stream_worker() -> None:
        """Stream synthesise each sentence chunk as raw PCM into pcm_queue."""
        nonlocal tts_error
        while True:
            sentence = sentences.get()
            if sentence is _END:
                pcm_queue.put(_END)
                return
            clean = _MD_STRIP.sub("", sentence).strip()
            if not clean:
                continue
            try:
                header_buf = bytearray()
                prefix_done = False
                rate, channels = 24000, 1
                for chunk in stream_speech(clean):
                    if not prefix_done:
                        header_buf.extend(chunk)
                        if len(header_buf) >= 44 and b"data" in header_buf:
                            rate, channels, bits, _ = _parse_wav_header(
                                bytes(header_buf[:44])
                            )
                            if bits != 16:
                                raise RuntimeError("non-16-bit PCM from TTS")
                            data_offset = _find_wav_data_offset(bytes(header_buf))
                            pcm = header_buf[data_offset:]
                            prefix_done = True
                            if pcm:
                                pcm_queue.put((rate, channels, bytes(pcm)))
                    else:
                        pcm_queue.put((rate, channels, chunk))
            except Exception as exc:
                tts_error.append(exc)
                pcm_queue.put(None)  # signal error
                return

    worker = None
    if play:
        worker = threading.Thread(target=tts_stream_worker, daemon=True)
        worker.start()

    try:
        for chunk in sentence_chunks(stream_llm(messages)):
            text_parts.append(chunk)
            console.print(f"[cyan]{chunk} [/cyan]", end="", soft_wrap=True)
            if play:
                sentences.put(chunk)
        if play:
            sentences.put(_END)

        if play:
            while True:
                item = pcm_queue.get()
                if item is _END:
                    break
                if item is None:
                    name = tts_error[0].__class__.__name__ if tts_error else "error"
                    console.print(f"\n[dim](speech unavailable: {name})[/dim]")
                    break
                rate, channels, pcm_bytes = item
                if t_first_pcm is None:
                    t_first_pcm = time.time()
                try:
                    player.ensure(rate, channels)
                    player.write(pcm_bytes)
                except Exception:
                    continue
    finally:
        player.finish()

    console.print()
    first = f"{t_first_pcm - t0:.2f}s" if t_first_pcm else "n/a"
    console.print(f"[dim](first word: {first}, total {time.time() - t0:.2f}s)[/dim]")
    return " ".join(text_parts)


def _clip_pcm(wav_bytes: bytes) -> bytes:
    """Return the raw PCM payload of a generated WAV clip."""
    return wav_bytes[_find_wav_data_offset(wav_bytes):]


def _warm_tts() -> None:
    """Warm the PocketTTS server in the background (first request loads it)."""

    def _warm() -> None:
        try:
            for _ in stream_speech("Yes, Sir."):
                break  # a single chunk is enough to warm the model
        except Exception:
            pass  # warming is best-effort

    threading.Thread(target=_warm, daemon=True).start()


@click.command()
@click.argument("question", nargs=-1)
def main(question: tuple) -> None:
    """Colen Voice Assistant: type a question, hear the answer via PocketTTS."""
    console.print(
        "[bold cyan]Colen Voice Assistant[/bold cyan] "
        "[dim](llama-3.1-8b-instant + PocketTTS)[/dim]"
    )
    console.print(
        "[dim]Type your question and press Enter. 'exit' to quit. "
        "'clear' to forget the conversation.[/dim]\n"
    )

    history: List[dict] = []

    if question:
        q = " ".join(question).strip()
        if q:
            answer(q, history)
        return

    _warm_tts()

    while True:
        try:
            text = console.input("[bold cyan]You › [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold cyan]Goodbye, Sir. Have a pleasant day.[/bold cyan]")
            try:
                speak("Goodbye, Sir. Have a pleasant day.", play=True)  # cached → instant
            except Exception:
                pass
            break

        if not text:
            continue
        if text.lower() in ("exit", "quit", "q", "bye"):
            console.print("[bold cyan]Goodbye, Sir. Have a pleasant day.[/bold cyan]")
            try:
                speak("Goodbye, Sir. Have a pleasant day.", play=True)  # cached → instant
            except Exception:
                pass
            break
        if text.lower() in ("clear", "reset"):
            history.clear()
            console.print("[dim]Conversation cleared, Sir.[/dim]")
            continue

        try:
            reply = answer(text, history)
        except Exception as exc:
            console.print(f"[red]Error:[/red] {exc}")
            continue
        history.append({"role": "user", "content": text})
        history.append({"role": "assistant", "content": reply})
        del history[:-10]  # keep the last few turns as context


if __name__ == "__main__":
    main()