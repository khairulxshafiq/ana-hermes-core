#!/usr/bin/env python3
"""
gcp_worker_client.py - Client for ANA Hermes to dispatch jobs to Luma GCP Dedicated Worker Fleet
Target: http://<REDACTED_IP>:8000 (GCP Node 'luma-us' via Tailscale mesh)
Supports 4 Engines:
  - Watchdog (A)
  - G-Vault Backup (B)
  - News & Viral Content Vault (C) (All States, Indonesia, 2-Stage On-demand Fetch)
  - Heavy Doc Parser (D) (with automatic local file base64 transfer)
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests

GCP_WORKER_URL = "http://<REDACTED_IP>:8000"

class GCPWorkerClient:
    def __init__(self, base_url: str = GCP_WORKER_URL, timeout: int = 120):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        url = f"{self.base_url}/health"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def watchdog_status(self) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/watchdog/status"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def scrape_viral(self, region: str = "all", limit: int = 15, min_score: int = 4) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/scrape-viral"
        payload = {"region": region, "limit": limit, "min_score": min_score, "save_db": True}
        try:
            resp = requests.post(url, json=payload, timeout=45)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def list_news(self, region: Optional[str] = None, min_score: int = 4, limit: int = 20, search: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/news/list"
        params = {"min_score": min_score, "limit": limit}
        if region:
            params["region"] = region
        if search:
            params["search"] = search
        try:
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def fetch_article(self, article_id: Optional[int] = None, url: Optional[str] = None, summarize: bool = False) -> Dict[str, Any]:
        endpoint = f"{self.base_url}/worker/news/fetch-article"
        payload = {"summarize": summarize}
        if article_id:
            payload["article_id"] = article_id
        if url:
            payload["url"] = url
        try:
            resp = requests.post(endpoint, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def parse_doc(self, file_path: str, summarize: bool = True) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/parse-doc"
        p = Path(file_path)
        payload = {"summarize": summarize}
        if p.exists():
            with open(p, "rb") as f:
                payload["file_base64"] = base64.b64encode(f.read()).decode('utf-8')
                payload["filename"] = p.name
        else:
            payload["file_path"] = file_path

        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def trigger_backup(self) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/backup-gvault"
        try:
            resp = requests.post(url, timeout=120)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def research(self, query: str, urls: Optional[List[str]] = None, depth: str = "summary", timeout_sec: int = 60) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/research"
        payload = {
            "query": query,
            "depth": depth,
            "timeout_sec": timeout_sec
        }
        try:
            resp = requests.post(url, json=payload, timeout=timeout_sec + 10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    def sync_gdrive(self, source_path: str, remote_path: str = "gdrive:backup", dry_run: bool = False) -> Dict[str, Any]:
        url = f"{self.base_url}/worker/sync-gdrive"
        payload = {
            "source_path": source_path,
            "remote_path": remote_path,
            "dry_run": dry_run
        }
        try:
            resp = requests.post(url, json=payload, timeout=180)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"status": "error", "detail": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Luma GCP Worker Client CLI")
    subparsers = parser.add_subparsers(dest="command")

    # Health & Watchdog
    subparsers.add_parser("health", help="Semak status kesihatan Luma GCP Worker")
    subparsers.add_parser("watchdog", help="Semak status semasa Watchdog A")

    # News & Viral (Engine C)
    viral_parser = subparsers.add_parser("viral", help="Sedut berita viral terkini mengikut negeri / wilayah")
    viral_parser.add_argument("--region", type=str, default="all", help="Wilayah: all, nasional, indonesia, kelantan, selangor, perak, johor, dll")
    viral_parser.add_argument("--limit", type=int, default=10, help="Bilangan artikel")
    viral_parser.add_argument("--min-score", type=int, default=4, help="Skor viral minima (1-10)")

    list_parser = subparsers.add_parser("news-list", help="Senaraikan berita dalam vault simpanan Luma")
    list_parser.add_argument("--region", type=str, default=None, help="Filter ikut wilayah")
    list_parser.add_argument("--limit", type=int, default=15, help="Bilangan rekod")
    list_parser.add_argument("--search", type=str, default=None, help="Carian kata kunci tajuk")

    fetch_parser = subparsers.add_parser("fetch-article", help="Ambil isi artikel penuh on-demand & cadang angle kandungan")
    fetch_parser.add_argument("--id", type=int, default=None, help="ID artikel dalam SQLite vault")
    fetch_parser.add_argument("--url", type=str, default=None, help="URL artikel terus")
    fetch_parser.add_argument("--summarize", action="store_true", help="Jana ringkasan AI dan 3 angle video/posting")

    # Parse Doc (Engine D)
    doc_parser = subparsers.add_parser("parse", help="Analisis dokumen berat PDF / Excel melalui GCP")
    doc_parser.add_argument("--file", type=str, required=True, help="Laluan fail PDF/Excel")
    doc_parser.add_argument("--no-summary", action="store_true", help="Langkau sintesis AI ringkasan")

    # Backup G-Vault (Engine B)
    subparsers.add_parser("backup", help="Cetuskan sandaran SQLite pangkalan data ke G-Vault GCP")

    # Research
    res_parser = subparsers.add_parser("research", help="Laksanakan penyelidikan selari & sintesis teks")
    res_parser.add_argument("query", type=str, help="Topik penyelidikan")
    res_parser.add_argument("--depth", choices=["summary", "deep"], default="summary", help="Kedalaman analisis")
    res_parser.add_argument("--timeout", type=int, default=60, help="Had masa (saat)")

    # Sync GDrive
    sync_parser = subparsers.add_parser("sync", help="Laksanakan rclone sync ke Google Drive")
    sync_parser.add_argument("--source", type=str, default="/home/khairulshafiq/antigravity-workspace/AnaFile", help="Laluan direktori sumber tempatan di GCP")
    sync_parser.add_argument("--remote", type=str, default="gdrive:backup", help="Laluan remote GDrive")
    sync_parser.add_argument("--dry-run", action="store_true", help="Jalankan simulasi tanpa perubahan")

    args = parser.parse_args()
    client = GCPWorkerClient()

    if args.command == "health":
        print(json.dumps(client.health(), indent=2, ensure_ascii=False))
    elif args.command == "watchdog":
        print(json.dumps(client.watchdog_status(), indent=2, ensure_ascii=False))
    elif args.command == "viral":
        res = client.scrape_viral(region=args.region, limit=args.limit, min_score=args.min_score)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "news-list":
        res = client.list_news(region=args.region, limit=args.limit, search=args.search)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "fetch-article":
        res = client.fetch_article(article_id=args.id, url=args.url, summarize=args.summarize)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "parse":
        res = client.parse_doc(file_path=args.file, summarize=not args.no_summary)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "backup":
        print(json.dumps(client.trigger_backup(), indent=2, ensure_ascii=False))
    elif args.command == "research":
        res = client.research(query=args.query, depth=args.depth, timeout_sec=args.timeout)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif args.command == "sync":
        res = client.sync_gdrive(source_path=args.source, remote_path=args.remote, dry_run=args.dry_run)
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
