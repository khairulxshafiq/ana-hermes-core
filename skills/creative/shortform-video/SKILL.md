---
name: shortform-video
description: Edit raw video into YouTube/Shorts cuts — default output is a JSON scene schema for React/Remotion/HyperFrames (FFmpeg render path kept as legacy fallback).
---

# Video Production & Transformation (YouTube Landscape & Shortform)

Turn raw user-submitted video footage into polished, high-retention video assets for YouTube (16:9 Landscape) or Reels/TikTok/Shorts (9:16 Vertical) with modern typography, interactive badges, and timed audio cues.

## ⚠️ CURRENT ROLE (2026-10 onward): Video Data Director — JSON, not FFmpeg

The owner explicitly reassigned this class of work. **Read this before doing anything with a video.**

> "Mulai sekarang, peranan anda telah ditukar daripada 'Penjana Kod FFmpeg' kepada 'Pengarah Data Video / Penganalisis JSON'."

- **Default deliverable = a JSON scene-schema** that drives an external React/Remotion/HyperFrames engine. The owner's web engine does the rendering; you do NOT render.
- **Do NOT write filtergraphs, FFmpeg CLI, or Python render scripts** unless the owner explicitly asks for a rendered MP4 again. The FFmpeg sections below are **legacy fallback only** (kept because they are validated — see "Legacy FFmpeg path" at the bottom).
- Output for a transcript job must be a **bare valid JSON array** — starts with `[`, ends with `]`, zero prose, zero preamble, zero code fences.
- Full schema + a boss-approved worked example: `references/remotion-scene-schema.md`.

### JSON mode is task-scoped, not conversational
Only emit raw JSON when you are processing an actual transcript/clip. Normal chat, greetings, clarifying questions, and briefings stay in normal voice. Emitting a one-element JSON array in reply to "sedia terima transkrip?" was received with *"Apa kau reply tu? Haha"* — it is robotic and unwanted. Match the mode to the input: transcript in → JSON out; conversation in → conversation out.

### Hard content rules inside the JSON
- **Subtitle pacing:** 3–5 words max per scene. Fast vlogger cadence, never paragraph-length lines.
- **Typography:** `Montserrat-ExtraBold`. `style` must be `text_stroke_shadow` or `glass_pill_background` — **never `solid_box` / solid background blocks** (the owner calls these "petak tofu").
- **Word highlighting:** `highlight_words` + contrasting `highlight_color` (gold `#FFE124` for the husband, coral `#FF66D9` for the wife; red `#EF4444` for emphasis/"self-made" declarations).
- **Overlays:** glass badges / status tags / HUD pills only. Every overlay gets a `trigger_time`, `position`, and a spring/slide/glitch `animation`. Real vector/emoji icon field, not text-in-a-badge.
- **Audio:** every overlay or emphasis must carry an `audio_sfx` cue (`pop_chime`, `pop_bubble`, `whoosh_slam`, `snap_click`, `boing_spring`, `ding_bell`). Plus `background_music` at `volume: 0.10–0.15` so dialogue stays dominant.
- **Camera:** `slow_zoom_in`, `pan_to_subject`, `punch_zoom_face` (+ `scale` 1.35–1.45 and `target`), `slow_zoom_out`. For comedic reactions add `distortion_effect: "barrel_bulge_fisheye"` (= the "zoom katak" the owner loves).
- **Privacy:** any sleeping infant/minor in frame gets a `privacy_mask` overlay (`feathered_gaussian_blur`, label `PRIVACY PROTECTED`) while adult faces stay sharp.
- **Aspect handling:** `input_aspect_ratio` + `target_aspect_ratio` + `resize_mode`. Landscape→vertical **must** use `center_crop_face_tracking`; never squash or stretch. Main YouTube upload = `16:9`; Shorts/Reels = `9:16`.
- **Never fabricate dialogue.** If ASR output is garbled, say so and ask for a transcript — do not invent lines to fill the timeline. (See transcription pitfalls.)

