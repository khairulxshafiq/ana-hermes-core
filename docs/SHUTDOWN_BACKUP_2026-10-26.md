# Shutdown backup — 2026-10-26

The Tencent VPS that ran Ana (Hermes Agent) was permanently shut down after this snapshot.
This repo is **PUBLIC**, so only sanitized material is included.

## Included
- personas/ — 6 persona SOULs (Telegram mobile formatting rules added)
- SOUL.md — live ~/.hermes/SOUL.md (IPs/emails/phones/IDs redacted)
- config/config.yaml — live ~/.hermes/config.yaml, secrets & IDs replaced with ${VAR}; hardening applied
  (no tirith curl_pipe_shell / schemeless_to_sink in command_allowlist, approvals.destructive_slash_confirm: true).
  TELEGRAM_HOME_CHANNEL must be set or cron/notification delivery has no target.
- config/config.template.yaml — original template
- .env.example — every key NAME from the live .env, values empty
- skills/ — live ~/.hermes/skills (caches, __pycache__, dotfiles, >5MB files and credential helper scripts excluded; custom skills redacted)
- systemd/ — user units: ana-gateway, ana-heal, hermes-gateway, tanair-bridge, airtable-webhook, airtable-webhook-tunnel, agy-memory-tunnel
- docs/GROK_ACCESS.md, docs/HARDENING_LOG.md — redacted

## NOT included (and where it is)
- ~/.hermes/.env, auth.json, google_token.json, all tokens — never committed; owner keeps secrets separately.
- ~/.hermes/memories (MEMORY.md, USER.md), ~/AnaFile/{STATUS,DIRECTION,OWNER_TASKS}.md — personal; omitted because the repo is public.
- state.db, kanban.db, sessions, caches, logs, cron/, hooks/, profiles/ — runtime state.
- ~/scripts, ~/ana-handover (local git, no remote).
- All of the above (minus secrets) is in an offline tarball held by the owner (vps-backup, 2026-10-26).
- Hermes fork code: github.com/khairulxshafiq/AuraOne, branch live-snapshot-2026-10-26.
