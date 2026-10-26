# Audit liveness provider + migrasi Groq free (25 Okt 2026)

Kes sebenar: Boss arah "delete je Google API, image gen Gemini tinggal, worker guna Groq free
kalau boleh, otherwise DeepSeek". Ringkasan apa yang diuji, apa yang mati, dan urutan kerja yang dipakai.

## 1. Fingerprint kunci dulu (elak padam kunci yang sebenarnya sama)

```bash
set -a; source ~/.hermes/.env; set +a
for v in GEMINI_API_KEY GEMINI_API_KEY_PAID GEMINI_API_KEY_FREE GOOGLE_API_KEY GROQ_API_KEY DEEPSEEK_API_KEY OPENROUTER_API_KEY; do
  val="${!v}"; [ -n "$val" ] && printf "%-24s %s (len %s)\n" "$v" "$(printf %s "$val" | md5sum | cut -c1-10)" "${#val}"
done
```

Hasil:
| Kunci | Fingerprint | Nota |
|---|---|---|
| `GEMINI_API_KEY` | 4d3a8d5fcf (53) | sama dengan PAID & FREE |
| `GEMINI_API_KEY_PAID` | 4d3a8d5fcf (53) | satu-satunya yang perlu kekal (image gen) |
| `GEMINI_API_KEY_FREE` | 4d3a8d5fcf (53) | "free lane" = ilusi → dibuang |
| `GOOGLE_API_KEY` | 8ed09b63a0 (53) | projek lain, tiada rujukan dalam skrip → dibuang |
| `GROQ_API_KEY` | 88cb7de1ec (56) | hidup |
| `DEEPSEEK_API_KEY` | 02e457491c (35) | hidup |
| `OPENROUTER_API_KEY` | f17a59369d (73) | **mati** (401) |

## 2. Liveness probe (setiap lane, bukan primary sahaja)

| Provider | Keputusan | Bukti |
|---|---|---|
| deepseek (teks) | HIDUP | `deepseek-v4-flash` jawab BM, JSON OK |
| deepseek (vision) | HIDUP | PNG 64x64 data-URI → `prompt_tokens` ~178, jawab warna |
| groq free | HIDUP | `openai/gpt-oss-120b`: tool call `get_quote{"symbol":"1155.KL"}` OK, 0.9s, `x-ratelimit-limit-requests: 1000` |
| gemini | HIDUP (image) | `GET /v1beta/models` 200, ada `gemini-2.5-flash-image`, `gemini-3-pro-image`, `gemini-3.1-flash-image` |
| openrouter | MATI | `401 {"message":"User not found"}` untuk semua model |
| byteplus (ark-code-latest) | MATI | `AccountQuotaExceeded`, reset `2026-10-29 23:59:59 +0800` |
| byteplus (seed-2-0-lite) | MATI | `ModelNotOpen` — model tak diaktifkan dalam Ark Console |

Groq model inventory ketika itu (11 total): `openai/gpt-oss-120b`, `openai/gpt-oss-20b`,
`qwen/qwen3.8-27b`, `gpt-oss-safeguard-20b`, 2x prompt-guard. Tiada llama-3.3, tiada vision.

Nota tingkah laku Groq `gpt-oss`:
* `response_format=json_object` + `tools` → `json mode cannot be combined with tool/function calling`.
* JSON mode dengan `max_tokens=50` → `json_validate_failed` ("max completion tokens reached before
  generating a valid document"); `max_tokens=900` → JSON sah. Reasoning token makan budget.
* Model ini hantar `reasoning_tokens` dalam `usage.completion_tokens_details` — bajet token lebih.

## 3. Config akhir selepas migrasi

| Profile | Primary | Fallback |
|---|---|---|
| `default` | deepseek-v4-flash | groq/gpt-oss-120b, byteplus/ark-code-latest |
| `writer`/`reviewer`/`researcher`/`coder`/`dokumentalis` | deepseek-v4-flash | groq/gpt-oss-120b, byteplus/ark-code-latest |

Semua: `auxiliary.vision` = deepseek/`deepseek-flash`, `auxiliary.title_generation` = deepseek-v4-flash,
`custom_providers` blok `google-paid` dibuang, provider `gemini-free` dibuang, `image_gen.provider` kekal `gemini`.

Sahkan: `hermes profile list` (model per profile) + `hermes config check`.

## 4. Skrip yang terkesan

* `~/scripts/ana_lora_gen.py` — Vision QA + SCALPT prompt compiler sebelum ini guna OpenRouter
  `google/gemini-2.5-flash` (mati). Dipindah ke `https://api.deepseek.com/v1/chat/completions`
  dengan `deepseek-v4-flash` (compiler) dan `deepseek-flash` (vision QA), key `DEEPSEEK_API_KEY`.
* `~/scripts/ana_vision_worker.py` — MASIH rujuk `GEMINI_API_KEY_FREE` yang dah dipadam → perlu
  dipindah ke `deepseek-flash` sebelum dipanggil lagi.
* `~/scripts/ana_nanobanana.py` / `aura_nanobanana.py` — kekal guna `GEMINI_API_KEY_PAID`
  (`gemini-3-pro-image` / `gemini-3.1-flash-image`) sebab lane imej dikekalkan.

## 5. Belum selesai ketika sesi tamat

1. Patch `ana_vision_worker.py` → DeepSeek vision.
2. `systemctl --user reload hermes-gateway` supaya config baru aktif untuk sesi baru.
3. Keputusan Boss: buang terus `OPENROUTER_API_KEY` (mati) atau tunggu kunci baru.

## 6. Pelajaran proses

* Jangan bina fallback chain daripada config lama — sesetengah lane dalam chain memang mati
  berbulan tanpa disedari (`hermes profile list` tak tunjuk status liveness).
* Kalau Boss cakap "delete je", tetap fingerprint dulu: tiga nama kunci boleh simpan satu nilai,
  dan satu lagi boleh jadi kunci projek berasingan yang tiada rujukan.
* Urutan selamat buang kunci: `grep` skrip → patch skrip → `py_compile` → padam kunci → baru reload.
