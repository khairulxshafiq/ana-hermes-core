#!/usr/bin/env python3
"""
Aura Web Scraper Tool for Hermes Agent.
Scrapes content from URLs using Firecrawl API or fallback HTTP client.
"""

import argparse
import json
import logging
import os
import re
import sys
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("aura.web_scraper")

FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")


def scrape_url(url: str) -> dict:
    api_key = os.getenv("FIRECRAWL_API_KEY", FIRECRAWL_API_KEY)
    
    # Try Firecrawl API first if key exists
    if api_key:
        try:
            fc_url = "https://api.firecrawl.dev/v1/scrape"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "url": url,
                "formats": ["markdown"]
            }
            with httpx.Client(timeout=30) as client:
                resp = client.post(fc_url, headers=headers, json=payload)
                if resp.status_code == 200:
                    res_data = resp.json().get("data", {})
                    markdown = res_data.get("markdown", "")
                    meta = res_data.get("metadata", {})
                    return {
                        "status": "success",
                        "title": meta.get("title") or meta.get("ogTitle") or "Scraped Article",
                        "content": markdown[:4000],
                        "source_url": url,
                        "image_url": meta.get("ogImage") or meta.get("image") or "",
                        "engine": "firecrawl"
                    }
        except Exception as e:
            logger.warning("Firecrawl scrape failed, falling back to HTTP: %s", e)

    # Fallback to direct HTTP fetch + basic text extraction
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        with httpx.Client(timeout=20, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            html = resp.text

        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "Scraped Article"

        # Remove script and style elements
        clean_text = re.sub(r"<(script|style).*?>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
        # Strip HTML tags
        clean_text = re.sub(r"<[^>]+>", " ", clean_text)
        # Condense whitespace
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        return {
            "status": "success",
            "title": title,
            "content": clean_text[:4000],
            "source_url": url,
            "image_url": "",
            "engine": "httpx_fallback"
        }
    except Exception as e:
        logger.error("HTTP fallback scrape error: %s", e)
        return {"status": "error", "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Scrape web content from URL")
    parser.add_argument("url", help="Target URL to scrape")
    args = parser.parse_args()

    res = scrape_url(args.url)
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
