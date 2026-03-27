#!/usr/bin/env python3
"""
PhysiqAI Reddit Scraper
Collects fitness transformation posts from r/progresspics and related subreddits
"""

import praw
import requests
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

# Configuration
SUBREDDITS = ['progresspics', 'Brogress', 'fitness', 'loseit']
POST_LIMIT = 1000  # Max posts to fetch per subreddit
MIN_UPVOTES = 50  # Filter for quality posts

class ProgressPicsScraper:
    def __init__(self, client_id: str, client_secret: str, user_agent: str):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        self.data_dir = Path('data/reddit_scrapes')
        self.images_dir = self.data_dir / 'images'
        self.metadata_dir = self.data_dir / 'metadata'

        # Create directories
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.metadata_dir.mkdir(exist_ok=True)

        self.stats = {
            'total_posts': 0,
            'valid_posts': 0,
            'images_downloaded': 0,
            'errors': 0
        }

    def extract_metadata_from_title(self, title: str) -> Optional[Dict]:
        """
        Extract structured data from post title
        Example: "M/25/6'0" [210lbs > 180lbs = 30lbs] (6 months)"
        """
        metadata = {}

        # Gender
        gender_match = re.search(r'\b([MF])\b', title, re.IGNORECASE)
        if gender_match:
            metadata['gender'] = gender_match.group(1).upper()

        # Age
        age_match = re.search(r'\b(\d{2})\b', title)
        if age_match:
            metadata['age'] = int(age_match.group(1))

        # Height (feet'inches or cm)
        height_match = re.search(r"(\d+)'(\d+)\"", title)
        if height_match:
            feet = int(height_match.group(1))
            inches = int(height_match.group(2))
            metadata['height_cm'] = round((feet * 30.48) + (inches * 2.54))
        else:
            height_cm_match = re.search(r'(\d{3})cm', title)
            if height_cm_match:
                metadata['height_cm'] = int(height_cm_match.group(1))

        # Weight change (lbs or kg)
        weight_match = re.search(r'(\d+)\s*(?:lbs?|pounds?)\s*>\s*(\d+)\s*(?:lbs?|pounds?)', title, re.IGNORECASE)
        if weight_match:
            metadata['weight_before_lbs'] = int(weight_match.group(1))
            metadata['weight_after_lbs'] = int(weight_match.group(2))
            metadata['weight_change_lbs'] = metadata['weight_after_lbs'] - metadata['weight_before_lbs']

        # Timeline
        timeline_patterns = [
            (r'(\d+)\s*months?', 'months'),
            (r'(\d+)\s*years?', 'years'),
            (r'(\d+)\s*weeks?', 'weeks'),
            (r'(\d+)\s*days?', 'days')
        ]

        for pattern, unit in timeline_patterns:
            timeline_match = re.search(pattern, title, re.IGNORECASE)
            if timeline_match:
                value = int(timeline_match.group(1))
                metadata['timeline_value'] = value
                metadata['timeline_unit'] = unit

                # Convert to days for consistency
                conversion = {'days': 1, 'weeks': 7, 'months': 30, 'years': 365}
                metadata['timeline_days'] = value * conversion[unit]
                break

        return metadata if metadata else None

    def download_image(self, url: str, post_id: str) -> Optional[str]:
        """Download image from URL and save locally"""
        try:
            # Handle reddit galleries (skip for now, focus on single images)
            if 'gallery' in url:
                return None

            # Only process direct image links
            if not any(url.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                return None

            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Save image
            extension = url.split('.')[-1].split('?')[0]
            filename = f"{post_id}.{extension}"
            filepath = self.images_dir / filename

            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.stats['images_downloaded'] += 1
            return str(filepath)

        except Exception as e:
            print(f"Error downloading image {url}: {e}")
            self.stats['errors'] += 1
            return None

    def scrape_subreddit(self, subreddit_name: str, limit: int = 100) -> List[Dict]:
        """Scrape posts from a subreddit"""
        print(f"\n🔍 Scraping r/{subreddit_name}...")

        subreddit = self.reddit.subreddit(subreddit_name)
        posts_data = []

        try:
            # Get top posts from the past year
            for post in subreddit.top(time_filter='year', limit=limit):
                self.stats['total_posts'] += 1

                # Filter criteria
                if post.score < MIN_UPVOTES:
                    continue

                if not post.url:
                    continue

                # Extract metadata from title
                metadata = self.extract_metadata_from_title(post.title)

                if not metadata:
                    continue

                # Download image
                image_path = self.download_image(post.url, post.id)

                if not image_path:
                    continue

                # Store post data
                post_data = {
                    'id': post.id,
                    'subreddit': subreddit_name,
                    'title': post.title,
                    'author': str(post.author),
                    'score': post.score,
                    'url': post.url,
                    'image_path': image_path,
                    'created_utc': post.created_utc,
                    'num_comments': post.num_comments,
                    'selftext': post.selftext[:500] if post.selftext else '',  # First 500 chars
                    'metadata': metadata,
                    'scraped_at': datetime.now().isoformat()
                }

                posts_data.append(post_data)
                self.stats['valid_posts'] += 1

                print(f"✓ Scraped: {post.title[:60]}... (Score: {post.score})")

                # Rate limiting
                time.sleep(0.5)

        except Exception as e:
            print(f"Error scraping r/{subreddit_name}: {e}")
            self.stats['errors'] += 1

        return posts_data

    def save_results(self, all_posts: List[Dict]):
        """Save scraped data to JSON file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.metadata_dir / f'scraped_posts_{timestamp}.json'

        with open(output_file, 'w') as f:
            json.dump(all_posts, f, indent=2)

        print(f"\n💾 Saved {len(all_posts)} posts to {output_file}")

        # Also save summary stats
        stats_file = self.metadata_dir / f'scrape_stats_{timestamp}.json'
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def run(self, subreddits: List[str], posts_per_sub: int = 100):
        """Main scraping workflow"""
        print("🚀 PhysiqAI Reddit Scraper Started")
        print(f"📋 Target: {posts_per_sub} posts per subreddit")
        print(f"📍 Subreddits: {', '.join(subreddits)}")

        all_posts = []

        for subreddit in subreddits:
            posts = self.scrape_subreddit(subreddit, limit=posts_per_sub)
            all_posts.extend(posts)

        self.save_results(all_posts)

        # Print summary
        print("\n" + "="*50)
        print("📊 SCRAPING SUMMARY")
        print("="*50)
        print(f"Total posts checked: {self.stats['total_posts']}")
        print(f"Valid posts extracted: {self.stats['valid_posts']}")
        print(f"Images downloaded: {self.stats['images_downloaded']}")
        print(f"Errors: {self.stats['errors']}")
        print("="*50)

        return all_posts


def load_env():
    """Load environment variables from .env file"""
    env_file = Path('.env')
    if not env_file.exists():
        raise FileNotFoundError("⚠️  .env file not found! Please create it with Reddit API credentials.")

    env_vars = {}
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


if __name__ == "__main__":
    print("\n" + "="*50)
    print("PhysiqAI - Reddit Transformation Scraper")
    print("="*50 + "\n")

    try:
        # Load credentials
        env = load_env()

        # Initialize scraper
        scraper = ProgressPicsScraper(
            client_id=env['REDDIT_CLIENT_ID'],
            client_secret=env['REDDIT_CLIENT_SECRET'],
            user_agent=env['REDDIT_USER_AGENT']
        )

        # Run scraper (start with 10 posts for testing)
        posts = scraper.run(
            subreddits=['progresspics'],  # Start with just one subreddit
            posts_per_sub=10  # Test with 10 posts first
        )

        print("\n✅ Scraping complete!")
        print(f"📁 Data saved to: data/reddit_scrapes/")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
