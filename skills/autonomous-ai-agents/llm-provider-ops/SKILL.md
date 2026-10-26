---
name: llm-provider-ops
description: Switch/prune LLM providers in Hermes config or app code.
version: 1.0.0
---

# LLM Provider Ops (Hermes model routing & cost control)

Use when Boss says: "tukar model primary", "buang provider mahal", "pakai apa yang kita ada",
"why is it using <provider>", "fallback kena tukar", atau bila nak audit kunci API mana yang bil.

Kerja ni sentuh `~/.hermes/config.yaml` (security-sensitive) dan boleh mematikan
vision / image-gen / worker profiles kalau dibuat semberono. Ikut urutan di bawah.

---

## 0. Recon dulu (jangan sentuh apa-apa lagi)

```bash
grep -n -A40 "^model:" ~/.hermes/config.yaml          # primary, aliases, base_url, timeouts
grep -n -A15 "^fallback_providers:" ~/.hermes/config.yaml
grep -n -A20 "^auxiliary:" ~/.hermes/config.yaml      # vision + title_generation
grep -n -A20 "^providers:" ~/.hermes/config.yaml      # custom provider + key_env
hermes profile list                                    # model SETIAP profile (lapor beza!)
```

`hermes profile list` penting: session utama boleh jadi deepseek sementara profile
`writer` masih pada provider berbayar. Jangan kata "dah tukar semua"
sebelum tengok senarai ni.

Backup dulu:

```bash
cd ~/.hermes && cp config.yaml config.yaml.bak.$(date +%Y%m%d_%H%M%S) \
  && cp .env .env.bak.$(date +%Y%m%d_%H%M%S)
# profile config pun sama: cp profiles/<nama>/config.yaml profiles/<nama>/config.yaml.bak.<ts>
```

---

## 1. SAHKAN model ID betul-betul wujud (jangan percaya nama dalam config)

Nama dalam config boleh jadi alias yang server resolve sendiri, atau terus tak wujud.
Probe `GET {base_url}/models` setiap provider, kemudian hantar satu chat completion murah:

```bash
python3 ~/.hermes/skills/autonomous-ai-agents/llm-provider-ops/scripts/probe_provider_models.py
```

Fakta yang pernah disahkan (2026-10):
* `https://api.deepseek.com/v1/models` → `deepseek-flash` (text+image, ctx 1M) dan `deepseek-v4-pro` (text).
  `deepseek-v4-flash` **tidak** disenaraikan tetapi dihantar OK — server resolve ke `deepseek-flash`.
  Jadi alias lama dalam profile pekerja masih jalan.
* Groq (`/openai/v1/models`) tiada model vision masa ni — jangan letak Groq pada lane vision.
* OpenRouter: tapis `architecture.input_modalities` untuk `image`; model `:free` yang boleh vision
  (contoh `nvidia/nemotron-3.5-super-vl:free`) sesuai jadi fallback vision kosong.

### 1b. Probe LIVENESS setiap provider dalam chain (bukan model primary sahaja)

Config lama boleh merujuk provider yang **kunci dah mati atau quota habis**. Sebelum membina
fallback chain, hantar satu call murah pada SETIAP provider yang akan dipakai:

```bash
set -a; source ~/.hermes/.env; set +a
curl -s -m 40 https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"<model-id>","messages":[{"role":"user","content":"Reply OK"}],"max_tokens":20}'
```

Status yang disahkan 25 Okt 2026 (semak semula — jangan andaikan kekal):
* OpenRouter → `401 {"message":"User not found"}` → kunci mati; fallback chain yang bergantung padanya cuma hiasan.
* BytePlus → `AccountQuotaExceeded` (reset hujung bulan) + `ModelNotOpen` untuk `seed-2-0-lite`
  → tak boleh dipakai walaupun kunci sah.