### Brand context (owner's channel)
- YouTube channel: **by.naykey** — creators **Keyrol** (the owner/husband) & **Nayli** (wife). Series: house-renovation vlog of their first subsale home.
- Watermark `by.naykey` top-left; creators credit `NAYLI & KEYROL`; outro = channel CTA card.
- Recurring badge vocabulary: `PROJEK RUMAH SUBSALE`, `TRADEMARK : FAILED`, `BARU DAPAT KUNCI`, `MODE: 100% D.I.Y`, `PHASE 01/02/03` (cat dinding / lantai SPC / tukar pintu), `MOODBOARD : PINTEREST`, `TUTORIAL : TIKTOK`.

## Where the compute actually runs (capacity planning)

The owner raises infrastructure questions ("kena top-up API ke? kena upgrade VPS ke?") precisely when
a quota runs out, and the two problems get conflated. Keep them separate before answering:

- **ASR is a cloud API call, not a local-compute job.** A quota/credit failure is never fixed by
  adding RAM. Gemini inline audio ran ~1,658 tokens for 66 s → **USD 5 ≈ 25 hours** of footage,
  usually far cheaper than a monthly spec bump.
- **Text-only ≠ multimodal.** DeepSeek V4 Flash (the cheap chat brain) cannot hear audio or see
  frames. Keeping it primary is right for scene direction; it must still be paired with a real
  ASR/vision path.
- **Local ASR needs RAM the box usually doesn't have.** On a 2 GB / 2 vCPU host only
  faster-whisper `small` fits, and `small` garbles noisy Manglish regardless of prompt tuning.
  `large-v3-turbo` wants ~3 GB+ and 4 vCPU.
- **The rendering engine needs RAM too.** Remotion/HyperFrames renders via headless Chromium
  (1.5–2.5 GB resident); on a 2 GB host the render gets OOM-killed.
- **Sane target** for the whole pipeline on one box (local Whisper + render + background agents):
  **4 vCPU / 8 GB RAM**.
- Check before recommending: `free -m; nproc; swapon --show; df -h /`. Swap in use on an idle box is
  the real argument to upgrade — a failed transcript is not.

### Render preflight — run `hyperframes doctor` before promising anything

`hyperframes doctor` is the fastest way to separate "API/quota" problems from "this box can't
render" problems. Read it like this:

| Check | Meaning for the job |
|---|---|
| ✗ Memory (e.g. `1.9 GB total · 1.2 GB available`) | The real blocker for renders. Chromium needs 1.5–2.5 GB → expect failures on long/1080p comps. |
| ✓ Chrome (cache path under `~/.cache/hyperframes/chrome/...`) | Headless browser is bundled — no system Chromium/chrome install needed. "chrome: TIADA" from `which` proves nothing. |
| ✗ whisper-cpp / TTS (Kokoro) / BGM (MusicGen) | **Optional.** Leave them off on a small VPS: transcription goes to Groq Whisper, TTS/music only if the owner asks. |
| ✗ Docker running | Only certain blocks need it; not a render blocker by itself. |
| ✓ FFmpeg / FFprobe / Disk | Baseline capabilities. |

Report to the owner in two buckets — "API settled" vs "hardware still short" — instead of a single
"tak boleh render". On a 2 GB / 2 vCPU box the honest answer is: transcript + subtitle + scene JSON
can be produced now; a heavy MP4 render is what needs the 4 vCPU / 8 GB upgrade.
- Decision matrix, measured numbers and the owner's agreed rollout:
  `references/asr-and-render-capacity.md`.
- **A dead key is a fleet problem, not a model problem.** When the shared provider key hits
  401/402, every worker profile (`writer`, `reviewer`, `researcher`, `coder`, `dokumentalis`)
  is dead too — but the main chat keeps running, so the fleet *looks* fine while every
  delegation silently fails. Audit and repoint them before promising delegated work:
  `references/provider-failover-and-worker-profiles.md` + `scripts/repoint_profiles.py`.
- **Separate summarisation from transcription when answering.** The owner may say "we have
  workers here, just summarise locally" — true for text, irrelevant for audio. Text-only
  models cannot hear the clip; a working summariser does not unblock a video job. Say which
  half is solved and which half is not.

