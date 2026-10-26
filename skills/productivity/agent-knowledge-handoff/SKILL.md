---
name: agent-knowledge-handoff
description: Export agent memory/skills into a portable migration bundle.
version: 1.0.0
---

# Agent Knowledge Handoff (pindah otak, bukan tangan)

Use when Boss says: "aku nak tinggal Hermes / VPS ni", "nak pindah ke Grok / bot lain",
"export memory & skills kau", "buat bundle untuk migrate", atau bila dia tanya apa yang
tinggal kalau platform ditukar.

Kerja ni menyentuh identiti, memori, dan kredensial. Janji palsu di sini lebih bahaya
daripada kegagalan teknikal — Boss mungkin akan matikan VPS berdasarkan apa yang kau cakap.

---

## 0. Jujur dulu: aset mana yang boleh pindah

Set jangkaan SEBELUM bina apa-apa. Jangan sekali-kali janji pariti keupayaan.

| Boleh pindah (otak) | Tak boleh pindah (tangan) |
|---|---|
| Identiti, tone, dasar bahasa | Shell / terminal / SSH |
| Memori fakta + profil pengguna | Cron, watchdog, jadual backup |
| Playbook (skill sebagai arahan) | Filesystem kekal |
| Inventori projek, ID, URL, IP | Skrip kerja (`~/scripts/*.py`) |
| Checklist kredensial (nama sahaja) | Gateway Telegram/Discord sendiri |
| Log keputusan | Swarm workers / kanban / n8n |

Chatbot platform (Grok, Claude app, ChatGPT) = **penasihat pandai**, bukan pekerja.
Kalau Boss perlukan automasi, cadang **hibrid**: otak baharu + VPS lama kekal sebagai tangan.
Itu biasanya lebih murah daripada membina semula semuanya.

---

## 1. Inventori dulu (angka sebenar, bukan agakan)

```bash
ls -la ~/.hermes/memories/                      # MEMORY.md, USER.md, long_term_facts.json
find ~/.hermes/skills -name SKILL.md | wc -l    # bilangan skill
du -sh ~/.hermes/skills ~/AnaFile
ls -lh ~/.hermes/state.db ~/.hermes/kanban.db   # sejarah sesi (SQLite)
ls ~/scripts/*.py | wc -l
systemctl --user list-units --type=service --no-legend | head
```

Lapor angka betul kepada Boss (contoh: "166 SKILL.md, 16MB, state.db 11MB, 90 skrip").
Angka inilah yang meyakinkan dia bundle tu lengkap — bukan ayat "semua dah ada".

---

## 2. Struktur bundle (guna susunan bernombor supaya jelas urutan baca)

```
MIGRATION/
  00_README.md                  apa ini, struktur, had penting
  01_IDENTITY.md                siapa agent, tone, bahasa, prinsip, sempadan
  02_<USER>_PROFILE.md          salinan USER.md
  03_MEMORY_FACTS.md            salinan MEMORY.md + long_term_facts.json
  04_PROJECTS_ASSETS.md         produk, jenama, blog/sheet ID, IP, laluan arkib
  05_RUNBOOK.md                 servis, port, endpoint, jadual cron
  06_CREDENTIALS_CHECKLIST.md   NAMA kunci + panjang + di mana nak dapat semula
  07_SKILLS_INDEX.md            indeks penuh + senarai skill terpilih
  08_IMPORT_GUIDE.md            langkah masuk ke platform sasaran
  skills_selected/              ~15-25 skill disalin penuh (bukan 166)
```

Peraturan keras: `06` **tidak boleh** mengandungi nilai kunci. Nama + panjang + sumber
penerbitan sahaja. Bundle ni akan berpindah tempat — anggap ia akan bocor.

---

## 3. Bina bundle dengan skrip, bukan tulis manual

Jalankan `scripts/export_agent_bundle.py` (dalam skill ni) — ia kumpul memori, indeks skill,
nama kunci env (tanpa nilai), unit systemd, kemudian `tar.gz`.

