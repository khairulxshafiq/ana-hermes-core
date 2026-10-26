# Case log — buang provider berbayar, pindah ke DeepSeek primary (2026-10)

Arahan Boss: "minta buang semua gemini api yang berbayar ni, haha. mahal. pakai apa yang kita ada:
deepseek, groq, openrouter. primary as deepseek. tukar now"

## Keadaan sebelum (config default)

| Lane | Nilai asal |
|---|---|
| `model.default` + 7 alias | `${DEFAULT_MODEL}` pada `custom:google-paid` |
| `model.base_url` | `https://generativelanguage.googleapis.com/v1beta/openai/` |
| `model.timeout_seconds` / `request_timeout_seconds` | 6 / 6 |
| `fallback_providers` | deepseek/deepseek-chat → openrouter/deepseek/deepseek-chat |
| `auxiliary.vision` | openrouter / `google/gemini-2.5-flash` |
| `auxiliary.title_generation` | custom:google-paid / ${DEFAULT_MODEL} |
| `providers` | `google-paid` (key_env `GEMINI_API_KEY_PAID`), `gemini-free`, `byteplus` |
| `custom_providers` | `- *id001` (YAML anchor → google-paid) |
| `image_gen.provider` | `gemini` (plugin `image_gen/gemini` disabled) |

## Yang dikerjakan

1. Backup `config.yaml`, `.env`, `profiles/ana-trade/config.yaml` dengan suffix timestamp.
2. Probe `/models` ketiga-tiga provider → sahkan ID sebenar.
3. Semua tulisan config melalui `hermes config set` / `hermes config unset`.
4. `providers.google-paid` DAN `custom_providers` di-unset bersama (anchor YAML).
5. Ujian chat `max_tokens=10` pada `deepseek-v4-flash` (200 OK, resolved `deepseek-flash`).
6. Ujian vision PNG 64x64 base64 → 200 OK, `prompt_tokens=223` (imej betul-betul masuk).

## Dapatan penting

* `deepseek-v4-flash` tiada dalam `/models` tetapi dihantar OK; server resolve ke `deepseek-flash`.
  Jangan "betulkan" nama ni dalam profile pekerja tanpa sebab.
* `deepseek-flash` satu-satunya model DeepSeek yang ada `input_modalities: ["text","image"]`
  → layak jadi `auxiliary.vision`.
* Groq tiada model vision dalam senarai semasa → jangan letak pada lane vision.
* OpenRouter `:free` yang ada `image` modality: `nvidia/nemotron-3.5-super-vl:free`,
  `google/gemma-4-*-it:free`, `thinkingmachines/inkling*:free`,
  `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`.

## Blocker yang ditemui (belum selesai)

1. `GEMINI_API_KEY`, `GEMINI_API_KEY_PAID`, `GEMINI_API_KEY_FREE` **identik** (53 aksara sama).
   Tiada "free lane" sebenar — quota 429 tetap pada projek yang sama. `GOOGLE_API_KEY` lain nilai.
2. `image_gen.provider: gemini` masih satu-satunya lane jana imej dalam config; ujian
   `gemini-3.1-flash-image` dengan kunci free balas **429 quota exceeded**.
   Alternatif belum dipasang: Replicate FLUX (`~/scripts/ana_lora_gen.py`), ComfyUI, BytePlus.
3. `~/scripts/ana_nanobanana.py` + `aura_nanobanana.py` baca `GEMINI_API_KEY_PAID` secara
   hardcode (`TIERS` → `gemini-3.1-flash-image` / `gemini-pro-image`) — mati kalau kunci dibuang.
4. Profile `ana-trade` masih `${DEFAULT_MODEL}` (aux dia guna `custom:byteplus`, bukan gemini).
5. Gateway belum reload → sesi semasa masih pada model lama.

## Ikutan untuk sesi seterusnya

* Baca semula `hermes config get model` + `hermes profile list` sebelum mula — jangan andaikan
  keadaan masih sama seperti log ni.
* Selesaikan HITL dengan Boss dulu (buang image-gen Gemini sepenuhnya vs kekalkan sementara)
  sebelum padam kunci dari `.env`, sebab itu mematikan jana imej.
