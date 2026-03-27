#!/usr/bin/env python3
"""
PhysiqAI Demo Scraper - Generates realistic sample data
Simulates what actual Reddit scraper would produce
"""

import json
from datetime import datetime
from pathlib import Path

# Sample transformation data (realistic examples)
SAMPLE_POSTS = [
    {
        "id": "1a2b3c4",
        "subreddit": "progresspics",
        "title": "M/25/6'0\" [210lbs > 180lbs = 30lbs] (6 months) Finally hit my goal!",
        "author": "user_fitjourney",
        "score": 1250,
        "url": "https://i.redd.it/sample1.jpg",
        "metadata": {
            "gender": "M",
            "age": 25,
            "height_cm": 183,
            "weight_before_lbs": 210,
            "weight_after_lbs": 180,
            "weight_change_lbs": -30,
            "timeline_value": 6,
            "timeline_unit": "months",
            "timeline_days": 180
        }
    },
    {
        "id": "5d6e7f8",
        "subreddit": "progresspics",
        "title": "F/28/5'4\" [165lbs > 135lbs = 30lbs] (1 year) Consistent gym 4x/week",
        "author": "user_strongmom",
        "score": 892,
        "url": "https://i.redd.it/sample2.jpg",
        "metadata": {
            "gender": "F",
            "age": 28,
            "height_cm": 163,
            "weight_before_lbs": 165,
            "weight_after_lbs": 135,
            "weight_change_lbs": -30,
            "timeline_value": 1,
            "timeline_unit": "years",
            "timeline_days": 365
        }
    },
    {
        "id": "9g0h1i2",
        "subreddit": "progresspics",
        "title": "M/32/5'10\" [155lbs > 175lbs = 20lbs] (8 months) Bulking progress",
        "author": "user_gainztrain",
        "score": 654,
        "url": "https://i.redd.it/sample3.jpg",
        "metadata": {
            "gender": "M",
            "age": 32,
            "height_cm": 178,
            "weight_before_lbs": 155,
            "weight_after_lbs": 175,
            "weight_change_lbs": 20,
            "timeline_value": 8,
            "timeline_unit": "months",
            "timeline_days": 240
        }
    },
    {
        "id": "3j4k5l6",
        "subreddit": "Brogress",
        "title": "M/23/6'2\" [190lbs > 210lbs = 20lbs] (10 months) Lean bulk cycle",
        "author": "user_ironaddic",
        "score": 1103,
        "url": "https://i.redd.it/sample4.jpg",
        "metadata": {
            "gender": "M",
            "age": 23,
            "height_cm": 188,
            "weight_before_lbs": 190,
            "weight_after_lbs": 210,
            "weight_change_lbs": 20,
            "timeline_value": 10,
            "timeline_unit": "months",
            "timeline_days": 300
        }
    },
    {
        "id": "7m8n9o0",
        "subreddit": "progresspics",
        "title": "F/30/5'6\" [145lbs > 125lbs = 20lbs] (5 months) CICO + walking",
        "author": "user_healthylife",
        "score": 445,
        "url": "https://i.redd.it/sample5.jpg",
        "metadata": {
            "gender": "F",
            "age": 30,
            "height_cm": 168,
            "weight_before_lbs": 145,
            "weight_after_lbs": 125,
            "weight_change_lbs": -20,
            "timeline_value": 5,
            "timeline_unit": "months",
            "timeline_days": 150
        }
    },
    {
        "id": "1p2q3r4",
        "subreddit": "progresspics",
        "title": "M/27/5'9\" [220lbs > 175lbs = 45lbs] (1 year) Keto + lifting",
        "author": "user_transformation",
        "score": 2340,
        "url": "https://i.redd.it/sample6.jpg",
        "metadata": {
            "gender": "M",
            "age": 27,
            "height_cm": 175,
            "weight_before_lbs": 220,
            "weight_after_lbs": 175,
            "weight_change_lbs": -45,
            "timeline_value": 1,
            "timeline_unit": "years",
            "timeline_days": 365
        }
    },
    {
        "id": "5s6t7u8",
        "subreddit": "progresspics",
        "title": "F/26/5'5\" [170lbs > 140lbs = 30lbs] (9 months) Best shape of my life!",
        "author": "user_fitfam",
        "score": 778,
        "url": "https://i.redd.it/sample7.jpg",
        "metadata": {
            "gender": "F",
            "age": 26,
            "height_cm": 165,
            "weight_before_lbs": 170,
            "weight_after_lbs": 140,
            "weight_change_lbs": -30,
            "timeline_value": 9,
            "timeline_unit": "months",
            "timeline_days": 270
        }
    },
    {
        "id": "9v0w1x2",
        "subreddit": "Brogress",
        "title": "M/29/6'1\" [165lbs > 195lbs = 30lbs] (14 months) First bulk complete",
        "author": "user_massbuilder",
        "score": 965,
        "url": "https://i.redd.it/sample8.jpg",
        "metadata": {
            "gender": "M",
            "age": 29,
            "height_cm": 185,
            "weight_before_lbs": 165,
            "weight_after_lbs": 195,
            "weight_change_lbs": 30,
            "timeline_value": 14,
            "timeline_unit": "months",
            "timeline_days": 420
        }
    },
    {
        "id": "3y4z5a6",
        "subreddit": "progresspics",
        "title": "F/24/5'3\" [150lbs > 120lbs = 30lbs] (7 months) Started tracking macros",
        "author": "user_fitnessgoals",
        "score": 612,
        "url": "https://i.redd.it/sample9.jpg",
        "metadata": {
            "gender": "F",
            "age": 24,
            "height_cm": 160,
            "weight_before_lbs": 150,
            "weight_after_lbs": 120,
            "weight_change_lbs": -30,
            "timeline_value": 7,
            "timeline_unit": "months",
            "timeline_days": 210
        }
    },
    {
        "id": "7b8c9d0",
        "subreddit": "progresspics",
        "title": "M/31/5'11\" [200lbs > 180lbs = 20lbs] (6 months) Cut completed successfully",
        "author": "user_shredded",
        "score": 534,
        "url": "https://i.redd.it/sample10.jpg",
        "metadata": {
            "gender": "M",
            "age": 31,
            "height_cm": 180,
            "weight_before_lbs": 200,
            "weight_after_lbs": 180,
            "weight_change_lbs": -20,
            "timeline_value": 6,
            "timeline_unit": "months",
            "timeline_days": 180
        }
    }
]

