---
name: delegate-verify-loop
description: "Verify delegated work via real files, not agent reports."
version: 1.0.0
author: ANA-Curator
license: MIT
metadata:
  hermes:
    tags: [delegation, verify, coder, agy, quality-control, git]
    category: productivity
---

# Delegate → Verify Reality Loop

## Prinsip
**`Status: SUCCESS` dalam report agent ≠ kerja sampai ke sasaran.** Delegated agents berjalan dalam konteks berasingan (GCP VM, subagent session, isolated clone) — keputusan mesti di-verify terhadap fail sebenar, bukan laporan mereka sendiri.

## Spot-Check Wajib (sebelum deliver ke Boss)
Buat semua checks secara sendiri pada keadaan sebenar:
- `git log --oneline -3` pada repo sasaran — commit baru betul-betul wujud?
- `ls` — fail yang patut dihapuskan hilang? fail patut kekal ada?
- `wc -c` / `wc -l` / `grep -c` — saiz & token kandungan match laporan?
- Syntax/logic check bebas (e.g. Node `new Function` untuk JS, `python -m json.tool` untuk JSON)
- **Post-rebrand BM leftover check** — selepas rebrand/English copy pass, jangan lupa check `app/login/`, `app/docs/`, `app/support/`. Landing page & cockpit selalu di-cover tapi pages dalam sering terlepas. Cari: `grep -rn "Kembali ke\|Log Masuk\|Daftar Akaun" app/login app/docs app/support`.

## Profile Routing Table
Bila ANA decide nak delegate, guna jadual ni:

| Task Class | Delegate To | Capabilities / Scope | Boundaries / Had | Verify Method |
|------------|------------|----------------------|------------------|---------------|
| Coding, quick fixes, local integration | **Coder** (VPS) | Python/JS scripting, git commit, local integration (<30 min) | Local VPS sahaja. Heavy compute delegasi ke Luma | git log, wc -c, syntax/unit test |
| Compute berat, video render 60fps | **Luma** (GCP 34.87.3.27) | Cloud Twin, Remotion/FFmpeg render, voice cloning (boss_voice_sample.wav), TanAir-Cloud repo git | Saluran pelaksana luaran. Hasil disimpan di GCP & Telegram | auto_sync_video.py output, video file check |
| Web research, fakta, data luar | **Researcher** | OpenRouter deepseek-v4.1-flash, search & synthesis | Draf teks, tidak ubah sistem atau publish | Spot-check citations & source URLs |
| Copywriting, posting, naratif | **Writer** | BytePlus deepseek-v4-flash, draf posting FB/Threads/Blog | Draf sahaja, tiada direct posting awam | Tone check, brand guidelines TanAir |
| Arkib, diagram seni bina, laporan | **Dokumentalis** | Mermaid diagrams, penyusunan status ~/AnaFile/ | Draf dokumentasi, dilarang edit config teras | File structure & markdown formatting |
| QA Gatekeeper & semakan ralat | **Reviewer** | Semakan pra-hantar kod & teks | Hanya menyemak, tiada kuasa deploy | Checklist pass/fail, audit diff |

### Verify approach per worker type
- **Coder/Luma**: verify on REAL FILES (git log, ls, wc, syntax check) — not on agent reports
- **Researcher**: spot-check cited sources actually say what the report claims
- **Writer**: read first/last paragraphs + verify brand names and tone
- **Reviewer**: the review IS the verification — confirm their checklist was thorough

## Cross-Profile Worker Chaining (Boss-Confirmed Pattern: Kanban + ANA Relay ✅)


### Confirmed Pipeline: Kanban Parent-Child + ANA Relay (Cara 1 + 3 Gabungan)

```
🧠 ANA (Orchestrator)
   │
   ├─ 1. Create task Worker A (Kanban)
   │     Worker A completes → writes to ~/AnaFile/handoff/
   │
   ├─ 🧠 ANA verify hasil ✅ → enrich context
   │
   ├─ 2. Create task Worker B with `parents: [Worker-A-task-id]`
   │     Worker B reads handoff file → completes
   │
   ├─ 🧠 ANA verify hasil ✅
   │
   └─ 3. Deliver final result ke Boss 🎯
```

