#!/usr/bin/env python3
"""export_agent_bundle.py — bina bundle pindahan agent (memory + skills + runbook).

Guna:
    python3 export_agent_bundle.py [--hermes ~/.hermes] [--archive ~/AnaFile] [--budget 25]

Hasil:
    <archive>/MIGRATION/00_README.md ... 08_IMPORT_GUIDE.md + skills_selected/
    <archive>/ana_portable_bundle_<tarikh>.tar.gz

PRINSIP: tiada NILAI rahsia dimasukkan. Hanya nama kunci, panjang, dan sumber semula.
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

PICK_DEFAULT = [
    "llm-provider-ops", "google-oauth-tokens", "rclone-remote-ops", "cloud-backup-auth",
    "content-flow", "shortform-video", "luma-worker", "model-router", "media-use",
    "telegram-native-ui", "hyperliquid", "bursa-malaysia",
]

LOSSES = """Grok/chatbot platform tiada: shell, VPS, cron, SSH, filesystem kekal,
worker swarm, gateway Telegram sendiri, backup berjadual, publisher sosial.
Yang dipindah: identiti, memori, playbook, inventori projek, checklist kredensial.
"""


def read(path):
    try:
        return pathlib.Path(path).read_text()
    except Exception:
        return ""


def env_key_names(env_path):
    rows = []
    for line in read(env_path).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        rows.append((key.strip(), len(val.strip())))
    return rows


def skill_entries(skills_dir):
    out = []
    for p in sorted(pathlib.Path(skills_dir).rglob("SKILL.md")):
        try:
            text = p.read_text()
        except Exception:
            continue
        name = p.parent.name
        m = re.search(r"^name:\s*(.+)$", text, re.M)
        if m:
            name = m.group(1).strip()
        d = re.search(r"^description:\s*(.+)$", text, re.M)
        desc = d.group(1).strip()[:140] if d else ""
        out.append((name, desc, p.parent))
    return out


def units():
    try:
        r = subprocess.run(
            ["systemctl", "--user", "list-units", "--type=service", "--no-legend", "--plain"],
            capture_output=True, text=True, timeout=30,
        )
        return [l.split()[0] for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hermes", default=os.path.expanduser("~/.hermes"))
    ap.add_argument("--archive", default=os.path.expanduser("~/AnaFile"))
    ap.add_argument("--budget", type=int, default=25, help="bilangan skill disalin penuh")
    args = ap.parse_args()

    hermes = pathlib.Path(args.hermes)
    archive = pathlib.Path(args.archive)
    out = archive / "MIGRATION"
    sel = out / "skills_selected"
    if sel.exists():
        shutil.rmtree(sel)
    sel.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today().isoformat()

    mem = read(hermes / "memories/MEMORY.md")
    user = read(hermes / "memories/USER.md")
    facts = read(hermes / "memories/long_term_facts.json")
    entries = skill_entries(hermes / "skills")
    keys = env_key_names(hermes / ".env")

    docs = {}
    docs["00_README.md"] = (
        "# Agent Portable Bundle\n"
        f"Dijana: {today}\n\n"
        "## Kandungan\n"
        "- 01 identiti, 02 profil pengguna, 03 fakta memori, 04 projek/aset,\n"
        "  05 runbook, 06 checklist kredensial (nama sahaja), 07 indeks skill,\n"
        "  08 panduan import, skills_selected/ (skill terpilih penuh).\n\n"
        f"## Had\n{LOSSES}"
    )
    docs["02_USER_PROFILE.md"] = "# PROFIL PENGGUNA\n\n" + (user or "(tiada USER.md)")
    docs["03_MEMORY_FACTS.md"] = (
        "# FAKTA MEMORI\n\n" + (mem or "(tiada MEMORY.md)")
        + "\n\n## long_term_facts.json\n```json\n" + facts[:3000] + "\n```\n"
    )

    idx = ["# INDEKS SKILL", "", f"Jumlah: {len(entries)} SKILL.md", ""]
    picked = []
    for name, desc, path in entries:
        if len(picked) < args.budget and name in PICK_DEFAULT:
            dest = sel / re.sub(r"[^A-Za-z0-9_.-]", "_", str(path.relative_to(hermes / "skills")))
            shutil.copytree(path, dest, dirs_exist_ok=True)
            picked.append(name)
            idx.append(f"- **{name}** (disalin) — {desc}")
    idx += ["", "## Selebihnya (indeks sahaja)", ""]
    for name, desc, _ in entries:
        if name not in picked:
            idx.append(f"- {name} — {desc}")
    docs["07_SKILLS_INDEX.md"] = "\n".join(idx)

    creds = ["# CHECKLIST KREDENSIAL (TIADA NILAI)", "", "Nama kunci + panjang (padanan sahaja):", ""]
    creds += [f"- `{k}` (len {n})" for k, n in sorted(keys)]
    docs["06_CREDENTIALS_CHECKLIST.md"] = "\n".join(creds) + "\n"

    svc = "\n".join(f"- `{u}`" for u in units()) or "- (tiada unit user)"
    docs["05_RUNBOOK.md"] = "# RUNBOOK\n\n## Servis user\n" + svc + "\n\n" + (
        "## Laluan penting\n"
        f"- state.db: {(hermes / 'state.db').stat().st_size // 1024 if (hermes / 'state.db').exists() else 0} KB\n"
        f"- skills: {len(entries)} SKILL.md\n"
    )

    docs["08_IMPORT_GUIDE.md"] = (
        "# PANDUAN IMPORT\n\n"
        "1. 01_IDENTITY -> Custom Instructions (mampat: identiti + tone + bahasa + 5 prinsip).\n"
        "2. 02/03 -> Memori, satu fakta satu entri.\n"
        "3. 04/05/06 -> Fail projek / knowledge upload.\n"
        "4. skills_selected -> playbook sebagai arahan, bukan kod.\n"
        "5. Ujian recall: 5 soalan fakta (ID, jenama, tone, IP, lane LLM).\n"
    )

    for name, text in docs.items():
        (out / name).write_text(text)

    bundle = archive / f"agent_portable_bundle_{today}.tar.gz"
    subprocess.run(["tar", "-czf", str(bundle), "-C", str(archive), "MIGRATION"], check=True)

    print(f"docs: {len(docs)} | skills disalin: {len(picked)} | kunci: {len(keys)}")
    print(f"bundle: {bundle} ({bundle.stat().st_size // 1024} KB)")
    print("PERINGATAN: semak 06_CREDENTIALS_CHECKLIST.md — pastikan tiada nilai rahsia.")


if __name__ == "__main__":
    sys.exit(main())