* Gemini → `GET /v1beta/models?key=$GEMINI_API_KEY_PAID` pulang 200 + `gemini-*-image`
  → selamat kekal untuk lane `image_gen` sahaja.
* Groq free → tinggal `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b`
  (llama-3.3-70b dah tiada; tiada model vision langsung).
* Groq juga bawa **STT percuma**: `whisper-large-v3` + `whisper-large-v3-turbo`
  (`POST /openai/v1/audio/transcriptions`, `response_format=verbose_json` → ada `segments` + timestamp).
  Ini lane transkripsi default bila RAM VPS tak cukup untuk Whisper lokal — jangan pasang whisper.cpp
  dan jangan bergantung pada Gemini untuk audio.

Peraturan: primary/fallback dipilih daripada senarai yang **baru diuji hidup**, bukan disalin
daripada config lama. Kalau satu-satunya lane hidup cuma DeepSeek, chain 2 langkah (groq ↔ deepseek)
lebih jujur daripada chain 4 langkah yang separuh mati.

---

## 2. Tulis config — WAJIB guna CLI, bukan patch/write_file

`patch`, `write_file` dan `execute_code` **ditolak** untuk `~/.hermes/config.yaml`
("Refusing to write to Hermes config file"). Guna CLI:

```bash
hermes config set model.default deepseek-v4-flash
hermes config set model.provider deepseek
hermes config set model.base_url https://api.deepseek.com/v1
hermes config set model.timeout_seconds 30          # 6s terlalu ketat utk model reasoning
hermes config set model.request_timeout_seconds 120

# alias satu-satu (coding/reason/easy/bulk/copywrite/writer/vision)
for a in coding reason easy bulk copywrite writer; do
  hermes config set model.aliases.$a.provider deepseek
  hermes config set model.aliases.$a.model deepseek-v4-flash
done
hermes config set model.aliases.vision.provider deepseek
hermes config set model.aliases.vision.model deepseek-flash

# aux lanes — selalu tertinggal kalau tak nampak
hermes config set auxiliary.vision.provider deepseek
hermes config set auxiliary.vision.model deepseek-flash
hermes config set auxiliary.title_generation.provider deepseek
hermes config set auxiliary.title_generation.model deepseek-v4-flash
```

`fallback_providers` (list) terima **JSON array string**:

```bash
hermes config set fallback_providers '[{"provider":"groq","model":"openai/gpt-oss-120b","key_env":"GROQ_API_KEY","request_timeout_seconds":25},{"provider":"openrouter","model":"deepseek/deepseek-v4-flash","key_env":"OPENROUTER_API_KEY","request_timeout_seconds":30}]'
```

Buang provider:

```bash
hermes config unset providers.google-paid
hermes config unset custom_providers   # anchor list - WAJIB buang sekali (lihat pitfall)
```

Semak: `hermes config get providers`, `hermes config get model`, `hermes config check`.

### 2b. Profile pekerja: CLI `config set` TIDAK cukup

`hermes config set` menulis config utama / profil aktif sahaja. Bila perlu migrasi 5-7 profile
serentak (`writer`, `reviewer`, `researcher`, `coder`, `dokumentalis`):

1. Backup setiap satu: `cp profiles/<nama>/config.yaml profiles/<nama>/config.yaml.bak.<ts>`.
2. Fail config Hermes **tiada komen** (`grep -c '^\s*#'` = 0) → YAML round-trip selamat.
   Dalam `execute_code`: `yaml.safe_load` → ubah `model` / `fallback_providers` /
   `auxiliary.vision` / `auxiliary.title_generation` / buang `custom_providers` → `yaml.safe_dump`.
3. Sahkan: `hermes profile list` mesti tunjuk model baru pada SETIAP profile + `hermes config check` bersih.
4. Jangan sentuh `image_gen` profile — biar kekal `gemini` kalau Boss nak lane imej hidup.

---

## 3. Ujian sebelum reload (jangan reload buta)

