---
name: cloud-backup-auth
description: Fix expiring cloud backup auth (rclone, Drive, S3, SA JSON).
version: 1.0.0
---

# Cloud Backup Auth (kredensial sandaran yang tak expire)

Guna bila: backup/sync gagal dengan `invalid_grant`, `storageQuotaExceeded`, `401`,
"token expired", atau bila Boss minta backup **auto setiap hari tanpa perlu login semula**.
Juga guna bila memilih destinasi sandaran (Google Drive / R2 / B2 / lokal) untuk node VPS + GCP.

Prinsip: **auth yang mati setiap 7 hari bukan automasi** — ia kerja manual berulang.
Sebelum cadang penyelesaian, kenal pasti *jenis* kredensial dan had sebenar setiap satu.

---

## 0. Recon dulu (jangan re-auth buta)

```bash
rclone listremotes
python3 - <<'PY'
import pathlib
p = pathlib.Path.home() / ".config/rclone/rclone.conf"
for line in p.read_text().splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if any(s in k for s in ("token", "client_secret", "client_id")):
            print(f"{k} = <len {len(v)}> {v[:12]}...")   # JANGAN print nilai penuh
        else:
            print(f"{k} = {v}")
    else:
        print(line)
PY
rclone lsd <remote>: --timeout 15s      # ini yang dedah invalid_grant
```

Yang penting dicatat dari config: `type`, `client_id`, `scope`, `root_folder_id`, `team_drive`,
dan sama ada `token` ada. Kalau `client_id` milik Boss (bukan client rclone default) → consent
screen projek itulah yang perlu di-publish.

Semak juga status servis & Docker bila backup bergantung padanya:
`systemctl is-active docker`, `ss -tlnp | grep <port>`, `docker ps` (mungkin perlu `sudo`).

---

## 1. Tiga jenis kredensial — had sebenar (disahkan 25 Okt 2026)

| Jenis | Expire? | Boleh TULIS? | Nota |
|---|---|---|---|
| OAuth user token (rclone `gdrive`) | **Ya, 7 hari** bila consent screen `Testing` | Ya | Punca `invalid_grant` berulang |
| Service account JSON | Tidak | **Tidak** untuk My Drive | `403 storageQuotaExceeded` — SA tiada kuota |
| S3-compatible token (R2/B2) | Tidak | Ya | Paling "set and forget" |

Fakta yang diuji pada sesi sebenar:
* SA boleh **senarai** folder yang dikongsi dengan email SA (`rclone lsd` berjaya).
* SA **gagal upload**:
  `403 Service Accounts do not have storage quota … storageQuotaExceeded`.
  Jadi "guna JSON je" bukan penyelesaian untuk backup, kecuali ke **Shared Drive** (Workspace)
  atau dengan domain-wide delegation.
* OAuth `invalid_grant: maybe token expired?` **bukan** sebab kunci API dipadam dan bukan
  sebab projek dimatikan — ia token refresh yang dah mati.

---

## 2. Punca sebenar refresh token mati setiap 7 hari

Google: projek dengan OAuth consent screen jenis **External** + publishing status **Testing**
dapat refresh token yang luput **7 hari**. Selagi status kekal `Testing`, masalah berulang
walaupun kau reconnect berkali-kali.

### Fix (percuma, kekal) — publish consent screen

1. Buka `console.cloud.google.com/apis/credentials/consent?project=<PROJECT_ID>`
   (PROJECT_ID = awalan `client_id`, contoh `<REDACTED_ID>`).
2. Lihat **Publishing status**. Kalau `Testing` → tekan **PUBLISH APP** → **Confirm**.
3. Sahkan status jadi **In production**.
4. Buat token baru (token lama memang mati, tak boleh diselamatkan):
   ```bash
   rclone config reconnect <remote>:
   ```
5. Browser akan tunjuk "Google hasn't verified this app" → **Advanced** → **Go to … (unsafe)**
   → Allow. Amaran ni normal; app unverified masih berfungsi, refresh token tak expire.
6. Sahkan: `rclone lsd <remote>:` keluar senarai tanpa error.

Kalau akaun itu **Google Workspace** (domain sendiri), lebih baik: tukar **User Type** dari
`External` ke **`Internal`** → tiada verification langsung, token kekal.

Nota skop: scope `drive` (restricted) boleh mencetuskan keperluan verification untuk app
*verified/public*. Untuk penggunaan sendiri, app unverified + `In production` sudah memadai.

---

## 3. Alternatif bila Owner tak mahu sentuh konsol Google

Cadang dengan implikasi, bukan senyap:

* **Cloudflare R2** — 10GB free, S3-compatible, token API kekal. `rclone config` → `type = s3`,
  provider `Cloudflare`, endpoint `https://<account>.r2.cloudflarestorage.com`.
* **Backblaze B2** — 10GB free, application key kekal.
* **Lokal** (VPS + node GCP) — `rsync`/`rclone` ke disk sendiri; zero token, tapi tiada offsite.
* **SA JSON + Shared Drive** — hanya kalau ada Workspace dan shared drive disediakan.

Guna HITL one-tap buttons bila menawarkan pilihan ini:
`python3 /home/ubuntu/scripts/tg_survey_buttons.py --chat-id <id> --question "..." --options "A|B|C"`

---

## 4. Verify selepas fix

```bash
rclone lsd <remote>:                    # senarai root
rclone copy /tmp/probe.txt <remote>:/   # tulis sebenar, bukan cuma baca
rclone delete <remote>:/probe.txt       # bersihkan
```

Untuk backup berjadual: uji endpoint servis (`/worker/backup`, cron job) dan baca output sebenar;
jangan tanda "selesai" berdasarkan config sahaja. Kalau token masih `Testing`, tulis dalam
`OWNER_TASKS.md` sebagai PENDING — jangan lapor backup automatik sudah pulih.

---

## Pitfalls

* ❌ Anggap service account JSON = penyelesaian sejagat. Ia boleh baca tapi **tak boleh tulis**
  ke My Drive (`storageQuotaExceeded`).
* ❌ Reconnect rclone berulang kali tanpa publish consent screen — token mati lagi 7 hari.
* ❌ Cetak `token` / `client_secret` penuh ke log atau chat. Cetak panjang + 12 aksara awal sahaja.
* ❌ Tanda backup pulih sebab `rclone lsd` berjaya — `lsd` hanya bukti scope baca.
* ❌ Lapor "semua settle" bila fix memerlukan klik Owner di konsol. Daftarkan dalam
  `~/AnaFile/OWNER_TASKS.md` dengan sebab dan di mana.

## Support files
* `references/google-drive-rclone-2026-10.md` — transkrip kes: `invalid_grant`, ujian SA
  (list OK / upload 403), config rclone sebenar (masked), dan langkah publish yang disediakan
  untuk Owner.
