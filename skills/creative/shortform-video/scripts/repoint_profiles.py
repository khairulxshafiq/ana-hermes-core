#!/usr/bin/env python3
"""Repoint Hermes profile models to a working provider.

Use when a shared provider key dies (401 bad key / 402 no credit) and the worker
profiles still point at it. The main chat falls back automatically, so the fleet
looks healthy while every delegation fails.

Every touched file is backed up to <config>.bak-<tag> first.

Usage:
    python3 repoint_profiles.py --provider deepseek --model deepseek-v4-flash \
        --base-url https://api.deepseek.com/v1 --dry-run
    python3 repoint_profiles.py --provider deepseek --model deepseek-v4-flash \
        --base-url https://api.deepseek.com/v1
    python3 repoint_profiles.py --provider deepseek --model deepseek-v4-flash \
        --profiles writer,reviewer --tag my-change

Verify afterwards with `hermes profile list` (NOT `hermes --profile X status`,
which reports the default profile's model).
"""

import argparse
import os
import shutil
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML required: pip install pyyaml")

DEFAULT_PROFILES = ["writer", "reviewer", "researcher", "coder", "dokumentalis"]


def profile_dir() -> str:
    return os.path.expanduser(os.environ.get("HERMES_HOME", "~/.hermes"))


def repoint(path: str, provider: str, model: str, base_url: str, tag: str, dry: bool) -> str:
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}

    m = cfg.get("model") or {}
    old = f"{m.get('provider')}/{m.get('default')}"

    m["provider"] = provider
    m["default"] = model
    if base_url:
        m["base_url"] = base_url

    # Aliases are separate routes (coding/bulk/writer/...) and keep the dead provider
    # unless rewritten — leaving them is the most common half-fix.
    aliases = m.get("aliases") or {}
    for name in list(aliases.keys()):
        aliases[name] = {"provider": provider, "model": model}
    if aliases:
        m["aliases"] = aliases

    # Vision is configured independently of the chat model.
    aux = cfg.get("auxiliary") or {}
    if "vision" in aux:
        aux["vision"] = {"provider": provider, "model": model,
                         "timeout": 60, "download_timeout": 30}
        cfg["auxiliary"] = aux

    cfg["model"] = m

    if dry:
        return f"[dry-run] {os.path.basename(os.path.dirname(path))}: {old} -> {provider}/{model}"

    shutil.copy2(path, f"{path}.bak-{tag}")
    with open(path, "w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)

    return f"OK {os.path.basename(os.path.dirname(path))}: {old} -> {provider}/{model}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default="")
    ap.add_argument("--profiles", default=",".join(DEFAULT_PROFILES))
    ap.add_argument("--tag", default="prev-provider")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    root = profile_dir()
    touched = 0
    for name in [p.strip() for p in args.profiles.split(",") if p.strip()]:
        path = os.path.join(root, "profiles", name, "config.yaml")
        if not os.path.exists(path):
            print(f"SKIP {name}: no config at {path}")
            continue
        print(repoint(path, args.provider, args.model, args.base_url, args.tag, args.dry_run))
        touched += 1

    print(f"\n{touched} profile(s) processed.")
    if not args.dry_run and touched:
        print("Verify with: hermes profile list")


if __name__ == "__main__":
    main()
