---
name: aura-integrations
description: Integrasi penerbitan kandungan Aura (Airtable ${AIRTABLE_TABLE_NAME}, Google Drive Storage, Apify, Firecrawl)
---

# Aura Integrations Skill

Skill ini menyediakan keupayaan penerbitan kandungan automatik dan pengurusan fail khas Aura ke dalam Hermes Agent.

## Keupayaan Utama
1. **Airtable ${AIRTABLE_TABLE_NAME}**: Simpan draf kandungan, kapsyen, tajuk, hashtags, dan pautan media ke Airtable.
2. **Google Drive Storage**: Muat naik gambar dan *article dumps* (.txt) ke Google Drive menggunakan Google Service Account.
3. **Apify Scraper**: Menjalankan scraping data daripada web/sosial media via Apify API.

## Penggunaan Script Utiliti

Semua script diletakkan di dalam folder skill ini dan boleh dipanggil oleh Hermes Agent:

```bash
# Simpan draf ke Airtable
python3 skills/aura_integrations/airtable_publisher.py --title "Tajuk Artikel" --caption "Kapsyen kandungan" --platform "facebook" --brand "Sakluma"

# Muat naik fail ke Google Drive
python3 skills/aura_integrations/gdrive_publisher.py --file "path/to/image.jpg" --mime "image/jpeg"
```
