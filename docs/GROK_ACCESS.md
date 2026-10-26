# GROK ACCESS MAP - Tencent VPS + Luma (GCP)

Dokumen ni untuk agent yang pegang admin selepas ANA. Baca dulu sebelum buat apa-apa.

## 1. HOST INI (otak + tangan)
- IP publik: <REDACTED_IP> | Port 22 | User: ubuntu (sudo OK, password auth OFF)
- Tailscale IP: ${TENCENT_TAILSCALE_IP}
- OS: Ubuntu 24.04, 2 vCPU, 1.9GB RAM, swap 1.9GB, disk 40GB (16GB free)
- Docker: aktif (perlu sudo untuk CLI)

## 2. SERVIS
- hermes-gateway : systemctl --user (reload guna USR1, JANGAN restart sembarangan)
- tanair-bridge, airtable-webhook, agy-memory-tunnel, airtable-webhook-tunnel : systemd system
- Hermes dokumen: ${HERMES_HOME} (config.yaml, state.db, skills/, memories/)

## 3. LUMA (GCP US) - dari VPS ni je
- SSH: ssh khairulshafiq@<REDACTED_IP> (Tailscale) atau alias: ssh agy
- API: http://<REDACTED_IP>:8000 (health, /worker/research, /worker/parse-doc, /worker/scrape-viral)
- Servis: luma-worker.service (sudo systemctl restart luma-worker)
- Kod: /home/khairulshafiq/antigravity-workspace/luma_worker/
- Env: /home/khairulshafiq/antigravity-workspace/.env (LLM_API_KEY/LLM_BASE_URL/LLM_MODEL -> Groq free)
- Spesifikasi: 953MB RAM, disk 28GB (17GB free). JANGAN jalankan Whisper atau render video di sini.
- Key ana-grokbot dah dimasukkan ke authorized_keys Luma (no-forwarding).

## 4. FAIL PENTING
- Kredensial: ${HERMES_HOME}/.env (37 kunci - JANGAN print, JANGAN commit)
- Identiti + memori: ${HERMES_HOME}/memories/{MEMORY.md,USER.md}
- Projek + status: /home/ubuntu/AnaFile/{STATUS.md,DIRECTION.md,OWNER_TASKS.md}
- Handover penuh: /home/ubuntu/ana-handover (git repo) + ana-handover-repo-2026-10-25.tar.gz
- Skrip kerja: /home/ubuntu/scripts (88 fail; blogger, social_publisher, luma client, telegram buttons)
- Blog: /home/ubuntu/AnaFile/blog/*.md -> publish guna scripts/ana_blogger_publish.py

## 5. PERATURAN (jangan langgar)
1. Backup fail (.bak.TARIKH) sebelum edit apa-apa config/kod.
2. Selepas edit Python: python3 -m py_compile <fail>.
3. JANGAN sentuh GEMINI_API_KEY / GEMINI_API_KEY_PAID - itu satu-satunya lane image generation.
4. JANGAN print nilai rahsia ke log/Telegram.
6. Gateway reload: systemctl --user reload hermes-gateway (bukan restart) supaya sesi tak putus.

## 6. MASALAH YANG MASIH TERBUKA (25 Okt 2026)
- FB Page token mati (OAuthException 190) - perlu long-lived token baru (owner task #30)
- rclone gdrive: invalid_grant - OAuth app mode Testing; SA JSON tak boleh upload (storageQuotaExceeded)
- OpenRouter key mati (401 User not found). BytePlus quota habis sampai 29 Okt 2026.
- hermes-webui inactive (bukan kritikal)
- Whisper: guna Groq whisper-large-v3-turbo (percuma). JANGAN bina whisper.cpp di VPS 2GB.

- 26 Okt 2026: Hardening Hermes siap (allowlist ketat, destructive_slash_confirm=true, token na_*.sh pindah ke .env, state.db 600). Lihat ~/HARDENING_LOG.md

## 7. AKSES YANG DIBERI
- Key SSH: ana-grokbot (ed25519) - tiada port/agent forwarding
- Fingerprint: SHA256:V9hphVmoaAyLdv++M+5KVYUgDBhX+fuqqgDel21fu+E
- Tarik balik: sed -i '/ana-grokbot/d' ~/.ssh/authorized_keys (VPS) dan sama di Luma
