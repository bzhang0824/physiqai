#!/usr/bin/env python3
"""
PhysiqAI Production Scraper - All Subreddits
Sequential execution (no parallel agents needed)
Uses Pushshift API + web scraping
"""

import requests
import json
import time
import re
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class PhysiqAIProductionScraper:
    def __init__(self):
        self.data_dir = Path('data/production_scrape')
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.stats = {
            'total_attempted': 0,
            'successful_parses': 0,
            'failed_parses': 0,
            'by_subreddit': defaultdict(int)
        }

        self.all_posts = []

    def parse_title(self, title):
        """Extract all metadata from Reddit post title"""
        result = {}

        # Gender (M/F)
        gender_match = re.search(r'\b([MF])[/\\]', title.upper())
        if not gender_match:
            return None
        result["gender"] = gender_match.group(1)

        # Age
        age_match = re.search(r'[MF][/\\](\d{2})[/\\]', title.upper())
        if age_match:
            result["age"] = int(age_match.group(1))

        # Height - feet'inches
        height_ft = re.search(r"(\d+)'(\d+)\"", title)
        if height_ft:
            feet = int(height_ft.group(1))
            inches = int(height_ft.group(2))
            result["height_cm"] = round((feet * 30.48) + (inches * 2.54))
            result["height_imperial"] = f"{feet}'{inches}\""
        else:
            # Height in cm
            height_cm = re.search(r'(\d{3})\s*cm', title, re.IGNORECASE)
            if height_cm:
                result["height_cm"] = int(height_cm.group(1))
                feet = int(result["height_cm"] // 30.48)
                inches = round((result["height_cm"] % 30.48) / 2.54)
                result["height_imperial"] = f"{feet}'{inches}\""

        # Weight before/after - various formats
        # Format: [210lbs > 180lbs = 30lbs]
        weight_match = re.search(r'(\d+)\s*(?:lbs?|pounds?)\s*>\s*(\d+)\s*(?:lbs?|pounds?)', title, re.IGNORECASE)
        if weight_match:
            result["weight_before_lbs"] = int(weight_match.group(1))
            result["weight_after_lbs"] = int(weight_match.group(2))
            result["weight_change_lbs"] = result["weight_after_lbs"] - result["weight_before_lbs"]

            # Calculate BMI if height available
            if "height_cm" in result:
                height_m = result["height_cm"] / 100
                result["bmi_before"] = round(result["weight_before_lbs"] * 0.453592 / (height_m ** 2), 1)
                result["bmi_after"] = round(result["weight_after_lbs"] * 0.453592 / (height_m ** 2), 1)

        # Timeline patterns
        timeline_patterns = [
            (r'(\d+)\s*months?', 'months', 30),
            (r'(\d+)\s*years?', 'years', 365),
            (r'(\d+)\s*weeks?', 'weeks', 7),
            (r'(\d+)\s*days?', 'days', 1)
        ]

        for pattern, unit, days_mult in timeline_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                result["timeline_value"] = int(match.group(1))
                result["timeline_unit"] = unit
                result["timeline_days"] = result["timeline_value"] * days_mult
                break

        return result if result.get("weight_before_lbs") and result.get("timeline_days") else None

    def classify_transformation(self, metadata):
        """Classify transformation type"""
        change = metadata.get("weight_change_lbs", 0)

        if change < -10:
            return "weight_loss"
        elif change > 10:
            return "muscle_gain"
        elif -10 <= change <= 10 and metadata.get("timeline_days", 0) > 180:
            return "recomp"
        else:
            return "both"

    def classify_intensity(self, metadata):
        """Classify intensity level"""
        timeline_days = metadata.get("timeline_days", 180)
        weight_change = abs(metadata.get("weight_change_lbs", 0))

        if timeline_days < 30:
            return "unknown"

        change_per_month = weight_change / (timeline_days / 30)

        if change_per_month > 8:
            return "advanced"
        elif change_per_month > 4:
            return "intermediate"
        else:
            return "beginner"

    def calculate_quality_score(self, post_data):
        """Calculate quality score 1-5"""
        score = 0
        meta = post_data.get("metadata", {})

        # Has demographics
        if all(k in meta for k in ["gender", "age", "height_cm"]):
            score += 1

        # Has weight data
        if all(k in meta for k in ["weight_before_lbs", "weight_after_lbs"]):
            score += 1

        # Has timeline
        if "timeline_days" in meta:
            score += 1

        # High engagement
        if post_data.get("score", 0) > 500:
            score += 1

        # Has image
        url = post_data.get("url", "")
        if url and ("i.redd.it" in url or "i.imgur" in url):
            score += 1

        return score

    def calculate_completeness(self, post_data):
        """Calculate data completeness 0-1"""
        meta = post_data.get("metadata", {})
        fields = ["gender", "age", "height_cm", "weight_before_lbs",
                  "weight_after_lbs", "timeline_days", "bmi_before"]
        filled = sum(1 for f in fields if f in meta)
        return round(filled / len(fields), 2)

    def scrape_pushshift(self, subreddit, limit=100, min_score=50):
        """Scrape subreddit using Pushshift API"""
        print(f"\n🔍 Scraping r/{subreddit}...")

        base_url = "https://api.pullpush.io/reddit/search/submission"
        posts = []

        # Calculate batches
        batch_size = 100
        num_batches = (limit + batch_size - 1) // batch_size

        for batch in range(num_batches):
            params = {
                "subreddit": subreddit,
                "size": min(batch_size, limit - len(posts)),
                "sort": "desc",
                "sort_type": "score",
                "score": f">{min_score}"
            }

            if batch > 0 and posts:
                params["before"] = posts[-1]["created_utc"]

            try:
                response = requests.get(base_url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()

                for post in data.get("data", []):
                    self.stats['total_attempted'] += 1

                    # Parse title
                    parsed = self.parse_title(post.get("title", ""))

                    if parsed:
                        post_data = {
                            "transformation_id": f"{subreddit}_{post['id']}",
                            "source": {
                                "post_id": post["id"],
                                "subreddit": subreddit,
                                "permalink": f"https://reddit.com{post['permalink']}",
                                "scraped_at": datetime.now().isoformat()
                            },
                            "demographics": {
                                "gender": parsed.get("gender"),
                                "age": parsed.get("age"),
                                "height_cm": parsed.get("height_cm"),
                                "height_imperial": parsed.get("height_imperial")
                            },
                            "body_metrics": {
                                "weight_before_lbs": parsed.get("weight_before_lbs"),
                                "weight_after_lbs": parsed.get("weight_after_lbs"),
                                "weight_change_lbs": parsed.get("weight_change_lbs"),
                                "bmi_before": parsed.get("bmi_before"),
                                "bmi_after": parsed.get("bmi_after")
                            },
                            "timeline": {
                                "duration_text": f"{parsed.get('timeline_value')} {parsed.get('timeline_unit')}",
                                "duration_days": parsed.get("timeline_days"),
                                "duration_weeks": parsed.get("timeline_days", 0) // 7,
                                "duration_months": round(parsed.get("timeline_days", 0) / 30, 1)
                            },
                            "media": {
                                "image_urls": [post.get("url", "")],
                                "num_images": 1,
                                "has_gallery": "gallery" in post.get("url", "")
                            },
                            "engagement": {
                                "score": post.get("score", 0),
                                "upvote_ratio": post.get("upvote_ratio", 0),
                                "num_comments": post.get("num_comments", 0)
                            },
                            "text_content": {
                                "title": post.get("title", ""),
                                "selftext": post.get("selftext", "")[:500],
                                "title_parsed": True,
                                "metadata_confidence": 0.92
                            }
                        }

                        # Add ML labels
                        post_data["ml_labels"] = {
                            "transformation_type": self.classify_transformation(parsed),
                            "intensity_level": self.classify_intensity(parsed),
                            "quality_score": self.calculate_quality_score(post_data),
                            "data_completeness": self.calculate_completeness(post_data),
                            "image_quality": "high" if post_data["engagement"]["score"] > 500 else "medium",
                            "has_before_after": True,
                            "pose_consistency": "unknown"
                        }

                        # Only keep quality posts (score >= 3)
                        if post_data["ml_labels"]["quality_score"] >= 3:
                            posts.append(post_data)
                            self.stats['successful_parses'] += 1
                            self.stats['by_subreddit'][subreddit] += 1
                    else:
                        self.stats['failed_parses'] += 1

                print(f"  Batch {batch+1}/{num_batches}: {len(posts)} quality posts so far")
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                print(f"  Error in batch {batch+1}: {e}")
                continue

        print(f"  ✅ r/{subreddit}: {len(posts)} posts collected")
        return posts

    def run_full_scrape(self):
        """Execute full scraping across all target subreddits"""
        print("="*60)
        print("PHYSIQAI PRODUCTION SCRAPER - NIGHTLY RUN")
        print("="*60)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Target subreddits with limits
        targets = [
            ("progresspics", 500),
            ("Brogress", 250),
            ("loseit", 250),
            ("xxfitness", 200),
            ("GettingShredded", 150),
            ("BulkOrCut", 150)
        ]

        all_posts = []

        for subreddit, limit in targets:
            posts = self.scrape_pushshift(subreddit, limit=limit)
            all_posts.extend(posts)
            self.all_posts = all_posts

            # Save incremental progress
            self.save_checkpoint()

        # Final save
        self.save_final_dataset()
        self.generate_report()

        return all_posts

    def save_checkpoint(self):
        """Save progress incrementally"""
        checkpoint_file = self.data_dir / 'checkpoint_latest.json'
        with open(checkpoint_file, 'w') as f:
            json.dump(self.all_posts, f, indent=2)

    def save_final_dataset(self):
        """Save final cleaned dataset"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Main dataset
        final_file = self.data_dir / f'physiqai_dataset_{timestamp}.json'
        with open(final_file, 'w') as f:
            json.dump(self.all_posts, f, indent=2)

        # Stats file
        stats_file = self.data_dir / f'physiqai_stats_{timestamp}.json'
        with open(stats_file, 'w') as f:
            json.dump(self.generate_statistics(), f, indent=2)

        print(f"\n💾 Dataset saved: {final_file}")
        print(f"📊 Stats saved: {stats_file}")

    def generate_statistics(self):
        """Generate dataset statistics"""
        if not self.all_posts:
            return {}

        stats = {
            "total_posts": len(self.all_posts),
            "collection_date": datetime.now().isoformat(),
            "by_subreddit": dict(self.stats['by_subreddit']),
            "gender_distribution": defaultdict(int),
            "age_stats": {"values": [], "min": 0, "max": 0, "avg": 0},
            "weight_change_distribution": {"loss": 0, "gain": 0, "recomp": 0, "both": 0},
            "timeline_stats": {"avg_days": 0, "min_days": 9999, "max_days": 0},
            "quality_distribution": defaultdict(int),
            "transformation_types": defaultdict(int)
        }

        ages = []
        timelines = []

        for post in self.all_posts:
            meta = post.get("demographics", {})
            body = post.get("body_metrics", {})
            timeline = post.get("timeline", {})
            labels = post.get("ml_labels", {})

            # Gender
            stats["gender_distribution"][meta.get("gender", "Unknown")] += 1

            # Age
            if meta.get("age"):
                ages.append(meta["age"])

            # Weight change
            change = body.get("weight_change_lbs", 0)
            if change < -10:
                stats["weight_change_distribution"]["loss"] += 1
            elif change > 10:
                stats["weight_change_distribution"]["gain"] += 1
            elif -10 <= change <= 10:
                stats["weight_change_distribution"]["recomp"] += 1
            else:
                stats["weight_change_distribution"]["both"] += 1

            # Timeline
            days = timeline.get("duration_days", 0)
            if days > 0:
                timelines.append(days)

            # Quality
            quality = labels.get("quality_score", 0)
            stats["quality_distribution"][str(quality)] += 1

            # Transformation type
            ttype = labels.get("transformation_type", "unknown")
            stats["transformation_types"][ttype] += 1

        if ages:
            stats["age_stats"]["min"] = min(ages)
            stats["age_stats"]["max"] = max(ages)
            stats["age_stats"]["avg"] = round(sum(ages) / len(ages), 1)
            stats["age_stats"]["values"] = ages

        if timelines:
            stats["timeline_stats"]["avg_days"] = round(sum(timelines) / len(timelines), 1)
            stats["timeline_stats"]["min_days"] = min(timelines)
            stats["timeline_stats"]["max_days"] = max(timelines)

        # Convert defaultdicts to regular dicts
        stats["gender_distribution"] = dict(stats["gender_distribution"])
        stats["quality_distribution"] = dict(stats["quality_distribution"])
        stats["transformation_types"] = dict(stats["transformation_types"])

        return stats

    def generate_report(self):
        """Print final report"""
        stats = self.generate_statistics()

        print("\n" + "="*60)
        print("📊 FINAL REPORT")
        print("="*60)
        print(f"Total quality transformations: {stats.get('total_posts', 0)}")
        print(f"Success rate: {(self.stats['successful_parses'] / max(self.stats['total_attempted'], 1) * 100):.1f}%")
        print(f"\nBy Subreddit:")
        for sub, count in stats.get('by_subreddit', {}).items():
            print(f"  r/{sub}: {count}")
        print(f"\nGender Split:")
        for gender, count in stats.get('gender_distribution', {}).items():
            print(f"  {gender}: {count}")
        print(f"\nAge Range: {stats.get('age_stats', {}).get('min', 0)}-{stats.get('age_stats', {}).get('max', 0)} (avg: {stats.get('age_stats', {}).get('avg', 0)})")
        print(f"Timeline Range: {stats.get('timeline_stats', {}).get('min_days', 0)}-{stats.get('timeline_stats', {}).get('max_days', 0)} days")
        print(f"\nTransformation Types:")
        for ttype, count in stats.get('transformation_types', {}).items():
            print(f"  {ttype}: {count}")
        print(f"\nQuality Distribution:")
        for quality, count in sorted(stats.get('quality_distribution', {}).items()):
            print(f"  Score {quality}: {count}")
        print("="*60)


if __name__ == "__main__":
    scraper = PhysiqAIProductionScraper()
    results = scraper.run_full_scrape()

    print(f"\n🎉 COMPLETE: {len(results)} transformations ready for ML training!")
