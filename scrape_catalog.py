"""Scrape SHL Individual Test Solutions into data/shl_catalog.json.

Run from the project root:
    python scraper/scrape_catalog.py

The SHL site can change its markup, so the parser is intentionally defensive.
It first collects product links from the catalog pages, then visits each product
page and stores only fields that are visible in the catalog/product page.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Dict, Iterable, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.shl.com"
CATALOG = "https://www.shl.com/solutions/products/product-catalog/"
OUT = Path(__file__).resolve().parents[1] / "data" / "shl_catalog.json"
HEADERS = {"User-Agent": "Mozilla/5.0 SHL-assignment-catalog-builder/1.0"}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def soup_for(url: str) -> BeautifulSoup:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def candidate_catalog_urls() -> Iterable[str]:
    # The catalog uses query parameters for pagination and filters on many builds.
    # These URLs cover the common Individual Test Solutions pages without relying
    # on JavaScript execution.
    for start in range(0, 500, 12):
        yield f"{CATALOG}?start={start}&type=1"
        yield f"{CATALOG}?start={start}&solution=individual-test-solutions"


def collect_product_links() -> List[str]:
    links = set()
    for url in candidate_catalog_urls():
        try:
            soup = soup_for(url)
        except Exception:
            continue
        before = len(links)
        for anchor in soup.select("a[href]"):
            href = anchor.get("href", "")
            if "/solutions/products/product-catalog/view/" in href:
                links.add(urljoin(BASE, href.split("#")[0]))
        if len(links) == before and before > 0:
            # Usually means pagination has ended.
            break
        time.sleep(0.2)
    return sorted(links)


def infer_test_type(text: str) -> str:
    low = text.lower()
    mapping = {
        "knowledge": "K",
        "ability": "A",
        "personality": "P",
        "biodata": "B",
        "situational": "S",
        "simulation": "S",
    }
    found = []
    for word, code in mapping.items():
        if word in low and code not in found:
            found.append(code)
    return ",".join(found)


def product_details(url: str) -> Dict:
    soup = soup_for(url)
    title = clean(soup.find("h1").get_text(" ") if soup.find("h1") else "")
    if not title:
        title = clean(soup.title.get_text(" ") if soup.title else url.rstrip("/").split("/")[-1].replace("-", " ").title())

    page_text = clean(soup.get_text(" "))
    description = ""
    for selector in ["meta[name='description']", "meta[property='og:description']"]:
        tag = soup.select_one(selector)
        if tag and tag.get("content"):
            description = clean(tag["content"])
            break
    if not description:
        paras = [clean(p.get_text(" ")) for p in soup.find_all("p")]
        paras = [p for p in paras if len(p) > 40]
        description = paras[0] if paras else ""

    duration = ""
    match = re.search(r"(\d+\s*(?:minutes|minute|min))", page_text, re.I)
    if match:
        duration = match.group(1)

    remote_testing = "Yes" if re.search(r"remote\s*testing|remote", page_text, re.I) else ""
    adaptive_irt = "Yes" if re.search(r"adaptive|IRT", page_text, re.I) else ""
    test_type = infer_test_type(page_text + " " + title)

    keywords = sorted(set(re.findall(r"[A-Za-z][A-Za-z+#.]{2,}", f"{title} {description}".lower())))[:30]
    return {
        "name": title,
        "url": url,
        "test_type": test_type,
        "description": description,
        "duration": duration,
        "remote_testing": remote_testing,
        "adaptive_irt": adaptive_irt,
        "keywords": keywords,
    }


def main() -> None:
    links = collect_product_links()
    print(f"Found {len(links)} product links")
    records = []
    for i, link in enumerate(links, start=1):
        try:
            item = product_details(link)
            records.append(item)
            print(f"[{i}/{len(links)}] {item['name']}")
        except Exception as exc:
            print(f"Skipped {link}: {exc}")
        time.sleep(0.2)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(records)} records to {OUT}")


if __name__ == "__main__":
    main()
