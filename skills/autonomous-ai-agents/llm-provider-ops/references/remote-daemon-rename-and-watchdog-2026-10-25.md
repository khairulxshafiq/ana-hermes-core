# Luma worker — lane rename + watchdog surgery (25 Okt 2026)

Kes sebenar pada `luma-worker.service` (GCP `agy` / `LumaOS`, `<REDACTED_IP>:8000`,
pkg `/home/khairulshafiq/antigravity-workspace/luma_worker`). Semua output di bawah
adalah output sebenar, bukan ilustrasi.

## 1. Kenapa lane kena env-driven

Selepas migrasi pertama Gemini → DeepSeek, kod simpan `DEEPSEEK_API_KEY/BASE_URL/MODEL`.
Boss kemudian arahkan lane **percuma** (Groq). Dengan env indirection, lane ditukar tanpa
sentuh logik:

```
# .env (mode 600)
LLM_API_KEY=<groq key>          # dihantar via stdin, bukan hujah shell
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
```

Kod:
```python
LLM_API_KEY = os.environ.get("LLM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY", "")
LLM_API_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/") + "/chat/completions"
LLM_MODEL   = os.environ.get("LLM_MODEL", "deepseek-v4-flash")
```

## 2. Bug rename yang memakan masa (direkod supaya tak berulang)

Skrip rename aku tambah flag terbitan:

```python
# SALAH - LLM_BASE_URL tak pernah wujud sebagai module variable
_is_deepseek_lane = "deepseek.com" in LLM_BASE_URL
```

`systemctl is-active` pulang `active` (autorestart), `py_compile` **OK**, tetapi:

```
$ curl -s http://<REDACTED_IP>:8000/health
(empty)

$ sudo journalctl -u luma-worker -n 8 --no-pager
worker_daemon.py", line 47, in <module>
    _is_deepseek_lane = "deepseek.com" in LLM_BASE_URL
NameError: name 'LLM_BASE_URL' is not defined. Did you mean: 'LLM_API_URL'?
luma-worker.service: Main process exited, code=exited, status=1/FAILURE
```

Fix:
```python
_is_deepseek_lane = "deepseek.com" in os.environ.get("LLM_BASE_URL", "")
```

Selepas fix → `COMPILE_OK` + `active` + `{"status":"healthy"}` +
`/worker/research` → `{"status":"success", ...}` dalam **4.9s**.

### Kenapa gate `thinking` penting

Helper asal hantar `"thinking":{"type":"disabled"}` untuk elak `content` kosong pada DeepSeek
(model reasoning). Di Groq param itu tak dikenali → 400, kemudian retry tanpa param berjaya.
Maknanya setiap call buat 2 request → kuota free 1000 req/hari habis 2x lebih cepat.
Gate ikut host:

```python
if attempt == 0 and _is_deepseek_lane:
    payload["thinking"] = {"type": "disabled"}
```

## 3. Buang watcher `moomoo_ok` (arahan Boss: "padam je")

Kontek: OpenD bind `${OPEND_HOST}:11111` di VPS Tencent. Dari Luma:
```
bridge 8000  -> 200
opend 11111  -> CLOSED
```
Jadi `moomoo_ok: false` adalah **false alarm**, bukan broker mati.

Tapak yang perlu dibuang (7 baris): entry dalam `watchdog_state`, `moomoo_ok = await
check_tcp_port(...)`, `watchdog_state["moomoo_ok"] = ...`, syarat `is_down`, `moomoo={...}`
dalam warning, blok `reasons.append("• Moomoo OpenD Port ...")`, dan key payload `/health`.

Skrip bedah (ringkas):
```python
lines = P.read_text().split("\n")
# loop baris: buang baris tepat; ganti syarat is_down; buang blok if not moomoo_ok + append
assert "moomoo_ok" not in new_text   # baru tulis
subprocess.run([venv_py, "-m", "py_compile", str(P)])
```

Keputusan:
```
dropped lines: 7
PY_COMPILE: OK
active

/health -> status: healthy
           watchdog: {'bridge_ok': True, 'failures': 0}
```

Nota: curl pertama selepas restart pulang **kosong** (uvicorn masih boot). Tunggu 3s, retest —
jangan salah tafsir sebagai crash.

## 4. Quirk model free (gpt-oss-120b)

Query "ringkas IHSG hari ini" pulang:
```json
{"status":"success","query":"ringkas IHSG hari ini",
 "synthesis":"**Maaf, saya tidak dapat membantu dengan permintaan itu.**",
 "execution_time_sec":0.66}
```
Query lain ("ringkas harga emas", "harga minyak sawit") pulang laporan penuh. Jadi penyebabnya
bukan lane mati — model enggan pada prompt tertentu. Guard: semak panjang teks output, retry
dengan rephrasing, atau lapor kepada Boss sebagai had model (bukan kegagalan sistem).