* **Text**: satu chat completion `max_tokens=10` pada model primary + setiap fallback.
* **Vision**: hantar imej PNG kecil sebagai `data:image/png;base64,...` dalam `image_url`
  pada model yang diklaim vision-capable. Kalau `usage.prompt_tokens` melonjak (~200+ untuk 64x64),
  imej betul-betul masuk. Jangan percaya label sahaja.
* **Reload**: `systemctl --user reload hermes-gateway` (tanpa putus sesi).
  Sesi semasa masih pegang model lama sampai reload — beritahu Boss.

---

## 4. Audit kunci & kos (bahagian yang selalu terlepas)

```bash
grep -v '^#' ~/.hermes/.env | grep -E 'API_KEY|TOKEN' | sed 's/=.*/=[REDACTED]/'
grep -rln "GEMINI_API_KEY\|OPENAI_API_KEY\|REPLICATE_API_TOKEN" ~/scripts ~/.hermes/skills 2>/dev/null
```

Bandingkan nilai sebenar kunci (bukan nama) — dua nama lain boleh simpan **kunci yang sama**.
Contoh disahkan: `GEMINI_API_KEY`, `GEMINI_API_KEY_PAID`, `GEMINI_API_KEY_FREE` semua identik
(53 aksara sama) → "free lane" itu ilusi, quota tetap kena tolak pada projek berbayar yang sama.
`GOOGLE_API_KEY` pula nilai lain (projek berasingan).

Sebelum padam kunci `.env`, senaraikan skrip yang bergantung padanya dan beritahu Boss
kesannya (contoh: `ana_nanobanana.py` / `aura_nanobanana.py` baca `GEMINI_API_KEY_PAID`).

---

## 5. Kesan sampingan yang WAJIB disebut kepada Boss

| Lane | Kalau provider dibuang |
|---|---|
| `model.*` (teks) | Selamat, asalkan fallback ada |
| `auxiliary.vision` | ANA buta pada gambar Telegram |
| `image_gen.provider` | DeepSeek/Groq tak jana imej — kena pindah ke Replicate FLUX / ComfyUI / BytePlus |
| Profile pekerja (`writer`, `coder`, …) | Ada blok `model:` sendiri, tak warisi config utama |
| Skrip `~/scripts/*` | Baca env key terus, bukan config |

Jangan buang lane imej tanpa kebenaran — tanya guna HITL one-tap buttons
(`/home/ubuntu/scripts/tg_survey_buttons.py`) dengan pilihan jelas + implikasi.

---

## 6. Repoint app/service code yang hardcode provider (bukan config Hermes)

Bila provider mati tapi servis lain (worker daemon, bot, cron script) masih hardcode
`generativelanguage.googleapis.com/...:generateContent` + nama model Gemini, config Hermes
tak tolong. Kena patch kod servis itu sendiri. Kes disahkan: `luma-worker.service` di GCP,
`len/synthesis` gagal dalam 0.5s sebab akaun Gemini habis kredit.

Urutan yang berjaya:

1. **Recon call site, bukan seluruh repo.** `grep -rn "GEMINI\|gemini-" <pkg>/*.py` →
   kira berapa `api_key = GEMINI_API_KEY` + `for model in ["${DEFAULT_MODEL}", ...]`.
   Kalau bilangan call site terhad (3-4), patch satu-satu lebih selamat daripada refactor.
2. **Cari env file sebenar.** `systemctl cat <svc>` — kalau TIADA `EnvironmentFile=`,
   env datang dari `load_dotenv()` dalam kod. Semak `Path(__file__).parent.parent / ".env"`
   dalam modul itu; itulah fail yang perlu ditambah kunci.
