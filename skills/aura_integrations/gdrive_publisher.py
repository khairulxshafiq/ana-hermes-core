#!/usr/bin/env python3
"""
Aura Google Drive Storage Publisher Tool for Hermes Agent.
"""

import argparse
import json
import logging
import os
import sys
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aura.gdrive_publisher")

GDRIVE_API = "https://www.googleapis.com/drive/v3"
GDRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"
DEFAULT_FOLDER_ID = os.getenv("GDRIVE_FOLDER_ID", "1Apv70Qwp2iF0405kn4mmzaB1UmXkWwqM")


def get_gdrive_access_token() -> str | None:
    sa_json_str = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    if not sa_json_str:
        return None
    try:
        sa_info = json.loads(sa_json_str)
        import google.auth.transport.requests
        from google.oauth2 import service_account

        credentials = service_account.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/drive"],
        )
        request = google.auth.transport.requests.Request()
        credentials.refresh(request)
        return credentials.token
    except Exception as e:
        logger.error("Failed to get Google Drive access token: %s", e)
        return None


def upload_file_to_drive(
    file_bytes: bytes,
    filename: str,
    mime_type: str = "image/jpeg",
    folder_id: str | None = None,
) -> dict:
    if not folder_id:
        folder_id = DEFAULT_FOLDER_ID

    token = get_gdrive_access_token()
    if not token:
        return {"status": "error", "error": "GOOGLE_SERVICE_ACCOUNT_JSON is not configured or invalid"}

    try:
        headers = {"Authorization": f"Bearer {token}"}
        metadata = json.dumps({"name": filename, "parents": [folder_id]})
        boundary = b"aura_hermes_boundary"
        body = (
            b"--" + boundary + b"\r\n"
            b"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            + metadata.encode()
            + b"\r\n"
            b"--" + boundary + b"\r\n"
            b"Content-Type: " + mime_type.encode() + b"\r\n\r\n"
            + file_bytes
            + b"\r\n"
            b"--" + boundary + b"--"
        )
        with httpx.Client(timeout=30) as client:
            resp = client.post(
                f"{GDRIVE_UPLOAD_API}/files",
                params={"uploadType": "multipart", "fields": "id,name,webViewLink"},
                content=body,
                headers={
                    **headers,
                    "Content-Type": "multipart/related; boundary=aura_hermes_boundary",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            file_id = data.get("id")

            # Make public read permission
            perm_url = f"{GDRIVE_API}/files/{file_id}/permissions"
            perm_payload = {"role": "reader", "type": "anyone"}
            client.post(perm_url, json=perm_payload, headers=headers)

        dl_link = f"https://docs.google.com/uc?export=download&id={file_id}"
        return {
            "status": "success",
            "file_id": file_id,
            "name": data.get("name"),
            "download_link": dl_link,
        }
    except Exception as e:
        logger.error("upload_file_to_drive error: %s", e)
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Upload file to Google Drive")
    parser.add_argument("--file", required=True, help="Local file path to upload")
    parser.add_argument("--mime", default="image/jpeg", help="MIME type (image/jpeg, text/plain, image/png, etc.)")
    parser.add_argument("--folder-id", default="", help="Target Google Drive Folder ID")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(json.dumps({"status": "error", "error": f"File not found: {args.file}"}))
        sys.exit(1)

    with open(args.file, "rb") as f:
        content = f.read()

    filename = os.path.basename(args.file)
    res = upload_file_to_drive(
        file_bytes=content,
        filename=filename,
        mime_type=args.mime,
        folder_id=args.folder_id or None,
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
