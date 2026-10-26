# Blogger Publishing Pipeline (VPS Tanair) — 25 Okt 2026

Rekod pipeline sebenar pada mesin ini. Guna bersama `google-oauth-tokens` §3b/§5.

## Aset & laluan

| Item | Nilai |
|---|---|
| Token OAuth | `~/.hermes/google_token.json` (scopes: `blogger`, `drive`) |
| Blog utama | `tanair` → ID `<REDACTED_ID>` (Tanair AI Explorer, ex-auraone) |
| Blog kedua | `anaberahi` / alias `sakluma` → ID `<REDACTED_ID>` |
| Helper API asal | `~/scripts/blogger_api.py` (guna `google-auth`; `/usr/bin/python3` ada libs, `python3` shell mungkin tiada) |
| Queue publisher | `~/scripts/blogger_queue_publish.py` — queue `~/Blogspot/blog_queue/queue.json`, maks 1 post/run ikut `publish_date` |
| Wrapper + gate | `~/scripts/run_blogger_publish.sh` — perlukan `~/.hermes/publish_gate.json` = `{"blogger":"OPEN"}`; kalau tiada/CLOSED ia SKIP dengan log |
| Helper baru (25 Okt) | `~/scripts/ana_blogger_auth.py`, `~/scripts/ana_blogger_publish.py` |
| Draf artikel | `~/AnaFile/blog/<slug>.md` + `<slug>.html` (HTML dijana dari MD) |

Blogger API: `POST https://www.googleapis.com/blogger/v3/blogs/{blogId}/posts/` (+`?isDraft=true`
untuk draf). Response mesti ada `status: LIVE`, `url`, `id`.

## Publish satu-perintah (selepas token hidup)

```bash
/usr/bin/python3 ~/scripts/ana_blogger_publish.py ~/AnaFile/blog/<slug>.md \
  --labels "AI,Automasi,Kos AI"
# tambah --draft untuk semak dulu sebelum LIVE
```

`ana_blogger_publish.py` refresh token via HTTP (tak perlu `google-auth`), guna `<slug>.html`
kalau wujud, ambil tajuk dari baris `# ` pertama, kemudian cetak `PUBLISHED status=… URL: …`.

## Gate & kebenaran

* Publish ke blog = tindakan luaran awam. Jalankan hanya bila Boss beri arahan eksplisit
  ("hantar ke blogger terus"), bukan atas inisiatif sendiri.
* Laluan queue (`run_blogger_publish.sh`) ada Owner Publish Gate; laluan manual
  `ana_blogger_publish.py` tiada gate — jadi disiplin pada arahan Boss.
* Selepas publish, bagi Boss `url` hidup + tajuk, bukan ringkasan sahaja.

## Markdown → HTML (tanpa dependency)

Modul `markdown` tak disahkan ada pada semua python. Converter minimum yang cukup untuk artikel
blog: `# / ## / ###` → `h1/h2/h3`, `- ` atau `• ` → `ul/li`, `---` → `hr`, `**x**` → `strong`,
`*x*` → `em`, `` `x` `` → `code`, baris lain → `p`.

## Kes 25 Okt 2026 (status)

* Artikel "Satu Malam Aku Buang Tiga API" siap: 537 patah perkataan, HTML 3.5KB.
* Publish **BLOCKED**: refresh `google_token.json` pulang
  `400 invalid_grant — Token has been expired or revoked` (app `<REDACTED_ID>` masih Testing).
* Tindakan: artis + HTML + skrip auth/publish disiapkan; auth URL loopback (`localhost:53682`)
  dihantar kepada Boss; selepas publish app + code exchange, publish jadi satu langkah.
* Pengajaran: siapkan semua artefak sebelum minta Boss authorize — jangan biar beliau tunggu
  untuk kerja yang boleh disiapkan lebih awal.