3. **Tambah kunci tanpa echo.** Hantar nilai melalui stdin, bukan hujah shell (hujah masuk
   `ps`/history/journal):
   ```bash
   KEY=$(grep -m1 '^DEEPSEEK_API_KEY=' ~/.hermes/.env | cut -d= -f2- | tr -d '"\r')
   printf '%s' "$KEY" | ssh host 'f=/path/.env; [ -n "$(tail -c1 "$f")" ] && printf "\n" >> "$f"; \
     read -r K; printf "DEEPSEEK_API_KEY=%s\n" "$K" >> "$f"'
   # sahkan tanpa dedah nilai: banding sha256 prefix
   ```
   Semak `grep -c '^KEY='` = 1 (elak duplicate) dan perms kekal `600`.
4. **Satu helper dikongsi, bukan 3 salinan.** Tulis `call_deepseek_llm(prompt, temperature,
   max_tokens, timeout) -> str` dan ganti setiap call site dengan 2-3 baris. Kekalkan
   **signature + return shape** fungsi asal dan kekalkan string fallback asal supaya
   endpoint lain tak berubah kelakuan.
5. **Backup + compile dengan python venv servis**, bukan python sistem:
   `cp -a f f.bak.<ts>` → `scp` → `/path/venv/bin/python -m py_compile f`.
6. **Uji 3 lapis**: (a) `curl` endpoint utama yang boss guna, (b) `GET /health`,
   (c) call site lain yang tak ada endpoint HTTP murah — import modul dalam venv servis dan
   `asyncio.run()` fungsi itu terus:
   ```bash
   cd <workspace> && venv/bin/python -c "\
   import asyncio; from pkg.mod import fn_a, fn_b; \
   async def m(): print(len(await fn_a('t','c'))); print(len(await fn_b('t','c')))
   asyncio.run(m())"
   ```
   Ini buktikan semua call site hidup tanpa perlu trigger scraping/IO yang perlahan.

Butiran penuh (kod helper, arahan patch, output ujian) →
`references/app-code-provider-migration-2026-10-25.md`.

---

## 6. Remote worker / app code: tukar lane guna ENV, bukan kod

Bila provider sesebuah servis jauh (contoh worker Python yang buat LLM call terus, bukan Hermes
config), jangan hardcode ID model baru ke dalam kod setiap kali lane ditukar. Buat call site baca
**base_url / model / api_key dari env**, kemudian tukar lane dengan edit env sahaja:

```python
API_KEY  = os.environ.get("<LANE>_API_KEY", "")
API_URL  = os.environ.get("<LANE>_BASE_URL", "https://api.deepseek.com/v1").rstrip("/") + "/chat/completions"
MODEL     = os.environ.get("<LANE>_MODEL", "deepseek-v4-flash")
```

Kelebihan yang terbukti (Luma, 25 Okt 2026): lane ditukar Gemini → DeepSeek → **Groq free** tanpa
sentuh semula logik kod; cukup tulis semula 3 baris env + restart servis.

### Dasar lane: FREE dulu (arahan Boss 25 Okt 2026)

Untuk worker/sub-agent automatik, **jangan default ke provider berbayar**. Urutan pilihan:
1. Groq free (`openai/gpt-oss-120b`, teks + tool calling, 1000 req/hari)
2. OpenRouter `:free` — hanya bila ada kunci sah (kunci lama boleh mati 401; jangan andaikan)
3. DeepSeek berbayar — hanya bila free tier tak cukup/tiada lane, atau Boss minta

Bila kau hantar `delegate_task` untuk migrasi provider, **tulis lane policy ni dalam context**.
Kesilapan sebenar: subagent diarah pindah worker ke DeepSeek, Boss pula mahu lane percuma —
kerja terpaksa di-ulang.

### Verify remote lane dengan endpoint servis itu sendiri

`systemctl is-active` / `/health` hanya bukti proses hidup. Endpoint tanpa-LLM (scrape, DB, backup,
watchdog) kekal OK walaupun kunci LLM mati; yang gagal hanya endpoint ber-LLM (research/summarize)
dan ia balas `{"status":"failed"}` dalam <1 saat. Sentiasa panggil satu endpoint ber-LLM selepas
restart, dan terima hanya `"status":"success"` + kandungan tak kosong.