**Key rules:**
1. **Parent-child auto-scheduling** — Worker B auto-promotes to ready only when Worker A is done (Kanban handles the wait)
2. **ANA verify every step** — read the actual handoff file, check quality, enrich context before passing to next worker
3. **Worker isolation preserved** — Workers never know other workers exist. Their context = task body + handoff file path only
4. **Handoff directory** — `~/AnaFile/handoff/<project>-<topic>-<YYYYMMDD>.md`
5. **Handoff naming pitfall** — Antigravity/Agy names handoff files by **project/topic** (`tanair-ana-gateway-master-queue-20261013.md`), NOT by "antigravity". Searching `grep -r antigravity` or `find *antigravity*` will MISS these. Search by project name (tanair, sakluma, bynaykey) OR by file age (files modified in last 48h).
6. **Loop max 3x** per worker. If ANA rejects Worker A's output 3 times, stop and use HITL buttons
6. **Task brief MUST state:** "You CANNOT access other profiles' files or memory. Your context is in this task body only. Read from ~/AnaFile/handoff/<file>.md if cited."

### Decision Rule
- **Simple 1-worker task** → Direct Kanban create, no chaining needed
- **Multi-worker pipeline** → Use Kanban parent-child + ANA relay. ANA creates each task sequentially (not all at once) so she can verify and enrich between hops
- **When ANA must review before next worker** → Always. This is the boss's explicit requirement

### Handoff Format Reference
See `references/handoff-protocol.md` for handoff file naming conventions and format standards.

### Worker LLM Cost Optimization (Confirmed 13Oct2026)

| Profile | Model | Provider | Cost Strategy |
|---------|-------|----------|---------------|
| 🧠 ANA | `ark-code-latest` | BytePlus | Paid — Lead Orchestrator (included in sub) |
| 🔧 Coder | `ark-code-latest` | BytePlus | Paid — Local Engineering (<30 min, included in sub) |
| 🔍 Researcher | `deepseek-v4.1-flash` | **OpenRouter** | **$0.075/M input** — murah untuk model research-grade. Free fallback: Meta Llama 3.3 70B → Qwen 3.8 27B → Deepseek Chat. **Jangan tukar ke BytePlus paid** — Boss confirm research intermittent, guna lane murah. |
| ✍️ Writer | `deepseek-v4-flash-ga-260731` | BytePlus | 💰 Jimat — flash cukup untuk content, included in sub |
| 📋 Dokumentalis | `deepseek-v4-flash-ga-260731` | BytePlus | 💰 Jimat — system docs, included in sub |
| ⚖️ Reviewer | `deepseek-v4-flash-ga-260731` | BytePlus | 💰 Jimat — QA gate, flash default, `reason` alias pro bila perlu |
| ⚡ Luma | Cloud Twin (GCP SG 34.87.3.27, host alias `agy`) | GCP / Gemini | VM Compute — 60fps Motion Video & Git Repo Worker (GCP cost). SSH: `ssh agy` (user khairulshafiq, key ~/.ssh/id_agy). Model: `Gemini 3.8 Flash (High)` via `agy --model "Gemini 3.8 Flash (High)" --dangerously-skip-permissions --print="..."` |

**Rules:**
- Researcher runs on **OpenRouter deepseek-v4.1-flash ($0.075/M)** — bukan BytePlus. Sebab: research intermittent (on-demand bila boss minta), tak perlu sub. Free fallback chain sedia ada.
- Writer/Reviewer guna BytePlus flash (cheapest BytePlus tier — included in sub, zero extra cost)
- Simpan `deepseek-v4-pro-ga-260813` hanya untuk complex reasoning via `reason` alias — jangan guna sebagai default
- Kalau worker free/cheap model cukup, jangan upgrade. Boss prefers cost-opt over performance.
- **Cost transparency:** Bila boss tanya model/cost mana-mana worker, ANA WAJIB boleh jawab dengan tepat — provider, model name, dan justifikasi kenapa guna yang tu (bukan yang mahal).

## Pipeline On-Demand Model (Confirmed 13Oct2026)

Boss confirmed: **Workers jalan bila diminta SAHAJA — bukan auto-daily, bukan proactive briefing.**

