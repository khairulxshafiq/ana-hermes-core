---
name: luma-worker
description: Dispatch intensive research, viral news scraping, document parsing, and database vault backups to the dedicated GCP Cloud Analytical & Storage Worker Fleet (luma-us at <REDACTED_IP>:8000).
---

# Luma Worker Fleet Integration (4 Engines A-B-C-D)

GCP Node `luma-us` (`<REDACTED_IP>:8000`) acts as ANA's dedicated heavy background worker over Tailscale WireGuard mesh.

## The 4 Core Supporting Engines:
1. **Engine A: Watchdog Alerter** – Pings Tencent Bridge every 5 mins. Dispatches Telegram alerts to Boss (${TELEGRAM_HOME_CHAT_ID}) on failure.
2. **Engine B: G-Vault Backup** – Daily automated SQLite backup (04:00 AM MYT) to Google Drive with 7-day retention.
3. **Engine C: Viral News Scraper** – Real-time scraping of Bursa Malaysia, Bernama, and Google News Malaysia with pandas scoring.
4. **Engine D: Heavy Doc Parser** – Extracts and synthesizes PDF/Excel documents via `pypdf` / `openpyxl` to spare Tencent RAM.

## CLI Usage (from Tencent ANA):
```bash
# 1. Health & Watchdog Check
python3 ~/.hermes/skills/gcp_worker_client.py health
python3 ~/.hermes/skills/gcp_worker_client.py watchdog

# 2. Scrape Viral & Trending News (Bursa, Bernama, Business)
python3 ~/.hermes/skills/gcp_worker_client.py viral --limit 5

# 3. Parse Heavy Documents (PDF / Excel)
python3 ~/.hermes/skills/gcp_worker_client.py parse --file /tmp/financial_report.pdf

# 4. Trigger G-Vault SQLite Backup
python3 ~/.hermes/skills/gcp_worker_client.py backup

# 5. Offload Deep Research
python3 ~/.hermes/skills/gcp_worker_client.py research "Analisis pasaran tenaga hijau Malaysia" --depth deep
```