### 6c. Rename lane env var (DEEPSEEK_* → LLM_*) — perangkap NameError

Bila kod worker mula-mula di-patch ke satu provider (var `DEEPSEEK_API_KEY/BASE_URL/MODEL`),
kemudian Boss mahu lane lain, jangan biar nama var terikat pada provider. Rename ke
`LLM_API_KEY / LLM_BASE_URL / LLM_MODEL` + kekalkan fallback nama lama:

```python
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
```

Perangkap sebenar (25 Okt 2026, luma-worker): selepas rename aku tambah flag terbitan
`_is_deepseek_lane = "deepseek.com" in LLM_BASE_URL` — **`LLM_BASE_URL` tak pernah wujud sebagai
module variable**, ia hanya dibaca inline dalam baris `os.environ.get("LLM_BASE_URL", ...)` yang
membina `LLM_API_URL`. Hasilnya `NameError` masa import: `systemctl` tunjuk `active` sekejap
(autorestart), `py_compile` lulus (NameError = runtime, bukan sintaks), dan `curl /health`
pulang **body kosong**. Fix: baca env terus —
`_is_deepseek_lane = "deepseek.com" in os.environ.get("LLM_BASE_URL", "")`.

Ikut urutan ni setiap kali rename:

1. `grep -n "DEEPSEEK_\|LLM_" file` dulu — pastikan setiap nama yang kau rujuk memang wujud
   sebagai pemboleh ubah modul (bukan cuma string env).
2. Gate param khusus provider ikut host, jangan hantar buta. `"thinking":{"type":"disabled"}`
   hanya sah untuk `api.deepseek.com`; Groq menolaknya → satu request gagal + retry setiap call
   = 2x penggunaan kuota harian. Contoh:
   ```python
   if attempt == 0 and _is_deepseek_lane:
       payload["thinking"] = {"type": "disabled"}
   ```
3. Selepas restart: tunggu ~3s, kemudian `curl` endpoint. **Body kosong = proses belum siap atau
   crash** — semak `systemctl is-active` DAN `journalctl -u <svc> -n 15`. Jangan ulang curl
   berkali-kali dan jangan andaikan servis sihat sebab `is-active` kata `active`.
4. Uji endpoint ber-LLM dan bandingkan dengan baseline sebelum rename (`success` + panjang teks).

### 6d. Edit daemon jauh secara bedah (buang satu watcher/check)

Bila Boss suruh buang satu bahagian daemon (contoh check `broker_ok` yang sentiasa false sebab
broker gateway bind `<host>` dan tak boleh dicapai dari GCP):

1. `grep -n "<symbol>" pkg/*.py` → kira semua tapak (state dict, assignment, `is_down` condition,
   log line, alert `reasons.append`, payload JSON).
2. Tulis skrip patch **berasaskan baris** (bukan regex besar) yang: backup `.bak.<tag>`, buang baris
   tepat, ganti syarat (`is_down = not bridge_ok or not broker_ok` → `is_down = not bridge_ok`),
   kemudian assert `"<symbol>" not in new_text` sebelum tulis.
3. `py_compile` guna venv servis → restart → `curl /health` → **sahkan payload JSON tak lagi ada
   key itu** (`watchdog: {'bridge_ok': True, 'failures': 0}`) → uji satu endpoint ber-LLM untuk
   pastikan pembedahan tak rosakkan laluan lain.

Jangan cuma set flag `True`: Boss minta "padam", bukan "sorok". Buang check + alert + payload
sekali, supaya tiada alert palsu berulang.

---

## Pitfalls

* ❌ `patch`/`write_file` pada `config.yaml` → ditolak. Guna `hermes config set|unset`.
* ❌ `hermes config unset providers.google-paid` sahaja, tinggal `custom_providers: - *id001`.
  Anchor YAML akan jadi rujukan tergantung. Buang kedua-duanya.
