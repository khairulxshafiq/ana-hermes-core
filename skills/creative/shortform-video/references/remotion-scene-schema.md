# Remotion / HyperFrames Scene Schema — Video Data Director contract

The owner's rendering engine (React / Remotion / HyperFrames) consumes this JSON and bakes the video. Your job ends at the JSON.

## Output contract

- One bare, valid JSON **array** starting `[` and ending `]`.
- No prose, no preamble, no closing remarks, no ``` fences, no comments.
- One array element per deliverable clip (`clip_id`, `topic`, `global_settings`, `scenes`).
- `scenes` is a chronological list of micro-beats. `start_time`/`end_time` in decimal seconds, non-overlapping, covering the segment you were asked to direct.
- JSON mode applies to transcript jobs ONLY — normal conversation stays normal voice.

## Skeleton

```json
[
  {
    "clip_id": "hook_01",
    "topic": "Human-readable clip title",
    "global_settings": {
      "theme": "glassmorphism_2040",
      "primary_font": "Montserrat-ExtraBold",
      "input_aspect_ratio": "16:9",
      "target_aspect_ratio": "16:9",
      "resize_mode": "center_crop_face_tracking",
      "channel_branding": {
        "channel_name": "by.naykey",
        "creators": "Nayli & Keyrol",
        "watermark_position": "top_left"
      },
      "background_music": { "track_type": "upbeat_acoustic_vlog", "volume": 0.12 }
    },
    "scenes": [
      {
        "start_time": 0.0,
        "end_time": 2.5,
        "camera": { "motion": "slow_zoom_in", "scale": 1.1, "target": "Keyrol" },
        "subtitle": {
          "speaker": "Keyrol",
          "text": "Max 3-5 words per scene",
          "font": "Montserrat-ExtraBold",
          "style": "text_stroke_shadow",
          "speaker_color": "#FFE124",
          "highlight_words": ["3-5", "words"],
          "highlight_color": "#FFE124"
        },
        "overlays": [
          {
            "type": "glass_badge",
            "trigger_time": 0.4,
            "icon": "⚡",
            "text": "BADGE TEXT",
            "position": "top_center",
            "animation": "spring_bounce_in"
          }
        ],
        "audio_sfx": [
          { "sfx_type": "pop_chime", "trigger_time": 0.4, "volume": 0.8 }
        ]
      }
    ]
  }
]
```

## Enumerations (stay inside these)

| Field | Allowed values |
|---|---|
| `theme` | `glassmorphism_2040` |
| `primary_font` | `Montserrat-ExtraBold` |
| `resize_mode` | `center_crop_face_tracking`, `fit_blurred_backdrop` |
| `camera.motion` | `slow_zoom_in`, `slow_zoom_out`, `pan_to_subject`, `pan_split_dialogue`, `steady_push_in`, `punch_zoom_face`, `auto_pan_subject` |
| `camera.distortion_effect` | `barrel_bulge_fisheye` (a.k.a. "zoom katak"), `subtle_barrel_zoom` |
| `subtitle.style` | `text_stroke_shadow`, `glass_pill_background`, `pop_words` — NEVER a solid box |
| `subtitle.animation` | `pop_words`, `shake`, `fade_in` |
| `overlay.type` | `glass_badge`, `status_tag`, `hud_pill`, `channel_cta_card`, `privacy_mask` |
| `overlay.position` | `top_left`, `top_center`, `top_right`, `bottom_center`, `bottom_right` |
| `overlay.animation` | `slide_in_spring`, `slide_in_smooth`, `slide_in_right`, `spring_bounce_in`, `glitch_in`, `glitch_slam_in`, `fade_in_scale`, `slide_up_fade` |
| `sfx_type` | `pop_chime`, `pop_bubble`, `snap_click`, `boing_spring`, `whoosh_slam`, `whoosh_hit`, `ding_bell`, `chime_bell`, `fail_buzzer` |
| `background_music.track_type` | `lofi_vlog`, `lofi_chill`, `upbeat_acoustic_vlog`, `upbeat_vlog` (volume 0.10–0.15) |

## Speaker palette (by.naykey)

- **Keyrol** (husband): `#FFE124` gold — emphasis accents `#EF4444` red for "SEMUA BUAT SENDIRI" style declarations.
- **Nayli** (wife): `#FF66D9` coral/rose.
- Topic accents: Pinterest `#E60023`, TikTok `#06B6D4`, SPC/floor `#FBBF24`, paint `#38BDF8`, keys/new-home `#34D399`.

## Beat construction heuristics

1. **Hook first (15–45 s budget when extracting a hook clip).** Open on the strongest laugh or the boldest claim; do not open on setup.
2. **Comedy beat pattern:** `punch_zoom_face` + `scale` 1.4 + `barrel_bulge_fisheye` + `boing_spring` SFX + a `status_tag` that names the joke (`TRADEMARK : FAILED`).
3. **Declaration beat pattern:** `punch_zoom_face` + `whoosh_slam` + red highlight on the thesis words + `MODE: 100% D.I.Y` glass badge.
4. **Value beat pattern:** `steady_push_in`, `snap_click` per list item, sequential `hud_pill` PHASE tags (01/02/03) so the viewer sees progress stack up.
5. **Privacy beat:** any sleeping child → `privacy_mask` with `mask_type: feathered_gaussian_blur`, `label: PRIVACY PROTECTED`, `target: baby_yellow_shirt` style descriptors; keep it pinned while the child is in frame.
6. **Close:** `slow_zoom_out` + `channel_cta_card` (`by.naykey • SUBSCRIBE`) + `chime_bell` at 0.9.
7. **Zero cuts when asked to preserve the frame.** If the owner says "kekalkan frame / jangan cut", every scene's time range must tile the full duration with no gaps and no removed footage.

## Worked example (approved by the owner — "Ni baru first class!")

9 scenes over 66.3 s: greeting beat → comedy punch-zoom + `TRADEMARK : FAILED` → key-moment `BARU DAPAT KUNCI` with baby privacy mask → three PHASE hud_pills (cat dinding / SPC / pintu) → red-highlighted `SEMUA BUAT SENDIRI` declaration → Pinterest moodboard → TikTok punch-zoom → subscribe CTA card. Structure it the same way for new footage; swap the dialogue and beats, keep the pacing and the tag vocabulary.
