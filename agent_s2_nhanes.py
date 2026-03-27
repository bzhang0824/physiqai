#!/usr/bin/env python3
"""
Agent S2: NHANES Data Downloader
Target: 10,000 sample records
"""

import requests
import json
import pandas as pd
from datetime import datetime
from pathlib import Path
import io

OUTPUT_DIR = Path('data/agents/agent_s2_nhanes')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("[AGENT S2] Starting NHANES data download...")

# NHANES data files (most recent cycles)
NHANES_FILES = {
    "demographics": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/DEMO_J.XPT",
    "body_measures": "https://wwwn.cdc.gov/Nchs/Nhanes/2017-2018/BMX_J.XPT",
    "body_fat": "https://wwwn.cdc.gov/Nchs/Nhanes/2011-2012/DXX_G.XPT"  # DEXA scans
}

collected = 0

for name, url in NHANES_FILES.items():
    print(f"[AGENT S2] Downloading {name}...")

    try:
        response = requests.get(url, timeout=60)

        if response.status_code == 200:
            # Save raw file
            output_file = OUTPUT_DIR / f"nhanes_{name}.xpt"
            with open(output_file, 'wb') as f:
                f.write(response.content)

            print(f"[AGENT S2] Saved: {output_file} ({len(response.content)//1024} KB)")

            # Try to convert to CSV (simplified)
            try:
                # Read with pandas
                df = pd.read_sas(io.BytesIO(response.content), format='xport')
                csv_file = OUTPUT_DIR / f"nhanes_{name}.csv"
                df.to_csv(csv_file, index=False)
                print(f"[AGENT S2] Converted to CSV: {len(df)} records")
                collected += len(df)
            except Exception as e:
                print(f"[AGENT S2] Conversion error: {e}")

    except Exception as e:
        print(f"[AGENT S2] Download error: {e}")

# Create summary
summary = {
    "agent": "S2",
    "source": "nhanes",
    "total_records": collected,
    "files_downloaded": list(NHANES_FILES.keys()),
    "collected_at": datetime.now().isoformat()
}

with open(OUTPUT_DIR / 'summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

print(f"[AGENT S2] COMPLETE: {collected} NHANES records downloaded")
