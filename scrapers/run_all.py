#!/usr/bin/env python3
"""
PhysiqAI - Launch All Data Collection Agents
Runs Reddit, NHANES, and Bodybuilding.com scrapers
"""

import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent

def run_scraper(name: str, script: str):
    """Run a scraper script"""
    print(f"\n{'='*60}")
    print(f"🚀 LAUNCHING: {name}")
    print(f"{'='*60}\n")

    script_path = BASE_DIR / script

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(BASE_DIR.parent),
            timeout=1800  # 30 min timeout
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"⚠️ {name} timed out")
        return False
    except Exception as e:
        print(f"❌ {name} failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("⚡ PhysiqAI DATA COLLECTION - ALL AGENTS")
    print("="*60)
    print("\nThis will run all Tier 1 scrapers sequentially:")
    print("  1. Reddit (progresspics, Brogress, loseit, GettingShredded)")
    print("  2. NHANES (CDC body composition data)")
    print("  3. Bodybuilding.com (transformation galleries)")
    print("\n" + "="*60 + "\n")

    results = {}

    # Run sequentially to avoid overwhelming network
    scrapers = [
        ("NHANES Downloader", "nhanes_scraper.py"),  # Fastest, do first
        ("Reddit Scraper", "reddit_scraper.py"),
        ("Bodybuilding.com Scraper", "bb_scraper.py"),
    ]

    for name, script in scrapers:
        success = run_scraper(name, script)
        results[name] = "✅ Success" if success else "❌ Failed"

    # Final summary
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    for name, status in results.items():
        print(f"  {status} {name}")
    print("="*60)
    print("\n🎉 Data collection complete! Check Mission Control for results.")
    print("📁 Data saved to: data/collected/")
    print("🖼️ Images in: data/collected/images/")

if __name__ == "__main__":
    main()