### Trigger Rule
- Boss minta sesuatu → ANA decide pipeline → spawn workers → verify → deliver
- JANGAN hantar auto-update pagi/petang tanpa diminta
- JANGAN buat daily briefing atau proactive crawling
- **Researcher aktif on-demand** — bila boss tanya pasal saham/berita/data/content, baru Researcher execute

### Canonical Pipelines

**📊 Saham / Kewangan:**
```
Boss: "Nak analisa saham X"
  → 🔍 Researcher cari data terkini + news (OpenRouter, $0.075/M)
  → 🧠 ANA verify hasil research ✅
  → 🧠 ANA verify ✅
  → 👁️ Reviewer QA check
  → 🧠 ANA final verify → deliver ke Boss 🎯
```

**📝 Content / Copywriting:**
```
Boss: "Tulis pasal product/topic"
  → 🔍 Researcher cari rujukan / data (OpenRouter)
  → 🧠 ANA verify hasil research ✅
  → ✍️ Writer tulis draft (BytePlus flash — included)
  → 🧠 ANA verify ✅
  → 👁️ Reviewer QA (tone check, brand guidelines)
  → 🧠 ANA final verify → deliver ke Boss 🎯
```

**🔧 Coding / Teknikal:**
```
Boss: "Fix/pasang/bina feature"
  → ⚡ Luma (heavy) atau 🔧 Coder (quick fix)
  → 🧠 ANA verify atas fail sebenar (git log, ls, syntax check)
  → Deliver ke Boss 🎯
```

**🎨 Visual / Image:**
```
Boss: hantar gambar / request visual
  → 🧠 ANA present draft ke Boss
  → Boss approve
  → 🧠 ANA verify → deliver 🎯
```

### Pipeline Rules
1. **Researcher SELALU dulu** untuk content/saham task — cari data sebelum tulis/analisa
2. **Reviewer SELALU last** — QA gate sebelum sampai boss
3. **ANA verify SETIAP peringkat** — jangan percaya worker report semata-mata
4. **Workers tak pernah deliver direct ke boss** — hanya ANA yang deliver
5. **Max 3x loop per worker** — kalau gagal 3x, HITL buttons minta keputusan boss
6. **Zero token bazir** — guna worker ikut keperluan, bukan sebab trendy

## Kesilapan yang Berulang (Instrumental dari 17Sep2026 merge)
1. **Split-brain repo**: Coder kerja pada fork/copy berasingan. Merge + test PASSED semua, tapi repo sasaran (Tencent / GitHub origin) tak berubah. Arahan yang lupa: `git push origin main` dari mesin jauh, kemudian `git pull` pada mesin utama. **Push→pull = single source of truth.**
2. **Delegate foreground timeout (exit 124, ~2 min) ≈ BUKAN kegagalan** — task Coder masih jalan di background. Poll `ssh agy 'tail -60 ~/agy_result.md'` tiap 3–5 minit. Jangan double-spawn task yang sama.
3. **Untracked fail lokal bertembung dengan remote** (e.g. scp manual sebelum pull) → `git pull` diblok. `mv` fail ke /tmp, pull, `diff` untuk pastikan kandungan tak hilang.
4. **Stash dulu** kalau working tree dirty (auto-updated stats files) sebelum pull.
5. **Branch conflict on push** — bila remote dah ada branch nama sama, `git push origin branch` ditolak. Jangan `git push --force`. Sebaliknya: `git pull origin branch --rebase`, resolve conflict guna `git checkout --ours <fail>` untuk fail yang versi kita adalah betul, `git add -A && git rebase --continue`, then push.
6. **Double arrow CTA pattern** — teks butang `"Get Started Free →"` + component dah auto-render `<ArrowRight />` icon = dua arrow. Simpan teks sebagai `"Get Started Free"` tanpa `→` / `->` bila component dah tambah icon sendiri. Cari semua `→` dalam teks button sebelum commit.
7. **Task brief mesti nyatakan FAIL yang JANGAN disentuh** — agent cenderung ulang fix pada fail yang sama (e.g. AntigravityCanvas.tsx) bila mobile layout broken, walaupun punca sebenar dekat HTML layout (app/page.tsx). Dalam brief: senaraikan explicit "JANGAN edit <fail>" + "Target: <fail betul>".
8. **Canvas vs HTML overlap — jangan teka centerY** — bila partikel canvas bertindih dengan HTML content, jangan ubah centerY semata-mata. Diagnose live: Chrome DevTools mobile emulation → inspect stacking context (z-index, position absolute/relative), canvas container height (`h-[850px]` hardcoded vs viewport), mask-image position. Root cause usually bukan centerY tapi canvas container position/size vs HTML padding.