## Format & Aesthetics Selection
- **YouTube Widescreen (16:9 Landscape):** Default for YouTube vlogs, tutorials, and long-form storytelling. Scale to 1280x720 or 1920x1080 with subtle color grading, corner badges, and dynamic bottom subtitles.
- **Shortform Vertical (9:16 Vertical):** For TikTok, Instagram Reels, and YouTube Shorts (720x1280 or 1080x1920) with blurred ambient background and centered foreground.
- **2040 Minimalist Glassmorphism (Apple VisionOS / Sleek HUD):**
  - NO clumsy, thick opaque boxes that clutter the frame or overlap subjects' faces.
  - Use compact translucent dark pills (`rgba(15, 23, 42, 230)`) with delicate 1px borders (`rgba(255, 255, 255, 45)`), rounded corners (radius 12-14px), and refined typography.
  - Keep face areas clear and unobstructed on both driver and passenger sides.
- **CRITICAL ANTI-PATTERN:** Never deliver raw default FFmpeg `drawtext` with generic square black boxes — it looks outdated (2010s aesthetic) and lacks engagement.

## Dynamic Comedic Punch Zooms & "Zoom Katak" (Facial Reaction Cuts)
When comedic timing or high viewer reaction is desired ("kacau muka / high reaction"):
1. Identify spontaneous comedic moments (e.g. failed trademark intro, unhinged confidence declarations, quick banter interruptions).
2. **Standard Punch Zoom:** Instant **1.4x–1.5x Digital Punch Zoom** centered on the subject's face using FFmpeg segmenting:
   - Always upscale base video to uniform canvas (e.g. 1280x720) *before* cropping to prevent negative/excess crop errors.
   - Crop target face (e.g. `crop=560:420:40:40,scale=1280:720,setsar=1`).
   - Tag every segment with `setsar=1` before `concat` to eliminate SAR parameter mismatch errors.
   - Pair each snap-zoom with a subtle SFX cue (*pop* or *snap*) and sleek status badge (e.g. `● TRADEMARK : FAILED`).
3. **"Zoom Katak" / Fisheye Barrel Bulge Effect:**
   - To create the popular comedic "muka kembang macam katak" (bulging cheeks/fisheye meme effect), chain FFmpeg's `lenscorrection` filter:
     `crop=560:420:40:40,scale=1280:720,lenscorrection=cx=0.5:cy=0.4:k1=-0.45:k2=-0.1,setsar=1`
   - `k1=-0.40` to `-0.50` produces pronounced barrel distortion that hilariously stretches facial features.
   - Always pair with a cartoon spring/boing sound cue (`sfx_boing.wav`) for maximum comedic timing.

## Full Timeline Preservation (Zero Frame Cuts)
When the user specifies "kekalkan frame / jangan cut apa-apa":
- Do NOT trim away dead air or cut scenes. Maintain 100% of the raw footage from `0.00s` to the exact final frame.
- Build the entire visual treatment (punch zooms, zoom katak, privacy masks, HUD badges, subtitles) strictly as in-place overlays and segmented concatenations that sum up exactly to the original video duration.

## Studio Privacy Masking (Child / Minor Privacy Blur)
When protecting the privacy of sleeping toddlers, infants, or sensitive personal data:
1. **Never use ugly mosaic / harsh black bars:** It ruins the aesthetic. Instead, use an **elliptical feathered blur** with clean studio aesthetics.
2. **Workflow:**
   - Crop target region (e.g. `crop=240:230:990:490`) and apply strong blur (`avgblur=20` or `boxblur=18:5`).
   - Generate an alpha feather mask PNG (Pillow drawing an anti-aliased white ellipse on transparent background with Gaussian blur for soft feathered edges).
   - Merge blurred stream with feather mask via `alphamerge`, then overlay back onto base canvas at exact coordinates (`overlay=990:490`).
   - Top with a sleek 2040 VisionOS-style capsule badge: `● PRIVACY PROTECTED` or `[ 👶 PRIVACY ON ]`.
   - Ensure the adult hosts' faces and eyes remain 100% sharp and unobstructed.

## Core Production Workflow (LEGACY FFmpeg path — only when an MP4 is explicitly requested)

### 1. Ingest & Inspect
Check stream information and duration:
```bash
ffprobe -v error -show_entries format=duration,size:stream=codec_name,width,height -of json input.mov
```

