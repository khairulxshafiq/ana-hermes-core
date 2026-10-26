---
name: google-oauth-tokens
description: Fix Google OAuth invalid_grant; re-auth headless.
version: 1.0.0
---

# Google OAuth Tokens (Drive / Blogger / Sheets / Gmail)

Use when: `invalid_grant`, `Token has been expired or revoked`, refresh token mati berulang,
rclone gagal list/upload ke Drive, Blogger API tak boleh post, atau bila perlu authorize Google
API dari **server tanpa browser**. Juga bila mempertimbangkan service-account JSON untuk backup.

Kerja ni sentuh token production + boleh memutuskan akses Boss ke Drive/blog. Diagnosa dulu,
jangan terus minta Boss authorize berulang — punca biasanya sama setiap kali.

---

## 1. Diagnosa: bezakan tiga punca `invalid_grant`

Jangan andaikan "token expired" = kena reconnect. Tiga punca berbeza, fix berbeza:

| Gejala | Punca sebenar | Fix |
|---|---|---|
| `invalid_grant` berulang **setiap ~7 hari** | OAuth consent screen masih **Testing** → Google hadkan refresh token 7 hari | Publish app (§2). Reconnect sahaja tak selesaikan |
| `invalid_grant` sekali selepas lama tak guna / tukar password / revoke | Refresh token dibuang | Reconnect (§3) |
| `403 storageQuotaExceeded` semasa upload | Guna **service account** untuk tulis ke My Drive | SA tiada kuota Drive. Guna OAuth user, Shared Drive, atau R2/B2 (§4) |

Sahkan punca #1 dengan membaca `client_id` dalam token/rclone conf:

```bash
grep -h 'client_id' ~/.config/rclone/rclone.conf ~/.hermes/google_token.json 2>/dev/null | cut -c1-60
# status app: console.cloud.google.com/apis/credentials/consent?project=<project-number>
```

`client_id` berbentuk `<project-number>-<hash>.apps.googleusercontent.com` → nombor depan itu
project yang consent screen-nya perlu diperiksa. **Satu client sering dikongsi** oleh rclone,
token Blogger, dan backup — jadi satu fix publish menyelesaikan semua servis serentak.
Semak scope dalam fail token: kalau ada `blogger` + `drive`, memang satu token serve dua kerja.

---

## 2. Publish OAuth app (fix kekal, percuma)

1. Buka `https://console.cloud.google.com/apis/credentials/consent?project=<PROJECT_NUMBER>`
2. Lihat **Publishing status**. Kalau `Testing` → itu punca.
3. Tekan **PUBLISH APP** → **Confirm** → status mesti jadi **In production**.
4. App unverified masih boleh guna: skrin amaran "Google hasn't verified this app" → **Advanced**
   → **Go to <app> (unsafe)** → Allow. Refresh token jadi kekal; verification tak perlu untuk
   kegunaan sendiri.
5. Kalau akaun Google Workspace (domain sendiri): tukar **User Type** `External` → **Internal`
   (tiada verification langsung).

Publish app **tidak** menghidupkan token lama — token yang dah mati mesti dibuat semula (§3).

---

## 3. Re-auth dari server tanpa browser

### 3a. rclone (ada browser di laptop Boss)

```bash
rclone config reconnect gdrive:
```
Ikut arahan, approve, kemudian sahkan `rclone lsd gdrive:` keluar senarai tanpa error.

### 3b. Scope bukan-rclone (contoh Blogger) — manual code extraction

Server tiada browser, jadi guna loopback redirect dan salin `code` dari URL:

1. Bina auth URL (client_id/secret diambil dari fail token sedia ada supaya redirect URI kekal
   sama dengan yang didaftarkan):

```python
import urllib.parse, json
tok = json.load(open('${HERMES_HOME}/google_token.json'))
print('https://accounts.google.com/o/oauth2/auth?' + urllib.parse.urlencode({
    'client_id': tok['client_id'], 'redirect_uri': 'http://localhost:53682/',
    'response_type': 'code', 'scope': 'https://www.googleapis.com/auth/blogger',
    'access_type': 'offline', 'prompt': 'consent'}))
```

2. Boss buka URL → Allow → browser cuba buka `localhost:53682` dan gagal (**normal**).
3. Boss salin URL penuh dari address bar (`http://localhost:53682/?state=&code=4/0A...`) dan
   hantar balik.
4. Tukar code → refresh token, tulis semula fail token (kekalkan `client_id`/`client_secret`):

```python
data = urllib.parse.urlencode({'client_id': tok['client_id'], 'client_secret': tok['client_secret'],
    'code': code, 'grant_type': 'authorization_code',
    'redirect_uri': 'http://localhost:53682/'}).encode()
```

