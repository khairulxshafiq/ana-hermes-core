#!/usr/bin/env python3
"""
Bursa Malaysia (KLSE) Stock Market Client Tool for Hermes Agent.
"""

import argparse
import json
import logging
import sys
import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("bursa_malaysia")

# Common Bursa Malaysia Ticker Mapping
STOCK_MAP = {
    "KLCI": "^KLSE",
    "FBMKLCI": "^KLSE",
    "MAYBANK": "1155.KL",
    "1155": "1155.KL",
    "CIMB": "1023.KL",
    "1023": "1023.KL",
    "PBBANK": "1295.KL",
    "PUBLICBANK": "1295.KL",
    "1295": "1295.KL",
    "TENAGA": "5347.KL",
    "TNB": "5347.KL",
    "5347": "5347.KL",
    "PCHEM": "5183.KL",
    "5183": "5183.KL",
    "IHH": "5225.KL",
    "5225": "5225.KL",
    "YTL": "4677.KL",
    "4677": "4677.KL",
    "YTLPOWR": "6742.KL",
    "6742": "6742.KL",
    "GENTING": "3182.KL",
    "3182": "3182.KL",
    "GENM": "4715.KL",
    "4715": "4715.KL",
    "INARI": "0166.KL",
    "0166": "0166.KL",
    "TOPGLOV": "7113.KL",
    "7113": "7113.KL",
    "AXIATA": "6888.KL",
    "6888": "6888.KL",
    "MAXIS": "6012.KL",
    "6012": "6012.KL",
    "CDB": "6947.KL",
    "CELCOMDIGI": "6947.KL",
    "6947": "6947.KL",
    "MISC": "3816.KL",
    "3816": "3816.KL",
    "NESTLE": "4707.KL",
    "4707": "4707.KL",
    "SIME": "4197.KL",
    "4197": "4197.KL",
    "SDG": "5285.KL",
    "SIMEDARBYPLANT": "5285.KL",
    "5285": "5285.KL",
    "GAMUDA": "5398.KL",
    "5398": "5398.KL",
    "RHBBANK": "1066.KL",
    "1066": "1066.KL",
    "AMBANK": "1015.KL",
    "1015": "1015.KL",
    "HLBANK": "5819.KL",
    "5819": "5819.KL",
}


def resolve_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if cleaned in STOCK_MAP:
        return STOCK_MAP[cleaned]
    if cleaned.startswith("^") or cleaned.endswith(".KL"):
        return cleaned
    if cleaned.isdigit() and len(cleaned) == 4:
        return f"{cleaned}.KL"
    return f"{cleaned}.KL"


def fetch_chart_data(symbol: str, range_str: str = "5d", interval: str = "1d") -> dict:
    target_symbol = resolve_symbol(symbol)
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{target_symbol}?interval={interval}&range={range_str}"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}

    try:
        with httpx.Client(verify=False, timeout=15) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        chart_res = data.get("chart", {}).get("result")
        if not chart_res:
            return {"status": "error", "error": f"No market data found for {symbol}"}

        meta = chart_res[0].get("meta", {})
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")
        change = (price - prev_close) if price and prev_close else 0.0
        change_pct = (change / prev_close * 100) if prev_close else 0.0

        return {
            "status": "success",
            "symbol": meta.get("symbol"),
            "name": meta.get("shortName") or meta.get("longName") or symbol.upper(),
            "currency": meta.get("currency", "MYR"),
            "price": price,
            "previous_close": prev_close,
            "change": round(change, 3),
            "change_pct": f"{change_pct:+.2f}%",
            "high": meta.get("regularMarketDayHigh"),
            "low": meta.get("regularMarketDayLow"),
            "volume": meta.get("regularMarketVolume"),
            "exchange": meta.get("exchangeName", "KLSE"),
        }
    except Exception as e:
        logger.error("Error fetching data for %s: %s", symbol, e)
        return {"status": "error", "error": str(e)}


def get_top_stocks_summary() -> dict:
    top_tickers = ["^KLSE", "MAYBANK", "CIMB", "PBBANK", "TENAGA", "GAMUDA", "YTL", "INARI"]
    results = []
    for ticker in top_tickers:
        res = fetch_chart_data(ticker)
        if res.get("status") == "success":
            results.append({
                "symbol": res.get("symbol"),
                "name": res.get("name"),
                "price": res.get("price"),
                "change": res.get("change"),
                "change_pct": res.get("change_pct"),
            })
    return {"status": "success", "market": "Bursa Malaysia (KLSE)", "stocks": results}


def main():
    parser = argparse.ArgumentParser(description="Bursa Malaysia KLSE Stock Client Tool")
    subparsers = parser.add_subparsers(dest="command")

    # Command: klci
    subparsers.add_parser("klci", help="Get FTSE Bursa Malaysia KLCI Index status")

    # Command: quote
    quote_parser = subparsers.add_parser("quote", help="Get stock price quote")
    quote_parser.add_argument("symbol", help="Stock code or name (e.g. MAYBANK, 1155, CIMB, TENAGA)")

    # Command: top-stocks
    subparsers.add_parser("top-stocks", help="Get summary of top Bursa Malaysia stocks")

    args = parser.parse_args()

    if args.command == "klci":
        res = fetch_chart_data("^KLSE")
        print(json.dumps(res, indent=2))
    elif args.command == "quote":
        res = fetch_chart_data(args.symbol)
        print(json.dumps(res, indent=2))
    elif args.command == "top-stocks":
        res = get_top_stocks_summary()
        print(json.dumps(res, indent=2))
    else:
        # Default fallback: get KLCI & top stocks
        res = get_top_stocks_summary()
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
