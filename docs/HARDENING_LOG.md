# Hermes hardening log

## 2026-10-26 21:52 MYT (Grok Bot)
- ~/.hermes/config.yaml (backup config.yaml.bak.20261026_215230):
  - command_allowlist: removed tirith:curl_pipe_shell, tirith:schemeless_to_sink (no use found in logs)
  - approvals.destructive_slash_confirm: false -> true (asks yes/no for /new /reset /undo only)
  - gateway reloaded (USR1), still active
  - Rollback: cp -p ~/.hermes/config.yaml.bak.20261026_215230 ~/.hermes/config.yaml && systemctl --user reload hermes-gateway
- ~/scripts/na_e2e4.sh, na_fixgroup.sh: hardcoded new-api tokens moved to ~/.hermes/.env as NEWAPI_LOCAL_TOKEN, NEWAPI_LOCAL_SK; scripts now source .env; removed from .gitignore; commit a5c6430
  - Backups: ~/scripts/na_*.sh.bak.20261026_215407, ~/.hermes/.env.bak.20261026_215407, ~/scripts/.gitignore.bak.*
  - Rollback: cd ~/scripts && git revert a5c6430; restore .bak files
- chmod 644 -> 600: ~/.hermes/state.db, state.db-shm, state.db-wal (dir already 700; auth.json/google_token.json already 600)
  - Rollback: chmod 644 ~/.hermes/state.db*
Mon Oct 26 22:01:14 CST 2026 TELEGRAM_HOME_CHANNEL added to .env (gateway/config.py reads YAML raw so ${TELEGRAM_HOME_CHAT_ID} never expanded). Rollback: cp -p ~/.hermes/.env.bak.20261026_220114 ~/.hermes/.env