def run_demo():
    """Simulate scraper run with sample data"""

    print("\n" + "="*50)
    print("PhysiqAI - Reddit Transformation Scraper")
    print("(DEMO MODE - Sample Data)")
    print("="*50 + "\n")

    # Create directories
    data_dir = Path('data/reddit_scrapes')
    images_dir = data_dir / 'images'
    metadata_dir = data_dir / 'metadata'

    data_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(exist_ok=True)
    metadata_dir.mkdir(exist_ok=True)

    print("🔍 Scraping r/progresspics...")

    # Add timestamp and image paths
    for post in SAMPLE_POSTS:
        post['scraped_at'] = datetime.now().isoformat()
        post['image_path'] = f"data/reddit_scrapes/images/{post['id']}.jpg"
        post['num_comments'] = post['score'] // 10  # Realistic comment count
        post['selftext'] = ''

        print(f"✓ Scraped: {post['title'][:60]}... (Score: {post['score']})")

    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = metadata_dir / f'scraped_posts_{timestamp}.json'

    with open(output_file, 'w') as f:
        json.dump(SAMPLE_POSTS, f, indent=2)

    print(f"\n💾 Saved {len(SAMPLE_POSTS)} posts to {output_file}")

    # Stats
    stats = {
        'total_posts': 25,
        'valid_posts': len(SAMPLE_POSTS),
        'images_downloaded': len(SAMPLE_POSTS),
        'errors': 0,
        'scrape_date': datetime.now().isoformat()
    }

    stats_file = metadata_dir / f'scrape_stats_{timestamp}.json'
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)

    # Print summary
    print("\n" + "="*50)
    print("📊 SCRAPING SUMMARY")
    print("="*50)
    print(f"Total posts checked: {stats['total_posts']}")
    print(f"Valid posts extracted: {stats['valid_posts']}")
    print(f"Images downloaded: {stats['images_downloaded']}")
    print(f"Errors: {stats['errors']}")
    print("="*50)

    print("\n✅ Scraping complete!")
    print(f"📁 Data saved to: data/reddit_scrapes/")

    # Data analysis
    print("\n" + "="*50)
    print("📈 DATA ANALYSIS")
    print("="*50)

    male_count = sum(1 for p in SAMPLE_POSTS if p['metadata']['gender'] == 'M')
    female_count = len(SAMPLE_POSTS) - male_count

    avg_weight_change = sum(abs(p['metadata']['weight_change_lbs']) for p in SAMPLE_POSTS) / len(SAMPLE_POSTS)
    avg_timeline = sum(p['metadata']['timeline_days'] for p in SAMPLE_POSTS) / len(SAMPLE_POSTS)

    print(f"Gender split: {male_count}M / {female_count}F")
    print(f"Avg weight change: {avg_weight_change:.1f} lbs")
    print(f"Avg timeline: {avg_timeline:.0f} days ({avg_timeline/30:.1f} months)")
    print(f"Age range: {min(p['metadata']['age'] for p in SAMPLE_POSTS)}-{max(p['metadata']['age'] for p in SAMPLE_POSTS)} years")
    print("="*50)

    return output_file

if __name__ == "__main__":
    run_demo()
