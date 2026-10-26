#!/usr/bin/env python3
"""Probe LLM providers used by Hermes: list models + modalities, test chat, test vision.

Usage:
    python3 probe_provider_models.py            # list models for all providers
    python3 probe_provider_models.py --chat     # + one cheap chat completion per model
    python3 probe_provider_models.py --vision   # + base64 image probe (vision lanes)

Reads keys from ~/.hermes/.env. Never prints key values.
"""
import base64
import os
import sys

import requests

ENV_FILE = os.path.expanduser("~/.hermes/.env")

PROVIDERS = {
    "deepseek": ("https://api.deepseek.com/v1", "DEEPSEEK_API_KEY"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY"),
}


def load_key(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    try:
        with open(ENV_FILE) as fh:
            for line in fh:
                line = line.strip()
                if line.startswith(name + "="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return ""


def tiny_png_b64() -> str:
    """64x64 solid red PNG, built without PIL."""
    import struct
    import zlib

    w = h = 64
    raw = b"".join(b"\x00" + bytes([200, 20, 20]) * w for _ in range(h))

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    return base64.b64encode(png).decode()


def list_models(name, base, key):
    try:
        r = requests.get(
            f"{base}/models", headers={"Authorization": f"Bearer {key}"}, timeout=25
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  [ERR] {name}: {exc}")
        return []
    if r.status_code != 200:
        print(f"  [ERR] {name}: HTTP {r.status_code} {r.text[:120]}")
        return []
    ids = []
    for m in r.json().get("data", []):
        mid = m.get("id")
        mods = (m.get("architecture") or {}).get("input_modalities") or m.get(
            "input_modalities"
        )
        ctx = m.get("context_window") or m.get("context_length") or (m.get("top_provider") or {}).get(
            "context_length"
        )
        flags = []
        if mods and "image" in mods:
            flags.append("VISION")
        if mid and mid.endswith(":free"):
            flags.append("FREE")
        print(f"    {mid} | mods={mods} | ctx={ctx} {' '.join(flags)}")
        ids.append(mid)
    return ids


def chat(base, key, model, image=None):
    content = "Reply with the single word OK."
    if image:
        content = [
            {"type": "text", "text": "What colour is this image? One word."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image}"},
            },
        ]
    try:
        r = requests.post(
            f"{base}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": content}],
                "max_tokens": 20,
            },
            timeout=90,
        )
    except Exception as exc:  # noqa: BLE001
        return f"EXC {exc}"
    if r.status_code != 200:
        return f"HTTP {r.status_code} {r.text[:160]}"
    body = r.json()
    usage = body.get("usage", {})
    msg = body["choices"][0]["message"]
    txt = (msg.get("content") or "").strip() or (msg.get("reasoning_content") or "").strip()[:60]
    return f"OK prompt_tokens={usage.get('prompt_tokens')} resolved={body.get('model')} :: {txt[:80]}"


def main():
    do_chat = "--chat" in sys.argv
    do_vision = "--vision" in sys.argv
    img = tiny_png_b64() if do_vision else None

    for name, (base, env) in PROVIDERS.items():
        key = load_key(env)
        print(f"\n=== {name} ({base}) key={'yes' if key else 'MISSING'} ===")
        if not key:
            continue
        ids = list_models(name, base, key)
        if do_vision and img:
            print("  -- vision probe (all listed models, first 40) --")
            for mid in ids[:40]:
                print(f"    {mid}: {chat(base, key, mid, image=img)}")
        elif do_chat:
            print("  -- chat probe --")
            for mid in ids[:6]:
                print(f"    {mid}: {chat(base, key, mid)}")


if __name__ == "__main__":
    main()