Extract sample frames (1 frame every 5s) and downsampled audio:
```bash
mkdir -p /tmp/video_inspect
ffmpeg -y -i input.mov -vf "fps=1/5" /tmp/video_inspect/frame_%03d.jpg
ffmpeg -y -i input.mov -vn -ar 16000 -ac 1 /tmp/video_inspect/audio.wav
```

### 2. Multimodal Transcription & Scene Breakdown
Send audio inline to the active Google Gemini endpoint (`${DEFAULT_MODEL}`) to generate structured dialogue timestamps:
```json
[
  {"start": 3.0, "end": 5.5, "speaker": "A", "text": "Short punchy phrase"}
]
```
Break dialogue into 3-5 word bursts for fast visual cadence.

**ASR must be verified before it drives the JSON.** Loud in-car / handheld audio at 32 kbps mono is hard input. Always sanity-read the transcript against the video's context before directing scenes off it. Rules:
1. **Groq `whisper-large-v3-turbo` is the primary ASR lane now** — free, fast, and returns
   `verbose_json` with `segments` + per-segment timestamps, which is exactly what the JSON scene
   schema needs. Extract audio with ffmpeg first (`-vn -ar 16000 -ac 1`), then
   `POST https://api.groq.com/openai/v1/audio/transcriptions` (model `whisper-large-v3-turbo`,
   `response_format=verbose_json`). It handles Manglish/code-switching acceptably; you lose
   per-speaker diarisation, so infer speaker turns from context and say so.
   Gemini inline audio is the **legacy** path — that account is usually unfunded, so do not make
   it the default plan. No local RAM is consumed by either cloud path.
2. If the cloud path is unavailable (quota/credential state), local fallback exists: `scripts/transcribe_local_whisper.py` (faster-whisper). Run it, then **judge the output** — `small` on noisy Malay vlog audio routinely returns nonsense ("Beli-beli ini pagi sob mula", "Saya sudah kebenaran"). Garbled output is a signal to stop, not to paraphrase.
3. Never silently repair a bad transcript by inventing plausible dialogue. Report the ASR failure, list the real segments you did get, and ask the owner for the transcript / auto-captions / a credit top-up. Fabricated subtitles are worse than a delay.

### 3. Modern ASS Subtitles (Advanced SubStation Alpha)
Use `libass` for studio-quality typography with Google Fonts (`Montserrat ExtraBold` or `Poppins Bold`):
- Assign distinct colors per speaker (e.g. Host = vibrant gold `&H0024E1FF&`, Co-host = soft coral `&H00D966FF&`).
- Set thick black outlines (`Outline=3.5`, `Shadow=2`) to guarantee legibility over any background without clunky opaque boxes.
- Subtitle style block example:
```ini
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Host,Montserrat ExtraBold,40,&H0024E1FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,30,30,58,1
Style: CoHost,Montserrat ExtraBold,40,&H00D966FF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,3.5,2,2,30,30,58,1
```

### 4. Interactive Graphic Badges & Pop-Ups
Render high-resolution alpha PNG badges using Pillow (`ImageDraw.rounded_rectangle`):
- **Glassmorphism / Rounded Pills:** Dark translucent slate with subtle colored borders and emoji/icons.
- **Timed Overlays:** Use FFmpeg's `overlay=x:y:enable='between(t, START, END)'`.
- Include context-aware badges: Topic checklist, Inspo source (Pinterest/TikTok), CTA cards (Subscribe + Bell).

### 5. Timed Audio Cues (SFX)
Synthesize or trigger subtle sound effects (*pop*, *chime*, *snap click*) at exact badge timestamps using pure Python standard library `wave` or WAV clips:
```bash
# In FFmpeg filter_complex:
[12:a]adelay=3000|3000,volume=0.8[sfx1];
[0:a][sfx1]amix=inputs=2:duration=first:dropout_transition=2[aout]
```

### 6. Video Delivery
Deliver rendered MP4 directly to Telegram:
```text
MEDIA:/absolute/path/to/output.mp4
```

