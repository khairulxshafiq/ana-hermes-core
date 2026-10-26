---
name: bursa-malaysia
description: Bursa Malaysia (KLSE) stock market prices, FBM KLCI index, stock search, and financial analytics.
version: 0.1.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Bursa Malaysia, KLSE, Stocks, Trading, Finance, Malaysia, FBMKLCI]
---

# Bursa Malaysia (KLSE) Skill

Skill ini membolehkan Hermes Agent menyemak data pasaran saham Bursa Malaysia (KLSE), indeks FTSE Bursa Malaysia KLCI (^KLSE), harga saham syarikat (seperti Maybank, CIMB, Tenaga, Inari, YTL, Public Bank, dll.), pergerakan harga harian, dan ringkasan pasaran kewangan Malaysia.

## Keupayaan Utama
1. **KLCI Index (`klci`)**: Menyemak status indeks FBM KLCI semasa (patah/point, mata perubahan, trend).
2. **Semakan Saham (`quote <ticker_or_name>`)**: Menyemak harga semasa, julat harian (high/low), jumlah dagangan (volume), dan peratusan pergerakan saham (contoh: `1155` / `MAYBANK`, `1023` / `CIMB`, `5347` / `TENAGA`).
3. **Senarai Saham Utama (`top-stocks`)**: Menyenaraikan harga & prestasi saham-saham utama di Bursa Malaysia.
4. **Sejarah Pergerakan (`chart <ticker> [--range 5d|1mo|6mo|1y]`)**: Memaparkan pergerakan harga bersejarah.

## Penggunaan Script

```bash
# Semak indeks FBM KLCI
python3 skills/bursa_malaysia/bursa_client.py klci

# Semak harga saham Maybank (1155 / MAYBANK)
python3 skills/bursa_malaysia/bursa_client.py quote MAYBANK

# Semak saham CIMB (1023)
python3 skills/bursa_malaysia/bursa_client.py quote 1023

# Semak senarai saham utama Bursa
python3 skills/bursa_malaysia/bursa_client.py top-stocks
```
