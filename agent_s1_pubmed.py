#!/usr/bin/env python3
"""
Agent S1: PubMed Scientific Paper Extractor
Target: 100 papers with body composition data
"""

import requests
import json
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

OUTPUT_FILE = Path('data/agents/agent_s1_pubmed.jsonl')
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print("[AGENT S1] Starting PubMed paper extraction...")

# PubMed E-utilities API
BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

SEARCH_TERMS = [
    "body composition weight loss",
    "DEXA scan body fat",
    "muscle gain intervention",
    "before after fitness"
]

collected = []

for term in SEARCH_TERMS:
    print(f"[AGENT S1] Searching: {term}")

    try:
        # Search
        search_url = f"{BASE_URL}/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": term,
            "retmax": 25,
            "retmode": "json",
            "sort": "relevance"
        }

        response = requests.get(search_url, params=search_params, timeout=30)
        search_data = response.json()

        idlist = search_data.get("esearchresult", {}).get("idlist", [])

        for pmid in idlist[:10]:  # Top 10 per term
            try:
                # Fetch details
                fetch_url = f"{BASE_URL}/efetch.fcgi"
                fetch_params = {
                    "db": "pubmed",
                    "id": pmid,
                    "retmode": "xml"
                }

                fetch_response = requests.get(fetch_url, params=fetch_params, timeout=30)

                # Parse basic info (simplified)
                root = ET.fromstring(fetch_response.content)

                article = {
                    "agent": "S1",
                    "source": "pubmed",
                    "pmid": pmid,
                    "title": "",
                    "abstract": "",
                    "has_data": True,
                    "collected_at": datetime.now().isoformat()
                }

                # Try to extract title
                title_elem = root.find('.//ArticleTitle')
                if title_elem is not None:
                    article["title"] = title_elem.text[:200] if title_elem.text else ""

                collected.append(article)

                with open(OUTPUT_FILE, 'a') as f:
                    f.write(json.dumps(article) + '\n')

                time.sleep(0.5)  # Rate limit

            except Exception as e:
                print(f"[AGENT S1] Error fetching {pmid}: {e}")
                continue

        print(f"[AGENT S1] Term '{term}': {len(idlist)} papers found")

    except Exception as e:
        print(f"[AGENT S1] Error searching: {e}")
        continue

print(f"[AGENT S1] COMPLETE: {len(collected)} papers collected")
