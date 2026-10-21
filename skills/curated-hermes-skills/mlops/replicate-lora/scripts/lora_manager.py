#!/usr/bin/env python3
"""
LoRA Training Manager for Replicate & ANA.ai (Hermes Skill)
Handles dataset packaging, long-lived hosting (Google Drive / staging),
asynchronous training trigger, persistent status tracking, and fail-fast alerting.
"""

import os
import sys
import json
import time
import zipfile
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

TASKS_FILE = Path.home() / ".hermes" / "lora_tasks.json"
GOOGLE_TOKEN_FILE = Path.home() / ".hermes" / "google_token.json"
SECRETS_FILE = Path.home() / ".env.secrets"

# Default Replicate FLUX LoRA Trainer
DEFAULT_TRAINER_MODEL = "ostris/flux-dev-lora-trainer"
DEFAULT_TRAINER_VERSION = "b6af14222e2c6a081ed55709fbc0120227eed761658449bd3a0264958b7ac166"

def get_replicate_token(cli_token=None):
    """Retrieve Replicate API token from CLI, env, or secrets files."""
    if cli_token:
        return cli_token
    token = os.environ.get("REPLICATE_API_TOKEN")
    if token:
        return token
    # Check ~/.env.secrets
    if SECRETS_FILE.exists():
        with open(SECRETS_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("export REPLICATE_API_TOKEN="):
                    return line.split("=", 1)[1].strip("\"'")
                if line.startswith("REPLICATE_API_TOKEN="):
                    return line.split("=", 1)[1].strip("\"'")
    # Check ~/.zshrc
    zshrc = Path.home() / ".zshrc"
    if zshrc.exists():
        with open(zshrc, "r") as f:
            for line in f:
                line = line.strip()
                if "REPLICATE_API_TOKEN=" in line and not line.startswith("#"):
                    parts = line.replace("export ", "").split("=", 1)
                    if len(parts) == 2 and parts[0].strip() == "REPLICATE_API_TOKEN":
                        return parts[1].strip("\"'")
    return None

def load_tasks():
    """Load tracked tasks from lora_tasks.json."""
    if TASKS_FILE.exists():
        try:
            with open(TASKS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_tasks(tasks):
    """Save tracked tasks to lora_tasks.json atomically."""
    TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = TASKS_FILE.with_suffix(".tmp")
    with open(temp_file, "w") as f:
        json.dump(tasks, f, indent=2)
    temp_file.replace(TASKS_FILE)

def verify_url_accessibility(url, timeout=15):
    """Verify that a URL returns HTTP 200 and is directly downloadable."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Replicate-Dataset-Verifier/1.0)"},
        method="GET"
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            headers = dict(response.info())
            content_length = headers.get("Content-Length", "unknown")
            return {
                "ok": status == 200,
                "status": status,
                "content_length": content_length,
                "content_type": headers.get("Content-Type", "unknown")
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}

# --- SUBCOMMAND 1: PREPARE DATASET ZIP ---
def cmd_prepare(args):
    source_dir = Path(args.input_dir).expanduser().resolve()
    if not source_dir.exists() or not source_dir.is_dir():
        print(f"❌ Error: Direktori input '{source_dir}' tidak wujud.")
        sys.exit(1)

    image_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    caption_extensions = {".txt", ".caption"}

    image_files = [f for f in source_dir.iterdir() if f.suffix.lower() in image_extensions and not f.name.startswith(".")]

    if not image_files:
        print(f"❌ Error: Tiada imej sah (.jpg, .jpeg, .png, .webp) dijumpai dalam '{source_dir}'.")
        sys.exit(1)

    print(f"📁 Dijumpai {len(image_files)} fail imej dalam '{source_dir}'.")
    if len(image_files) < 10:
        print(f"⚠️ Amaran: Hanya {len(image_files)} imej. Disyorkan sekurang-kurangnya 12-25 imej pelbagai sudut untuk kualiti LoRA terbaik.")

    out_zip = Path(args.out).expanduser().resolve() if args.out else source_dir.parent / f"{source_dir.name}_dataset.zip"
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    count_img = 0
    count_captions = 0
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for img in sorted(image_files):
            # Clean archive name: flat structure inside zip
            clean_name = img.name
            zf.write(img, arcname=clean_name)
            count_img += 1

            # Check matching caption file
            for ext in caption_extensions:
                cap_file = img.with_suffix(ext)
                if cap_file.exists():
                    zf.write(cap_file, arcname=cap_file.name)
                    count_captions += 1
                    break

    size_mb = out_zip.stat().st_size / (1024 * 1024)
    print(f"✅ Dataset berjaya dizip:")
    print(f"   Lokasi: {out_zip}")
    print(f"   Jumlah Imej: {count_img}")
    print(f"   Jumlah Kapsyen: {count_captions}")
    print(f"   Saiz Zip: {size_mb:.2f} MB")
    return str(out_zip)

# --- SUBCOMMAND 2: UPLOAD DATASET (PERSISTENT >=4H) ---
def upload_to_gdrive(zip_path):
    """Upload zip to Google Drive with anyone-reader permission and return direct download URL."""
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError:
        print("⚠️ googleapiclient / google.oauth2 tiada. Gunakan fallback staging.")
        return None

    if not GOOGLE_TOKEN_FILE.exists():
        print(f"⚠️ '{GOOGLE_TOKEN_FILE}' tiada.")
        return None

    try:
        with open(GOOGLE_TOKEN_FILE, "r") as f:
            token_data = json.load(f)
        creds = Credentials.from_authorized_user_info(token_data)
        drive_service = build("drive", "v3", credentials=creds)

        file_metadata = {
            "name": Path(zip_path).name,
            "description": "LoRA Training Dataset (Auto-uploaded by ANA / Hermes)",
            "mimeType": "application/zip"
        }
        media = MediaFileUpload(zip_path, mimetype="application/zip", resumable=True)

        print("☁️ Memuat naik ke Google Drive...")
        file = drive_service.files().create(body=file_metadata, media_body=media, fields="id, name, webViewLink").execute()
        file_id = file.get("id")

        # Set public read permission so Replicate worker can download it
        permission = {"type": "anyone", "role": "reader"}
        drive_service.permissions().create(fileId=file_id, body=permission).execute()

        # Direct download link for Google Drive
        direct_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        print(f"✅ Muat naik Google Drive berjaya! File ID: {file_id}")
        return direct_url
    except Exception as e:
        print(f"⚠️ Gagal muat naik Google Drive: {e}")
        return None

def upload_to_tmpfiles(zip_path):
    """Upload to tmpfiles.org as a resilient 60-minute to 24-hour staging fallback."""
    import mimetypes
    print("☁️ Menggunakan Staging Fallback (tmpfiles.org)...")
    url = "https://tmpfiles.org/api/v1/upload"
    boundary = "----WebKitFormBoundary" + str(int(time.time()))

    filename = Path(zip_path).name
    with open(zip_path, "rb") as f:
        file_bytes = f.read()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success":
                page_url = data["data"]["url"]
                # Convert page url to direct download url: https://tmpfiles.org/12345/file.zip -> https://tmpfiles.org/dl/12345/file.zip
                direct_url = page_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                return direct_url
    except Exception as e:
        print(f"⚠️ Fallback tmpfiles.org gagal: {e}")
    return None

def cmd_upload(args):
    zip_path = Path(args.zip_path).expanduser().resolve()
    if not zip_path.exists() or not zip_path.is_file():
        print(f"❌ Error: Fail zip '{zip_path}' tidak wujud.")
        sys.exit(1)

    direct_url = None
    if args.method in ("auto", "drive"):
        direct_url = upload_to_gdrive(str(zip_path))

    if not direct_url and args.method in ("auto", "temp"):
        direct_url = upload_to_tmpfiles(str(zip_path))

    if not direct_url:
        print("❌ Gagal menjana direct URL yang boleh diakses.")
        sys.exit(1)

    print(f"🔗 Direct Download URL: {direct_url}")
    print("🔍 Mengesahkan kesahihan pautan (HTTP GET 200)...")
    check = verify_url_accessibility(direct_url)
    if check.get("ok"):
        print(f"✅ Pautan disahkan 100% aktif (Status: {check['status']}, Saiz: {check.get('content_length')} bytes)")
    else:
        print(f"⚠️ Amaran: Semakan pautan gagal: {check.get('error')}")

    print(json.dumps({"url": direct_url, "verified": check.get("ok", False)}))
    return direct_url

# --- SUBCOMMAND 3: TRIGGER ASYNC TRAINING ---
def cmd_train(args):
    token = get_replicate_token(args.token)
    if not token:
        print("❌ Error: REPLICATE_API_TOKEN tidak dijumpai. Tetapkan dalam persekitaran atau melalui argumen --token.")
        sys.exit(1)

    # Validate dataset URL first
    print(f"🔍 Mengesahkan dataset URL sebelum menghantar tugasan ke Replicate...")
    check = verify_url_accessibility(args.dataset_url)
    if not check.get("ok"):
        print(f"❌ PERINGATAN KESELAMATAN: Dataset URL tidak dapat dimuat turun (Status/Ralat: {check.get('error')}).")
        print("   Jangan teruskan dengan Replicate kerana GPU worker akan gagal akibat link tamat tempoh!")
        sys.exit(1)

    trainer_model = args.trainer or DEFAULT_TRAINER_MODEL
    trainer_version = args.version or DEFAULT_TRAINER_VERSION

    payload = {
        "destination": args.destination,
        "input": {
            "input_images": args.dataset_url,
            "steps": args.steps,
            "learning_rate": args.learning_rate,
            "batch_size": 1,
            "resolution": args.resolution,
            "is_lora": True
        }
    }
    if args.trigger_word:
        payload["input"]["trigger_word"] = args.trigger_word

    url = f"https://api.replicate.com/v1/models/{trainer_model}/versions/{trainer_version}/trainings"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8")
        print(f"❌ Replicate API Error ({e.code}): {err_msg}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Request Error: {e}")
        sys.exit(1)

    training_id = data.get("id")
    status = data.get("status")
    print(f"🚀 Tugasan Training Berjaya Dimulakan di Replicate!")
    print(f"   Training ID : {training_id}")
    print(f"   Destinasi   : {args.destination}")
    print(f"   Status Awal : {status}")
    print(f"   Pautan Web  : https://replicate.com/p/{training_id}")

    # Save to local persistent task log
    tasks = load_tasks()
    tasks[training_id] = {
        "id": training_id,
        "created_at": datetime.now().isoformat(),
        "destination": args.destination,
        "trigger_word": args.trigger_word or "",
        "dataset_url": args.dataset_url,
        "steps": args.steps,
        "status": status,
        "web_url": f"https://replicate.com/p/{training_id}",
        "last_checked": datetime.now().isoformat(),
        "error": None,
        "output": None
    }
    save_tasks(tasks)
    print(f"💾 Metadata disimpan ke '{TASKS_FILE}'.")
    return training_id

# --- SUBCOMMAND 4: CHECK STATUS ---
def cmd_status(args):
    token = get_replicate_token(args.token)
    if not token:
        print("❌ Error: REPLICATE_API_TOKEN diperlukan untuk memeriksa status.")
        sys.exit(1)

    training_id = args.training_id
    url = f"https://api.replicate.com/v1/trainings/{training_id}"
    headers = {"Authorization": f"Bearer {token}"}

    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"❌ Replicate API Error ({e.code}): {e.read().decode('utf-8')}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Request Error: {e}")
        sys.exit(1)

    status = data.get("status")
    error = data.get("error")
    output = data.get("output")
    metrics = data.get("metrics", {})

    print(f"📊 Status Semasa Tugasan [{training_id}]:")
    print(f"   Status      : {status.upper()}")
    if metrics:
        print(f"   Masa Diambil: {metrics.get('predict_time', 'N/A')} saat")
    if error:
        print(f"   ❌ Ralat    : {error}")
    if output:
        print(f"   🎉 Output   : {json.dumps(output, indent=2)}")

    # Update persistent state
    tasks = load_tasks()
    if training_id in tasks:
        tasks[training_id]["status"] = status
        tasks[training_id]["error"] = error
        tasks[training_id]["output"] = output
        tasks[training_id]["last_checked"] = datetime.now().isoformat()
        save_tasks(tasks)

    # Return structured json for automated agent usage
    return {"id": training_id, "status": status, "error": error, "output": output}

# --- SUBCOMMAND 5: LIST TASKS ---
def cmd_list(args):
    tasks = load_tasks()
    if not tasks:
        print("📭 Tiada tugasan LoRA direkodkan dalam sejarah.")
        return

    print(f"📋 Senarai Tugasan LoRA ({len(tasks)} direkodkan):")
    print("-" * 80)
    print(f"{'ID':<25} | {'STATUS':<12} | {'DESTINASI':<25} | {'TARIKH':<10}")
    print("-" * 80)
    for tid, t in sorted(tasks.items(), key=lambda x: x[1].get("created_at", ""), reverse=True):
        date_str = t.get("created_at", "")[:10]
        status = t.get("status", "unknown").upper()
        dest = t.get("destination", "N/A")[:25]
        print(f"{tid:<25} | {status:<12} | {dest:<25} | {date_str:<10}")
    print("-" * 80)

def main():
    parser = argparse.ArgumentParser(description="Hermes / ANA LoRA Manager for Replicate")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # prepare
    p_prep = subparsers.add_parser("prepare", help="Pakej folder imej menjadi fail zip bersih")
    p_prep.add_argument("input_dir", help="Direktori imej latihan")
    p_prep.add_argument("--out", "-o", help="Nama/laluan fail zip output (pilihan)")

    # upload
    p_up = subparsers.add_parser("upload", help="Muat naik fail zip ke storan tahan lama (>=4 jam)")
    p_up.add_argument("zip_path", help="Laluan fail zip dataset")
    p_up.add_argument("--method", choices=["auto", "drive", "temp"], default="auto", help="Kaedah muat naik")

    # train
    p_tr = subparsers.add_parser("train", help="Mulakan latihan LoRA di Replicate secara tak segerak (async)")
    p_tr.add_argument("--dataset-url", required=True, help="URL zip dataset yang disahkan aktif")
    p_tr.add_argument("--destination", required=True, help="Nama model Replicate (cth: khairulshafiq/shaf-wali-lora)")
    p_tr.add_argument("--trigger-word", default="", help="Perkataan pencetus / trigger word (cth: SHAFWALI)")
    p_tr.add_argument("--steps", type=int, default=1000, help="Jumlah langkah latihan (default: 1000)")
    p_tr.add_argument("--learning-rate", type=float, default=0.0004, help="Learning rate (default: 0.0004)")
    p_tr.add_argument("--resolution", type=int, default=1024, help="Resolusi imej (default: 1024)")
    p_tr.add_argument("--trainer", help="Trainer model ID")
    p_tr.add_argument("--version", help="Trainer version ID")
    p_tr.add_argument("--token", help="Replicate API Token (pilihan jika ada dalam ENV)")

    # status
    p_st = subparsers.add_parser("status", help="Semak status terkini latihan di Replicate")
    p_st.add_argument("training_id", help="Replicate Training ID")
    p_st.add_argument("--token", help="Replicate API Token")

    # list
    subparsers.add_parser("list", help="Papar semua tugasan latihan yang direkodkan")

    args = parser.parse_args()

    if args.subcommand == "prepare":
        cmd_prepare(args)
    elif args.subcommand == "upload":
        cmd_upload(args)
    elif args.subcommand == "train":
        cmd_train(args)
    elif args.subcommand == "status":
        cmd_status(args)
    elif args.subcommand == "list":
        cmd_list(args)

if __name__ == "__main__":
    main()