* ❌ Anggap `hermes --profile X status` melapor model profile X — ia lapor model default.
  Guna `hermes profile list`.
* ❌ Timeout 6s pada provider reasoning → gagal senyap. 30s/120s lebih realistik.
* ❌ Andaikan nama model dalam config = ID sah provider. Probe `/models` dulu.
* ❌ Terus reload gateway sebelum uji chat + vision — kalau primary baru rosak, semua lane mati.
* ⚠️ `image_gen.provider: gemini` boleh kekal merujuk plugin yang disabled; sahkan lane imej
  sebenar (`ana-image` dispatcher / `ana_lora_gen.py`) sebelum mengaku imej masih jalan.
  Semak fail itu benar-benar WUJUD — skill `ana-image`/`dispatcher.py` & `~/.hermes/ana_image_config.json`
  pernah tiada langsung pada VPS ini; lane imej sebenar = `~/scripts/ana_nanobanana.py` (Nano Banana)
  dan `~/scripts/ana_lora_gen.py` (Replicate FLUX + Vision QA).
* ❌ Padam kunci `.env` SEBELUM repoint skrip yang membacanya. `ana_vision_worker.py` baca
  `GEMINI_API_KEY_FREE`; bila kunci dibuang, skrip mati senyap. Urutan betul:
  `grep -rn "KEY_NAME" ~/scripts ~/.hermes/skills` → patch skrip → `python3 -m py_compile` → baru padam kunci.
* ❌ Andaikan `hermes config set` mengubah profile pekerja. Ia tulis config utama/profil aktif sahaja
  (rujuk §2b). Bukti wajib: `hermes profile list`.
* ❌ Groq `gpt-oss-*`: `response_format: json_object` tak boleh digabung dengan `tools`
  (`json mode cannot be combined with tool/function calling`), dan JSON mode dengan `max_tokens` kecil
  gagal `json_validate_failed` sebab reasoning token makan budget → guna `max_tokens` ≥ 800.
* ❌ Lapor "dah migrasi semua" sebelum uji lane vision dengan imej sebenar. `deepseek-flash` sah
  terima imej (PNG 64x64 → prompt_tokens melonjak); Groq tiada lane vision.
* ❌ Hantar `delegate_task` migrasi provider tanpa menyatakan lane policy. Kalau tak dinyatakan,
  lane berbayar jadi default — dan Boss akan tolak ("guna yg free model"). Tulis dalam context:
  free dulu (Groq `openai/gpt-oss-120b` / OpenRouter `:free`), berbayar hanya dengan kebenaran.
* ❌ Samakan "kunci mati" dengan "lane free tak boleh dipakai". OpenRouter `:free` masih pilihan sah
  **selepas** Boss buat kunci baru — jangan tutup lane itu, minta kunci baru.
* ❌ Anggap servis jauh sihat sebab `systemctl is-active` / `/health` OK. Endpoint tanpa-LLM kekal
  hidup walaupun kunci LLM mati; uji satu endpoint ber-LLM dan terima hanya `"status":"success"`.
* ❌ `deepseek-v4-flash` (= alias `deepseek-flash`) ialah **model reasoning**: `content` boleh
  pulang KOSONG sebab reasoning token makan `max_tokens` (disahkan: `max_tokens` kecil →
  `content: ""`, `reasoning_content` 380 aksara). Dua fix, pakai kedua-duanya:
  `"thinking":{"type":"disabled"}` dalam payload (→ 1.4s, `reasoning_content` len 0) **dan**
  fallback baca `reasoning_content` kalau `content` kosong. Uji dengan `max_tokens` ≥ 512.