## Pitfalls & Lessons Learned
- **Deliver one variant, then stop and get a verdict.** The owner iterates by feel ("cuba lagi? Nak cuba kau sampai kau faham cara aku"). Do not batch three options; produce one, ask what to fix. Two consecutive style rejections ("langsung tak creative. Buruk. Font tahun bila ntah") cost more than one careful pass.
- **Self-review rendered output before delivering it.** Extract 3–4 frames at the emotion beats (`ffmpeg -ss <t> -vframes 1 f.jpg`) and look at them yourself; this is how the tofu boxes, the clumsy blue overlay covering the wife's face, and the dated borders were caught. Ship nothing you have not seen a frame of.
- **Emoji in ASS always becomes tofu.** Covered under the emoji pitfall below — but note it recurred: any icon must be a rendered PNG/Vectored layer (or a JSON `icon` field for the web engine), never a unicode glyph inside subtitle text.
- **Prefer the vision/LLM review loop, but never block the deliverable on it.** If cloud vision/ASR credentials are exhausted, say so plainly and offer options (owner supplies transcript / top-up / heavier local model) instead of quietly degrading quality.
- **Fast local Whisper needs manual audio decode.** Current `faster-whisper` + newer PyAV breaks on file input with `TypeError: open() got an unexpected keyword argument 'metadata_errors'`. Fix: decode the WAV yourself with stdlib `wave` + `numpy.float32`, then pass the array to `model.transcribe()`. Script: `scripts/transcribe_local_whisper.py`. Pre-clean audio with `highpass=f=90,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11` first.
- **Audio Stream Multi-Reuse vs Modular Audio Master:** Reusing the same audio input stream multiple times in FFmpeg's `filter_complex` (e.g. `[13:a]adelay=...` followed by another `[13:a]adelay=...`) fails with `matches no streams`. Either branch with `asplit` explicitly, or ideally generate a dedicated `audio_master.wav` via Python/FFmpeg beforehand, then map directly (`-map 0:v -map 1:a`). This decouples complex audio mixing from video filter chains.
- **Zero Unicode Emojis in ASS Subtitles (Tofu Prevention):** Never embed raw unicode emojis (e.g. 🏠, 🚪, 🔑, 🎨, 🪵) in `.ass` dialogue lines. Most standard text fonts lack full color-emoji glyphs, causing `libass` to render ugly square tofu boxes. Use clean text with color accent highlights (`{\\c&H0037E6FF&}...{\\r}`), and render icons strictly inside alpha PNG overlay badges.
- **FFmpeg Concat SAR Mismatch:** When stitching cropped punch-zoom segments with uncropped segments, FFmpeg throws `Input link parameters (SAR ...) do not match`. Always add `,setsar=1` to every video branch before the `concat` filter.
- **Crop Size Exceeding Input:** FFmpeg's `crop` filter fails if crop dimensions exceed input stream dimensions. Always upscale low-res input (e.g. 640x352) to target canvas (1280x720) *before* applying sub-region cropping.
- **Font Availability:** If Google Fonts are missing on Linux hosts, install them via `apt-get install -y fonts-montserrat fonts-inter fonts-roboto` rather than curl stubs.
- **Terminal Backgrounding Guard:** Never place raw `&` characters in FFmpeg shell commands inside python one-liners; write Python build scripts to `.py` files and execute them directly.
- **Resolution Mismatch:** When upscaling 352p or 480p clips to 720p/1080p, always chain Lanczos scaling with an unsharp mask (`unsharp=5:5:0.8:3:3:0.4`) and slight saturation boost to prevent a muddy upscale.
- **Check `md5sum` before analysing a "new" attachment.** The owner re-sent an identical clip labelled as fresh test footage; only the filename differed. Hash it against the previous attachment first — cheap, and it stops you redoing a full pass for nothing.
- **`hermes --profile <name> status` reports the *default* profile's model**, not the named one — so a correctly repointed profile still looks broken. Verify with `hermes profile list`, which prints a Model column per profile. (`config get model` is also unreliable here.)
- **A worker node that answers `/health` has not proven its AI layer works.** Triage by layer: scraping / DB-read / filesystem / system-probe endpoints succeed while anything needing inference returns `{"status":"failed"}` in under a second. Fast failure = dead key, not a timeout. Full triage recipe in `references/provider-failover-and-worker-profiles.md`.
- **Probe credentials with a real request, never by reading config.** A provider entry existing in `config.yaml` says nothing about the key being funded. Fire a 10-token chat completion and read the status code (401 = bad key, 402/RESOURCE_EXHAUSTED = no credit) before you plan any work around it.
