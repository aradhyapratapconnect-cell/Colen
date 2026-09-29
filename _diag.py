"""Diagnose audio break-up: measure TTS production rate + playback starvation."""
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import colen.assistant as A
from colen.speech import (
    _find_wav_data_offset,
    _parse_wav_header,
    stream_speech,
)


def measure(text, label):
    t0 = time.time()
    header = bytearray()
    info = None
    pcm_bytes = 0
    first_pcm_at = None
    n_chunks = 0
    for chunk in stream_speech(text):
        n_chunks += 1
        if info is None:
            header.extend(chunk)
            if len(header) >= 44 and b"data" in header:
                sr, ch, bits, _ = _parse_wav_header(bytes(header[:44]))
                off = _find_wav_data_offset(bytes(header))
                info = (sr, ch, bits)
                first_pcm_at = time.time() - t0
                pcm_bytes += len(header) - off
        else:
            pcm_bytes += len(chunk)
    t1 = time.time()
    if info is None:
        print(f"[{label}] NO WAV HEADER! first bytes: {bytes(header)[:60]!r}")
        return None
    sr, ch, bits = info
    bps = max(1, sr * ch * (bits // 8))
    audio = pcm_bytes / bps
    print(f"[{label}] rate={sr} ch={ch} bits={bits} | first PCM @ {first_pcm_at:.2f}s | "
          f"wall={t1 - t0:.2f}s audio={audio:.2f}s => production {audio / (t1 - t0):.2f}x realtime "
          f"({n_chunks} net chunks)")
    return sr, ch, bits


TEXT1 = ("The quick brown fox jumps over the lazy dog while the old grey cat "
         "watches from the sunny windowsill nearby.")
TEXT2 = "Welcome back, Sir. All systems are online."
info = measure(TEXT1, "TTS-1")
measure(TEXT2, "TTS-2")

# ---- Playback timeline for a real answer --------------------------------
writes = []
captured = bytearray()
orig_write = A.ContinuousPlayer.write


def spy_write(self, pcm):
    writes.append((time.time(), len(pcm)))
    captured.extend(pcm)
    return orig_write(self, pcm)


A.ContinuousPlayer.write = spy_write

chunks = []
orig_sc = A.sentence_chunks


def spy_sc(tokens, *a, **k):
    for ch in orig_sc(tokens, *a, **k):
        chunks.append((time.time(), ch))
        yield ch


A.sentence_chunks = spy_sc

T0 = time.time()
answer_text = A.answer("Tell me one short fun fact about the Moon, please.", play=True)
T1 = time.time()
A.ContinuousPlayer.write = orig_write
A.sentence_chunks = orig_sc

sr = info[0] if info else 24000
frame = max(1, sr * 2)

print("\n[CHUNK TIMELINE]")
for t, ch in chunks:
    print(f"  {t - T0:6.2f}s  {ch!r}")

print(f"\n[WRITES] count={len(writes)}  answer wall={T1 - T0:.2f}s")
prev_t = None
starve = 0.0
for i, (t, n) in enumerate(writes):
    dur = n / frame
    gap = (t - prev_t) if prev_t is not None else None
    flag = ""
    if gap is not None and dur > 0.05 and gap < dur * 0.7:
        starve += dur - gap
        flag = "  <-- SYNTHESIS LAG"
    if i < 30 or flag:
        g = f"{gap * 1000:6.0f}ms" if gap is not None else "   ---"
        print(f"  write#{i:03d} @{t - T0:6.2f}s  audio={dur * 1000:5.0f}ms  since_prev={g}{flag}")
    prev_t = t
print(f"[STARVE] approx stalled audio time: {starve:.2f}s")
print(f"[CAPTURE] {len(captured)} bytes of PCM inspected")

# Inspect the captured PCM for embedded headers / long silences.
import numpy as np

pcm = np.frombuffer(bytes(captured), dtype=np.int16)
if pcm.size:
    raw = bytes(captured)
    print(f"[CAPTURE] embedded b'RIFF' occurrences: {raw.count(b'RIFF')} (1 = clean)")
    quiet = np.abs(pcm) < 200
    # find runs of near-silence longer than 60ms
    runs = []
    start = None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            runs.append((start, i - start))
            start = None
    if start is not None:
        runs.append((start, quiet.size - start))
    long_runs = [(s, n) for s, n in runs if n > 0.06 * sr]
    print(f"[CAPTURE] silence runs > 60ms: {len(long_runs)} "
          f"(total {sum(n for _, n in long_runs) / sr:.2f}s of {pcm.size / sr:.2f}s)")
    for s, n in long_runs[:20]:
        print(f"    @{s / sr:5.2f}s  {n / sr * 1000:5.0f}ms silent")

print("[ANSWER]", answer_text)