* ❌ Anggap `patch` fuzzy-match hanya ubah baris yang dimaksudkan. Dalam sesi luma, patch
  berjaya "rename" `BOSS_CHAT_ID` → placeholder dari konteks saya. Selepas SETIAP patch pada
  fail produksi, semak diff hunk dan `grep` simbol jiran yang tak sepatutnya berubah.
* ❌ Hantar kunci API sebagai hujah shell (`ssh host "KEY=$KEY ..."`) — masuk `ps`/journal.
  Guna stdin (`printf '%s' "$KEY" | ssh host 'read -r K; ...'`), sahkan dengan sha256 prefix.
* ❌ Compile guna `python3` sistem untuk kod yang jalan bawah venv servis — dependency/versi
  lain. Sentiasa venv servis itu (`/path/venv/bin/python -m py_compile`).
* ❌ Anggap `py_compile` lulus = selamat. `NameError` (contoh selepas rename var jadi
  `_is_deepseek_lane = "deepseek.com" in LLM_BASE_URL` sedangkan `LLM_BASE_URL` tak wujud)
  hanya meletup masa import → servis restart-loop, `curl` pulang body kosong. Semak
  `journalctl -u <svc> -n 15` bila body kosong.
* ❌ Hantar param khusus satu provider (`"thinking":{"type":"disabled"}`) tanpa gate host.
  Di Groq ia ditolak, lalu fallback retry tanpa param → **2 request untuk setiap call**,
  separuh kuota harian terbakar. Gate ikut base_url / provider.
* ❌ Tafsir body kosong selepas `systemctl restart` sebagai "lane mati". Uvicorn ambil 1-3s untuk
  startup; tunggu, retest, dan bezakan dengan crash sebenar melalui journal.
* ❌ Terima `{"status":"success"}` tanpa baca kandungan. `gpt-oss-120b` kadang pulang ayat enggan
  ("Maaf, saya tidak dapat membantu…") untuk prompt tertentu — nampak macam berjaya, sebenarnya
  sampah. Semak panjang/sanity teks; kalau < ~80 aksara, retry dengan rephrasing atau tukar lane.

---

## Support files
* Skill berkaitan: `google-oauth-tokens` — bila "API bermasalah" sebenarnya token OAuth
  (`invalid_grant`, refresh token mati 7 hari, SA tiada kuota Drive), bukan lane LLM.
* `scripts/probe_provider_models.py` — senarai model + modaliti + ujian chat/vision untuk
  deepseek, groq, openrouter. Jalankan sebelum dan selepas tukar provider.
* `references/provider-switch-2026-10.md` — transkrip kes sebenar: buang Gemini berbayar,
  pindah ke DeepSeek primary + Groq/OpenRouter fallback, termasuk apa yang gagal.
* `references/provider-liveness-audit-2026-10-25.md` — audit liveness penuh: fingerprint kunci,
  status hidup/mati setiap provider (OpenRouter 401, BytePlus quota/ModelNotOpen, Groq inventory),
  config akhir per profile, dan skrip yang terkesan (`ana_lora_gen.py`, `ana_vision_worker.py`).
* `references/remote-worker-lane-swap-2026-10.md` — kes worker jauh (Luma) Gemini → Groq free pakai
  env indirection: env var, fail env yang betul, output verification sebenar, dan kenapa
  `systemctl is-active` bukan bukti lane LLM hidup.
* `references/app-code-provider-migration-2026-10-25.md` — repoint kod servis (bukan config):
  luma_worker Gemini→DeepSeek, helper `call_deepseek_llm`, pemindahan kunci tanpa echo,
  dan output ujian sebenar (research endpoint 200 + synthesis 3261 aksara).
* `references/remote-daemon-rename-and-watchdog-2026-10-25.md` — rename lane var ke `LLM_*`,
  bug `NameError` yang lulus `py_compile`, gate param `thinking` ikut host, prosedur bedah
  buang watcher `broker_ok` (7 baris), dan quirk `gpt-oss-120b` pulang ayat enggan.
