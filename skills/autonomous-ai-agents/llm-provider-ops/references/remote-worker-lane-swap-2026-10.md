# Remote worker lane swap — Luma (Gemini → Groq free), 25 Okt 2026

Kes sebenar: worker jauh (`luma-us`, GCP) masih hardcode Gemini; kredit Gemini habis, jadi semua
endpoint ber-LLM gagal. Lane ditukar ke Groq **percuma** tanpa ubah logik kod.

## Gejala

```bash
curl -s -X POST http://<REDACTED_IP>:8000/worker/research \
  -H 'Content-Type: application/json' \
  -d '{"query":"harga emas hari ini ringkas","depth":"summary","timeout_sec":60}'
# → {"status":"failed","query":"...","synthesis":"Gagal menghasilkan sintesis.","execution_time_sec":0.48}
```

Ciri penting: gagal dalam **<1 saat** (bukan timeout) → kunci/quota/provider mati, bukan rangkaian.
`GET /health` masih `healthy` dan `/worker/viral`, `/worker/backup` masih OK — sebab semua itu
**tidak** panggil LLM. Jangan guna health sebagai bukti lane LLM hidup.

## Punca

`luma_worker/worker_daemon.py` (3 call site) + `luma_worker/config.py` rujuk `GEMINI_API_KEY`
dengan model `gemini-3.8` / `gemini-3.5`. Kunci sah tetapi kredit projek habis.

## Fix: env-driven lane

Selepas call site dijadikan env-driven:

```python
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1").rstrip("/") + "/chat/completions"
MODEL   = os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
```

Tukar lane = tulis semula 3 baris dalam `/home/khairulshafiq/antigravity-workspace/.env`
(`ENV_PATH = WORKSPACE_DIR / ".env"` — bukan `~/.env`):

```
DEEPSEEK_API_KEY=<GROQ_API_KEY>
DEEPSEEK_BASE_URL=https://api.groq.com/openai/v1
DEEPSEEK_MODEL=openai/gpt-oss-120b
```

```bash
sudo systemctl restart luma-worker && sleep 6 && systemctl is-active luma-worker   # active
```

## Verification sebenar (lulus)

```json
{"status":"success","query":"harga emas hari ini ringkas","synthesis":"**Laporan Ringkas – Harga Emas Hari Ini...**"}
```

Fail kecil untuk swap env boleh di-pipe ke stdin (elak kunci muncul dalam `ps`/history):

```bash
printf '%s\n' "$GROQ_API_KEY" | ssh agy "python3 /tmp/luma_free_lane.py"
```

## Lessons

1. Nama var kekal `DEEPSEEK_*` walaupun nilainya Groq — rename hanya kalau sanggup ubah semua call site.
2. Backup `.env` + `py_compile` guna venv Luma (`/home/khairulshafiq/ana-v2-env/bin/python`) sebelum restart.
3. Delegation mesti bawa lane policy (free-first). Subagent yang diarah "pindah ke DeepSeek" akan
   buat tepat itu, walaupun Boss mahukan lane percuma → kerja berganda.
4. `gcp_worker_client.py research` guna argumen posisi (`research "soalan"`), bukan `--query`.