Kalau perlu tulis dokumen panjang secara manual, **jangan** harap `write_file` untuk teks
beribu aksara: ia boleh terpotong senyap dan menulis literal `…[truncated]`. Bina string
dalam `execute_code` dan `Path(...).write_text(...)`, atau pecah kepada `p1.md`, `p2.md`,
kemudian `cat p*.md > final.md`. Sahkan dengan `wc -w -l` + baca 5 baris pertama.

Selepas siap: `tar -czf ~/AnaFile/ana_portable_bundle_<tarikh>.tar.gz -C ~/AnaFile MIGRATION`
kemudian hantar kepada Boss sebagai `MEDIA:/laluan/bundle.tar.gz` — bundle 400-500KB cukup
untuk dihantar terus dalam chat.

---

## 4. Peta import ke platform sasaran (contoh Grok / chatbot)

| Kandungan bundle | Tempat masuk |
|---|---|
| `01_IDENTITY.md` | Custom Instructions / About me / system prompt |
| `02`, `03` | Memori — **satu fakta satu entri**, bukan satu blok panjang |
| `04`, `05`, `06` | Fail projek / knowledge upload |
| `skills_selected/*` | Playbook sebagai "cara kerja aku" dalam arahan atau fail rujukan |
| `07` | Rujukan sahaja (jangan upload 166 fail) |

Had aksara custom instructions biasanya ketat: mampatkan identiti kepada
*identiti + tone + bahasa + 5 prinsip kerja*. Selebihnya masuk memori/fail.

---

## 5. Verifikasi (recall test, bukan "dah upload")

Tanya platform sasaran 5 soalan fakta yang ada dalam bundle, contoh:
blog ID, nama jenama, peraturan bahasa, IP nod pekerja, lane LLM semasa.

Jawapan salah = fakta itu belum masuk. Ulang langkah 2/4 untuk fakta tersebut.
Tanpa ujian ini, "migrasi selesai" cuma andaian.

---

## 6. Checklist decommission (urutan wajib)

1. Export bundle + salinan pangkalan data (`state.db`, `kanban.db`).
2. Sahkan import dalam platform baharu (recall test lulus).
3. Bekukan cron / jadual automatik (`cronjob action=pause` atau `crontab -e`).
4. Revoke kunci API yang tak dipakai lagi (satu-satu, rekod tarikh).
5. Snapshot disk VPS sebelum terminate (image atau `tar` ke storan luar).
6. Baru batalkan langganan VPS / GCP.
7. Simpan satu salinan bundle di luar kedua-dua platform.

Jangan padam sumber sebelum langkah 2 lulus — kalau import gagal, Boss tiada jalan balik.

---

## Pitfalls

* ❌ Janji "boleh migrate semua". Tangan (shell/cron/skrip) tidak ikut — sebut awal.
* ❌ Masukkan nilai kunci ke dalam bundle. Nama + di mana nak dapat semula sahaja.
* ❌ Salin 166 skill bulat-bulat. Curate ~15-25 yang benar-benar digunakan (rujuk
  `skills/.usage.json`) + yang khusus untuk bisnes Boss.
* ❌ Tulis dokumen panjang dengan satu `write_file` — risiko truncation senyap.
* ❌ Anggap platform sasaran boleh jalankan playbook. Skill Hermes banyak bergantung pada
  tool tempatan; tulis semula sebagai arahan bahasa manusia.
* ❌ Hantar bundle sebelum verify isi (`head`/`wc`) — bundle kosong nampak sama seperti bundle penuh.
* ❌ Lupa rekod dalam `STATUS.md` + `OWNER_TASKS.md` (contoh: "Boss pertimbang migrasi ke X,
  bundle siap <tarikh>, tunggu keputusan").
* ✅ Cadang hibrid (otak baharu + VPS lama) sebagai pilihan default — ia menyelesaikan 80%
  keperluan tanpa kehilangan automasi.