## Luma Offline Fallback (from 30Sep2026 rebrand task)

### Critical: Luma SSH connectivity
Luma (GCP 34.87.3.27) uses **host alias `agy`** in SSH config — NOT raw IP. The SSH config at `~/.ssh/config` defines:
```
Host agy
    HostName 34.87.3.27
    User khairulshafiq
    IdentityFile ~/.ssh/id_agy
```
- **Always test with `ssh agy "echo SSH_OK"`**, not `ssh ubuntu@34.87.3.27` (that user/key combo fails).
- The `agy_delegate.sh` script uses `scp agy:~/luma_task_current.md` and `ssh agy` — it works because it uses the alias.
- If you test manually with raw IP + wrong user/key, you'll get `Permission denied (publickey)` — this is NOT the VM being down, it's the wrong SSH target.

Apabila `agy_delegate.sh` gagal exit 124 (SSH timeout) dan:
- **Tiada AGY_RESULT_*.md baru** — SSH gagal sebelum runner start → Luma VM unreachable. Jangan retry.
- **AGY_RESULT_*.md wujud tapi model stalled** — runner started tapi model tak jawab → boleh retry sekali.

### Decision Tree
1. **Is the task purely text/git/ops?** (sed replace, file rename, README, git commit/push, npm build/test) → **ANA execute directly** — no need for Luma's compute engine.
2. **Is the task complex coding?** (new feature, refactor, complex logic) → Try Luma once more via `process(wait)` with longer timeout; if still 124, inform Boss via HITL buttons.
3. **Is it a quick fix?** (< 3 tool calls) → ANA handle regardless of Luma status.

### ANA Direct Execution Workflow (for rebrand/git tasks)
When falling back to ANA execution on VPS:
1. **Clone** repo to `/tmp/` — `git clone <url> /tmp/workdir`
2. **Sed replace** in batches (safe ordering: longest match first):
   ```bash
   # Order matters — do "TanAir Cloud" before "TanAir" to avoid double-replace
   find . -type f \( -name "*.md" -o -name "*.ts" -o -name "*.tsx" -o -name "*.css" \) \
     ! -path "./node_modules/*" ! -path "./.git/*" \
     -exec sed -i 's/TanAir Cloud/TanAir Cloud/g' {} \;
   find . -type f ... -exec sed -i 's/\bTanAir\b/TanAir/g' {} \;
   ```
3. **Rename files** with `mv` + sed pattern on the path
4. **Update cross-references** — second pass for renamed file names in backtick references
5. **Update README** — replace boilerplate with proper SaaS description
6. **Commit & push** — `git add -A && git commit -m "..." && git push origin main`
7. **Verify** — `git log --oneline -3`, `npm install`, `npm run build`, `npx vitest run`
   - **Build note**: prerender error due to missing `.env.local` is **pre-existing** — not caused by rebrand. Check that TypeScript compile passes and tests pass.
8. **Update repo metadata** — `gh repo edit --description "..." --homepage "..."`

### Pitfall: Brand file references in cross-references
File renames (e.g. `01_TANAIR_*.md` → `01_TANAIR_*.md`) leave stale backtick references in audit docs. After renaming files, run a second sed pass specifically targeting those file-name references before committing.

## Loop (max 3x)
Kesan masalah → tulis semula arahan delegate yang lebih spesifik (cite bukti: output verbatim yang patut berubah, fail yang patut wujud) → verify semula. Gagal 3x → stop & minta keputusan Boss (One-Tap buttons).

## Workflow Penuh untuk Task Berat
1. Audit dahulu, JANGAN terus tweak code — audit semua fail → senarai section → matrix keep/merge/drop → spec redesign.
2. Boss approve plan sebelum execute.
3. Pass execute ke Coder; cite fail laporan audit sebagai source-of-truth; declare explicitly fail yang WAJIB kekal vs dihapuskan; larang build compiler (vanilla JS untuk web prototaip).
4. Verify spot-check atas file sebenar sebelum deliver.
