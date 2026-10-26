---
name: rclone-remote-ops
description: Fix broken rclone backups; pick a durable remote.
version: 1.0.0
---

# rclone Remote Ops (backup/sync yang tahan lama)

Guna bila: backup ke Google Drive gagal, `invalid_grant`, `storageQuotaExceeded`, boss tanya
"kenapa backup asyik mati", atau nak pilih remote yang tak perlu re-auth setiap minggu.

Prinsip: **remote backup mesti lulus UJIAN TULIS, bukan sekadar senarai fail.** Banyak remote
boleh `lsd` (read) tetapi gagal `copy` (write) — dua kebenaran berbeza.

---

## 1. Recon

```bash
rclone listremotes
rclone config show gdrive | grep -vE 'token|client_secret'   # nama remote + type sahaja
rclone lsd gdrive: --timeout 15s                              # ujian BACA
```

## 2. Diagnosa ralat lazim

### `invalid_grant: maybe token expired? try refreshing with "rclone config reconnect"`

Refresh token OAuth dah mati. Punca paling kerap (bukan salah config rclone):

* OAuth consent screen masih dalam mode **"Testing"** → Google matikan refresh token selepas
  **7 hari**. Jadi ia berulang setiap minggu, bukan sekali.
* Client ID dipadam/diubah, atau skop berubah selepas token dikeluarkan.
* Token dicabut (revoke) atau akaun tukar password.

### `403 ... storageQuotaExceeded: Service Accounts do not have storage quota`

Service-account JSON **tidak** menyelesaikan masalah expiry untuk tujuan upload:

* SA boleh **baca** folder My Drive yang di-share kepadanya (list boleh lulus).
* SA **tidak boleh menulis** ke My Drive — Google beri SA 0 kuota storage.
* Hanya jalan bila: (a) target ialah **Shared Drive** (Google Workspace), atau
  (b) domain-wide delegation (Workspace admin), atau (c) target S3/B2/R2 — bukan Drive.
* Ujian pengesahan (1KB sahaja, jangan backup penuh dulu):

```bash
export RCLONE_CONFIG_SATEST_TYPE=drive
export RCLONE_CONFIG_SATEST_SCOPE=drive
export RCLONE_CONFIG_SATEST_SERVICE_ACCOUNT_FILE=/path/sa-key.json
rclone lsd satest: --drive-root-folder-id <FOLDER_ID>     # biasanya LULUS
echo test > /tmp/sa_test.txt
rclone copy /tmp/sa_test.txt satest: --drive-root-folder-id <FOLDER_ID>   # biasanya GAGAL 403
```

## 3. Pilihan remote yang tahan lama (free)

| Pilihan | Kos | Tahan lama? | Nota |
|---|---|---|---|
| Publish OAuth consent screen ke **Production** | free | Ya (refresh token tak expire 7 hari) | Kekalkan setup sedia ada; skop bukan-sensitive (`drive.file`) kurangkan risiko verification |
| **Shared Drive** + service account | free (perlu Workspace) | Ya | SA ada kuota dalam Shared Drive |
| **Cloudflare R2** (10GB) / **Backblaze B2** (10GB) | free tier | Ya | `type = s3`, access key kekal, tiada OAuth |
| Disk lokal (VPS / node worker) | free | Ya | Paling selamat; cloud copy jadi optional |

Rekonek OAuth di mesin **ada browser** (VPS headless tak boleh buka browser):

```bash
rclone authorize "drive"      # di laptop → salin token balik ke config VPS
# atau: rclone config reconnect gdrive:   (di mesin ber-browser)
```

## 4. Verify selepas fix

```bash
rclone copy /tmp/sa_test.txt gdrive:<folder> --timeout 20s   # WAJIB lulus, bukan cuma lsd
rclone check /tmp/sa_test.txt gdrive:<folder>
```
Kemudian jalankan satu kitaran backup sebenar (systemd timer / cron) dan sahkan fail muncul
di remote. Kalau backup dijalankan oleh servis lain (contoh worker jauh), uji endpoint servis itu,
bukan CLI lokal.

---

## Pitfalls

* ❌ Uji `rclone lsd` sahaja, then lapor "backup ok". List ≠ write. Uji `copy` 1KB.
* ❌ Andaikan service-account JSON = "tak expire, mesti boleh tulis". Ia boleh baca, tak boleh tulis
  ke My Drive (403 storageQuotaExceeded).
* ❌ Jalankan `rclone config reconnect` di VPS headless dan tunggu kod keluar. Ia perlu browser —
  guna `rclone authorize` di laptop.
* ❌ Tukar nama remote (`gdrive:` → `gdrive_sa:`) tanpa kemas kini skrip/servis yang merujuknya;
  simpan nama remote stabil, tukar backend di belakangnya.
* ❌ Papar/tampal `client_secret`, token, atau isi SA JSON dalam chat atau log.
* ✅ Bila punca di luar kawalan (perlu Boss klik Consenter screen), daftarkan sebagai owner task
  (`ana_owner_task add ...`) dan beri Boss arahan tepat + kesan jika tak dibuat (backup tak jalan).
