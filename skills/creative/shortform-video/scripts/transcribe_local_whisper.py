#!/usr/bin/env python3
"""Local ASR fallback for video transcripts when cloud multimodal ASR is unavailable.

Why this exists: `faster_whisper.model.transcribe("<file>.wav")` crashes on newer
PyAV builds with:
    TypeError: open() got an unexpected keyword argument 'metadata_errors'
Passing a pre-decoded float32 numpy array sidesteps PyAV entirely.

Setup (one time):
    uv venv ~/.venv-whisper --python 3.12
    uv pip install --python ~/.venv-whisper/bin/python faster-whisper

Usage:
    ffmpeg -y -i input.mov -vn -ar 16000 -ac 1 \
      -af "highpass=f=90,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11" audio_clean.wav
    ~/.venv-whisper/bin/python transcribe_local_whisper.py audio_clean.wav small ms

WARNING — read the output before you trust it. `small` on noisy, code-switched
Malay (in-car vlog, 32 kbps mono) frequently returns fluent nonsense. If the text
does not read like the video's actual subject matter, STOP: report the ASR failure
and ask the owner for a transcript. Never paraphrase or invent dialogue to fill a
timeline.

Memory note: this box has ~2 GB RAM. `small` int8 needs ~0.5 GB and runs ~2 min for
67 s of audio; `medium` will swap heavily. Run long jobs with background=true.
"""
import json
import sys
import wave

import numpy as np
from faster_whisper import WhisperModel

wav_path = sys.argv[1] if len(sys.argv) > 1 else "audio_clean.wav"
model_size = sys.argv[2] if len(sys.argv) > 2 else "small"
lang = sys.argv[3] if len(sys.argv) > 3 else "ms"

with wave.open(wav_path, "rb") as wf:
    sr = wf.getframerate()
    raw = wf.readframes(wf.getnframes())
audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

print(f"sr={sr} samples={len(audio)} dur={len(audio) / sr:.2f}s", flush=True)

model = WhisperModel(model_size, device="cpu", compute_type="int8", cpu_threads=2)
segments, _info = model.transcribe(
    audio,
    language=lang,
    beam_size=5,
    best_of=5,
    temperature=[0.0, 0.2, 0.4],
    vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=250, threshold=0.35),
    condition_on_previous_text=False,
    initial_prompt=(
        "Ini vlog keluarga Melayu di Malaysia. Suami Keyrol dan isteri Nayli "
        "berbual dalam kereta tentang membeli perabot rumah, renovate rumah "
        "subsale, dan barang rumah. Bahasa Melayu pasar campur English."
    ),
)

out = []
for s in segments:
    out.append({"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()})
    print(f"{s.start:6.2f} -> {s.end:6.2f} | {s.text.strip()}", flush=True)

dest = f"whisper_{model_size}.json"
with open(dest, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=1)

print(f"SAVED {len(out)} segments -> {dest}")
print("VERIFY the text against the video context before directing scenes off it.")
