# Provider Failover Across the Profile Fleet

Use when a provider key hits **401** (bad key) or **402 / RESOURCE_EXHAUSTED** (no credit).
The main chat session usually keeps working — it falls back to another provider — so the
failure is invisible until a delegated (profile) task silently returns nothing.

## 0. Establish which layer is actually broken

Three independent layers consume the same key family:

| Layer | Who uses it | Symptom when dead |
|---|---|---|
| Chat / reasoning | main session + all profiles | profile delegations return empty or error |
| Vision | `auxiliary.vision` | image/video frame review fails |
| ASR / audio | inline-audio multimodal call | transcription request returns 402 instantly |

Do not conclude "the model is broken" from one layer. Fire one tiny request per layer.

## 1. Probe the candidate keys with a real request

```python
import requests
r = requests.post("<base_url>/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"model": "<model>", "messages": [{"role": "user", "content": "Say OK"}],
          "max_tokens": 10}, timeout=25)
print(r.status_code, r.text[:160])
```

- `200` → key + model + base_url are all correct, record the working triple.
- `401 User not found` → key invalid/revoked. Common with aggregator/proxy keys that look
  valid in `.env` but have no account behind them.
- `402 … prepayment credits are depleted` → funded account, empty wallet. Top-up fixes it;
  RAM/CPU changes never will.
- `404 … no longer available to new users` → model retired on that account; switch to the
  model name the error message recommends.

**Measured working triple (verified 2026-10):**
`base_url=https://api.deepseek.com/v1`, `model=deepseek-v4-flash`,
key env `DEEPSEEK_API_KEY` (also accepts `deepseek-chat` on that endpoint — both return 200).

## 2. Audit EVERY profile, not just the default

Profiles carry their own `model:` block and do **not** inherit a later fix to the main
config. All five worker profiles were still pointing at the dead provider while the main
session had already fallen back to a healthy one.

```bash
for p in writer reviewer researcher coder dokumentalis; do
  f=~/.hermes/profiles/$p/config.yaml
  [ -f "$f" ] && python3 -c "
import sys,yaml;c=yaml.safe_load(open('$f'));m=c.get('model',{})
print('$p', m.get('provider'), m.get('default'))"
done
```

Also check each profile's `auxiliary.vision` — it is configured separately and will still
point at the dead provider after the chat model is repointed.

## 3. Repoint (script: `scripts/repoint_profiles.py`)

```bash
python3 scripts/repoint_profiles.py \
  --provider deepseek --model deepseek-v4-flash \
  --base-url https://api.deepseek.com/v1 --dry-run   # inspect first
```

The script copies `<config>.bak-<tag>` before writing, rewrites `model.provider`,
`model.default`, `model.base_url`, every `model.aliases.*` entry, and `auxiliary.vision`.
Aliases matter: leaving them pointing at the dead provider means a task routed to
`coding`/`bulk`/`writer` still fails even though the default looks fine.

## 4. Verify — and use the right command

```bash
hermes profile list        # ✅ authoritative: one Model column per profile
```

**Do not** verify with `hermes --profile <name> status` — it reports the *default*
profile's model and will make a successful repoint look like a failure. `hermes
--profile <name> config get model` has the same problem.

## 5. Rollback

Every write leaves `config.yaml.bak-<tag>` beside the original:

```bash
cp ~/.hermes/profiles/writer/config.yaml.bak-gemini-dead \
   ~/.hermes/profiles/writer/config.yaml
```

## 6. Remote worker-node triage (separate machine, shared key)

A node can be fully healthy and still be useless for AI work. Classify endpoints:

- **Green — no inference, keeps working even with a dead key:** scraping / RSS harvest,
  DB reads, filesystem/PDF text extraction, backup+upload, temp cleanup, watchdog/system
  probes. Verify with a real call (e.g. a scrape returning N articles, a list returning rows).
- **Red — needs the LLM, dies with the key:** research/synthesis, article summarisation,
  and the "summary" half of document parsing (text extraction still succeeds; the summary
  field returns `"Ringkasan AI tidak dapat dijana sepenuhnya. Teks asal berjaya diekstrak."`).

Fast failure (<1 s) with `status: failed` is the tell — a network or timeout problem looks
different. Response: keep using the node as a raw data harvester, do the thinking on the
box with the healthy key. Do not "fix" the node; its AI layer shares the same exhausted
account.

## 7. What to tell the owner

Keep the two costs apart:

- Transcript blocked → **ASR path problem** (credit, or local model too small). Fix = top-up
  or bigger box, and USD 5 usually covers dozens of hours of footage.
- Delegation failing → **fleet config problem**. Fix = repoint, costs nothing.
- Do not let "we'll just summarise locally" close an audio-transcription request — a
  text-only summariser never unblocks ASR.
