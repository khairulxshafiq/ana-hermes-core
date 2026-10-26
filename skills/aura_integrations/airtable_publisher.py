#!/usr/bin/env python3
"""
Aura Airtable ${AIRTABLE_TABLE_NAME} Publisher Tool for Hermes Agent.
"""

import argparse
import json
import logging
import os
import sys
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aura.airtable_publisher")

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "${AIRTABLE_BASE_ID}")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "${AIRTABLE_TABLE_NAME}")
DEFAULT_BRAND = os.getenv("DEFAULT_BRAND", "Sakluma")


def save_draft_to_airtable(
    title: str,
    caption: str,
    platform: str = "facebook",
    brand: str = "",
    status: str = "Approved",
    hashtags: str = "",
    image_url: str = "",
    created_by: str = "Hermes (AuraOne)",
    content_type: str = "Article",
) -> dict:
    api_key = os.getenv("AIRTABLE_API_KEY", AIRTABLE_API_KEY)
    base_id = os.getenv("AIRTABLE_BASE_ID", AIRTABLE_BASE_ID)
    table_name = os.getenv("AIRTABLE_TABLE_NAME", AIRTABLE_TABLE_NAME)

    if not api_key or not base_id:
        return {"status": "error", "error": "AIRTABLE_API_KEY or AIRTABLE_BASE_ID is missing"}

    if not brand:
        brand = os.getenv("DEFAULT_BRAND", DEFAULT_BRAND)

    plat_name = "X" if platform.lower() in ["twitter", "x"] else platform.title()
    clean_caption = caption.replace("**", "").replace("*", "") if caption else ""

    url = f"https://api.airtable.com/v0/{base_id}/{table_name}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    fields = {
        "Title": title,
        "Caption": clean_caption,
        "Platform": [plat_name],
        "Post Status": status,
        "Brand": brand,
        "Content Type": content_type,
        "Created By": created_by,
        "Hashtags": hashtags,
    }
    if image_url:
        fields["Image file"] = [{"url": image_url}]

    try:
        with httpx.Client(timeout=15) as client:
            while True:
                resp = client.post(url, headers=headers, json={"fields": fields, "typecast": True})
                if resp.status_code == 200:
                    break
                elif resp.status_code == 422 and "UNKNOWN_FIELD_NAME" in resp.text:
                    err_msg = resp.text
                    removed = False
                    for k in list(fields.keys()):
                        if k in err_msg:
                            logger.info("Field '%s' not in Airtable schema, removing for retry.", k)
                            fields.pop(k, None)
                            removed = True
                    if not removed:
                        resp.raise_for_status()
                else:
                    resp.raise_for_status()

            data = resp.json()
            record_id = data.get("id")

            # Check for n8n Webhook trigger
            n8n_url = os.getenv("N8N_WEBHOOK_URL", "")
            if n8n_url:
                try:
                    n8n_payload = {
                        "event": "content_created",
                        "record_id": record_id,
                        "title": title,
                        "caption": clean_caption,
                        "platform": plat_name,
                        "brand": brand,
                        "image_url": image_url,
                        "hashtags": hashtags,
                        "status": status
                    }
                    n8n_resp = client.post(n8n_url, json=n8n_payload, timeout=10)
                    logger.info("n8n Webhook triggered: HTTP %s", n8n_resp.status_code)
                except Exception as n8n_err:
                    logger.warning("n8n Webhook trigger warning: %s", n8n_err)

            return {"status": "success", "record_id": record_id}
    except Exception as e:
        logger.error("Airtable save error: %s", e)
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Publish content draft to Airtable ${AIRTABLE_TABLE_NAME}")
    parser.add_argument("--title", required=True, help="Content Title")
    parser.add_argument("--caption", required=True, help="Post Caption")
    parser.add_argument("--platform", default="facebook", help="Target platform (facebook, instagram, x, etc.)")
    parser.add_argument("--brand", default="", help="Brand name")
    parser.add_argument("--hashtags", default="", help="Hashtags string")
    parser.add_argument("--image-url", default="", help="Public URL of featured image")
    args = parser.parse_args()

    res = save_draft_to_airtable(
        title=args.title,
        caption=args.caption,
        platform=args.platform,
        brand=args.brand,
        hashtags=args.hashtags,
        image_url=args.image_url,
    )
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
