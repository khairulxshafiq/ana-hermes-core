# Google Drive + rclone: `invalid_grant` dan had service account (25 Okt 2026)

Konteks: sandaran G-Vault dari VPS Tencent / node Luma ke Google Drive Boss gagal, dan
Boss mahu ia **auto tanpa isu berulang**.

## Config rclone sebenar (masked)

```
[gdrive]
type = drive
client_id = <len 72> 317795779844...
client_secret = <len 35> GOCSPX-...
scope = drive
root_folder_id = 1Huq51lGPWTrB3bBOE_6bzJm9GGzLSTPy
token = <len 482>
team_drive =
```

`client_id` milik Boss sendiri (bukan client default rclone) → consent screen projek
`<REDACTED_ID>` itulah yang menentukan hayat refresh token.

## Gejala

```
rclone lsd gdrive:
ERROR : couldn't fetch token: invalid_grant: maybe token expired?
        - try refreshing with "rclone config reconnect gdrive:"
```

## Ujian service account JSON (hipotesis "guna JSON je, free")

Kunci SA sedia ada: `~/.config/tanair-n8n-sa-key.json` (`tanair-n8n-sa@…`).

```bash
export RCLONE_CONFIG_SADRIVE_TYPE=drive
export RCLONE_CONFIG_SADRIVE_SCOPE=drive
export RCLONE_CONFIG_SADRIVE_SERVICE_ACCOUNT_FILE=~/.config/tanair-n8n-sa-key.json
rclone lsd sadrive: --drive-root-folder-id 1Huq51lGPWTrB3bBOE_6bzJm9GGzLSTPy
```

Baca → **BERJAYA** (folder `01_Piko_&_Bojo`, `AnaFile_gen`, `Aura_gen`, … tersenarai).

Tulis → **GAGAL**:

```
Failed to copy: googleapi: Error 403: Service Accounts do not have storage quota.
Leverage shared drives, or use OAuth delegation instead.
storageQuotaExceeded
```

Kesimpulan: SA sesuai untuk **baca** (dan untuk Sheets/API yang tak makan kuota Drive),
tidak sesuai untuk **upload backup** ke My Drive.

## Punca & fix yang diberitahu kepada Owner

Refresh token luput 7 hari sebab OAuth consent screen `External` + status `Testing`.

Langkah yang disediakan untuk Boss (belum selesai dalam sesi ini — status PENDING):
1. `console.cloud.google.com/apis/credentials/consent?project=<REDACTED_ID>`
2. **PUBLISH APP** → Confirm → status jadi **In production**
3. `rclone config reconnect gdrive:` di mesin ada browser
4. Amaran "unverified app" → Advanced → Go to rclone (unsafe) → Allow
5. `rclone lsd gdrive:` tanpa error
6. Kalau Workspace: tukar User Type → `Internal` (tiada verification)

Alternatif yang dicadangkan serentak: Cloudflare R2 (10GB free, S3 token kekal),
Backupblaze B2, atau backup lokal VPS+Luma sahaja.

## Lesson

* `rclone lsd` berjaya ≠ backup jalan; kena uji `copy` + `delete` juga.
* Jangan lapor backup automatik pulih selagi consent screen masih `Testing`; daftar sebagai
  owner task PENDING.