Ready-made: `~/scripts/ana_blogger_auth.py "<redirect_url_dengan_code>"` (Blogger scope).
`prompt=consent` wajib, kalau tidak Google tak pulang `refresh_token` baharu.

### 3c. Refresh tanpa library Google

`google-auth` mungkin tiada pada python sistem. Refresh terus via HTTP, tak perlu dependency:

```
POST https://oauth2.googleapis.com/token
  client_id, client_secret, refresh_token, grant_type=refresh_token
```
Bezakan `400 invalid_grant` (token mati) dari `400 invalid_client` (client_id/secret salah)
sebelum lapor Boss.

---

## 4. Service account JSON: boleh baca, tak boleh tulis

Service account **tiada kuota storage Drive** (dasar Google). Disahkan 25 Okt 2026 pada folder
yang memang di-share dengan SA:

```bash
RCLONE_CONFIG_SADRIVE_TYPE=drive RCLONE_CONFIG_SADRIVE_SCOPE=drive \
RCLONE_CONFIG_SADRIVE_SERVICE_ACCOUNT_FILE=/path/sa.json \
rclone lsd sadrive: --drive-root-folder-id <FOLDER_ID>     # ✅ boleh list
# rclone copy fail kecil ke folder itu → ❌ 403 storageQuotaExceeded
```

Jadi SA sesuai untuk **Sheets API / baca folder**, tidak untuk backup upload ke My Drive.
Pilihan untuk backup auto yang tak expire:
1. **Publish OAuth app** + refresh token user (§2) — paling murah, guna setup sedia ada
2. **Cloudflare R2 / Backblaze B2** (S3-compatible, token API tak expire, free tier ~10GB)
3. **Shared Drive** (Workspace) + SA, kalau ada
4. Backup lokal (disk nod lain) sebagai fallback terakhir

Jangan cadangkan "guna JSON SA" sebagai penyelesaian `invalid_grant` tanpa uji upload dahulu —
ia gagal pada langkah tulis, bukan pada langkah auth.

---

## 5. Verifikasi (jangan lapor "settle" tanpa bukti)

1. Refresh manual → mesti pulang `access_token` (bukan ralat).
2. Panggil endpoint sebenar yang Boss guna: `rclone lsd gdrive:` / `GET blogger/v3/users/self/blogs`
   / post draft.
3. Selepas publish app: sahkan status **In production** dan refresh token baharu disimpan
   (pastikan `refresh_token` hadir dalam fail token).
4. Rekod dalam `STATUS.md`: client_id/project, status app, tarikh re-auth, servis mana guna.

---

## Pitfalls

* ❌ Reconnect berulang tanpa semak **Publishing status** — token akan mati lagi dalam 7 hari.
  Diagnosa punca dulu (§1), reconnect kemudian.
* ❌ Anggap token rclone dan token Blogger berasingan. Selalunya satu `client_id`, satu project,
  satu status app — satu fix untuk semua, satu luput untuk semua.
* ❌ Salin `client_id` baharu semasa re-auth. Redirect URI mesti didaftar pada client yang sama;
  tukar client = `redirect_uri_mismatch`.
* ❌ Lupa `prompt=consent` + `access_type=offline` → tiada `refresh_token` dalam response.
* ❌ Sesetengah tool menolak command yang mengandungi `python3 -c "..."` (guard baca skrip yang
  dirujuk lalu gagal `embedded null byte`). Jalankan kod melalui `execute_code`/`subprocess` atau
  letak dalam fail `.py` dahulu — jangan ulang command yang sama.
* ❌ Lapor "blog dah publish" sebelum dapat `url` + `id` post dari API. Kalau auth gagal, beritahu
  Boss ia **blocked**, dan siapkan semua artefak (HTML, skrip, auth URL) supaya publish jadi satu
  langkah bila token hidup.
* ❌ Abaikan fail besar semasa menulis artikel/aset: `write_file` boleh terpotong senyap dan
  menulis literal `…[truncated]` ke dalam fail. Sahkan `bytes_written` vs saiz jangkaan; kalau
  terpotong, tulis dalam beberapa bahagian (`p1.md`, `p2.md`, …) kemudian `cat p*.md > final.md`.
* ✅ Sentiasa `wc -w -l` fail artikel selepas tulis dan baca 5 baris pertama — dua check ini
  menangkap truncation serta-merta.

---

## Support files
* `references/blogger-publishing-tanair.md` — pipeline Blogger sebenar pada VPS ini: lokasi token,
  blog ID, skrip queue/publish, publish gate, dan langkah publish manual satu-perintah.
