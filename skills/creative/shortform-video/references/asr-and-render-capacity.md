# ASR & Render Capacity — where the compute actually runs

Reference for the recurring question: *"kenapa transkripsi gagal? kena top-up API ke, kena upgrade VPS ke?"*
Those are two different machines' jobs. Answering them as one problem leads to wrong spending.

## The three separate paths

| Job | Runs on | Fix when it fails |
|---|---|---|
| Speech-to-text (ASR) | Cloud multimodal API (Gemini inline audio) **or** local Whisper | Top-up / different API **or** supply a transcript. RAM does not help a quota error |
| Scene direction → JSON | The chat/reasoning model (DeepSeek V4 Flash) | Nothing — text-only models do this fine |
| Rendering to MP4 | React/Remotion/HyperFrames on the owner's engine | RAM/CPU on the render host (headless Chromium) |

**Text-only ≠ multimodal.** DeepSeek V4 Flash is the cheap, fast chat brain, but it cannot hear
audio or see frames. Keeping it primary is correct for direction work; it must still be paired
with a real ASR/vision path. Never tell the owner "upgrade and DeepSeek can do transcription."

## Measured numbers (Tencent VPS, 2026-10)

Host: **2 vCPU / 1,967 MB RAM / 1.9 GB swap (525 MB already in use) / 40 GB disk at 58%.**

| Workload | RAM needed | Fits 2 GB? |
|---|---|---|
| faster-whisper `small` int8, 2 threads | ~500 MB | Yes — but garbles noisy Malay |
| faster-whisper `large-v3-turbo` int8 | ~3 GB+ | No |
| Remotion / headless Chromium render | 1.5–2.5 GB resident | No — OOM-killed |

Garbled `small` output actually observed on a 67 s in-car clip (32 kbps mono AAC):

```
"Beli-beli ini pagi sob mula."
"Ya boleh pakai Atomi, SP, Litter, Ons."
"Saya sudah kebenaran."
```

That is a model-capacity ceiling, not a fixable prompt problem. `initial_prompt` in Malay,
`beam_size=5`, VAD on and a cleaned signal (`highpass=f=90,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11`)
all still produced the above. Treat it as a signal to escalate the ASR path.

## Cloud ASR cost math (why top-up usually wins)

Gemini inline audio, 66 s clip → **1,658 audio tokens**. Extrapolated: ~90k tokens/hour of
footage ≈ **under USD 0.20 per hour**. So **USD 5 ≈ ~25 hours** of footage — dozens of episodes.

A VPS spec bump is recurring monthly cost and does not fix an exhausted API quota. Recommend the
cheap correct fix, even when the owner is leaning toward the purchase.

## When local ASR *is* worth it

- Owner wants zero per-minute cost and full privacy for family footage.
- Owner wants the whole pipeline (local Whisper + render + background agents) on one box.
- Sane target: **4 vCPU / 8 GB RAM**. Then run `large-v3-turbo` and render on the same host.

## Diagnose before advising

```bash
free -m; nproc; swapon --show; df -h / | tail -1
```

Swap already in use on an idle box = already starved. That is the argument for upgrading —
not a failed transcription (which an API top-up fixes for cents).

## Delivery pattern once capacity exists

```
Telegram video → ffmpeg audio extract + DSP clean → Whisper large-v3-turbo (local)
             → DeepSeek directs JSON scenes → Remotion renders → MP4 back to Telegram
```

## Standing directives from the owner

- **Replicate: do not use** for transcription as of 2026-10 (owner said "jgn guna replicate lagi").
  It remains the fallback if the cloud-API path is unavailable and the owner approves.
- Plan of record lives at `~/AnaFile/VIDEO_ENGINE_PLAN.md`; the VPS resize is tracked as an
  owner task. Update both when capacity or credentials change.
