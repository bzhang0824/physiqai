# PhysiqAI Data Gap Analysis Report
**Generated:** 2026-02-22  
**Dataset:** 5,609 total posts (5,598 Reddit + 11 other sources)

---

## Executive Summary

Our dataset of 5,609 posts has significant gaps that will impact model training quality. Only **32.6%** have complete metadata (gender + age + timeline), and we have severe imbalances in gender representation and transformation types.

---

## 1. Metadata Completeness Analysis

### Overall Statistics
| Field | Count | Percentage |
|-------|-------|------------|
| **Complete metadata** (all 4 fields) | 1,826 | **32.6%** |
| Partial metadata (1-3 fields) | 3,243 | 57.8% |
| Missing all metadata | 540 | 9.6% |

### Individual Field Coverage
| Field | Present | Missing | Coverage |
|-------|---------|---------|----------|
| Gender | 3,203 | 2,406 | **57.1%** |
| Age | 2,710 | 2,899 | **48.3%** |
| Weight info | 2,444 | 3,165 | **43.6%** |
| Height | 2,270 | 3,339 | **40.5%** |
| Timeline | 3,824 | 1,785 | **68.2%** |

---

## 2. Gender Balance Analysis

### Overall Distribution (where known)
| Gender | Count | Percentage |
|--------|-------|------------|
| Male | 1,844 | **57.6%** |
| Female | 1,359 | **42.4%** |
| Unknown | 2,406 | - |

### Gender by Subreddit
| Subreddit | Male % | Female % | Total Posts |
|-----------|--------|----------|-------------|
| r/progresspics | 21% | 79% | 1,482 |
| r/Brogress | 98% | 2% | 747 |
| r/loseit | 94% | 6% | 152 |
| r/gainit | 93% | 7% | 228 |
| r/xxfitness | 80% | 20% | 82 |
| r/BTFC | 50% | 50% | 166 |

**Key Finding:** We have a **42.9% gap** in gender data. r/progresspics is heavily female-skewed (79%), while fitness subreddits like r/Brogress are male-dominated. We need more balanced male data from general fitness subs.

---

## 3. Transformation Type Analysis

| Type | Count | Percentage |
|------|-------|------------|
| **Weight Loss** | 560 | **10.0%** |
| **Muscle Gain** | 122 | **2.2%** |
| **Body Recomp** | 102 | **1.8%** |
| **Unclear/Unclassified** | 4,814 | **86.0%** |

**Key Finding:** Among classified posts, we have a **4.6:1 ratio** of weight loss to muscle gain examples. This severe imbalance will bias our model toward predicting weight loss transformations.

### By Subreddit
- **Weight loss focused:** r/loseit, r/keto, r/intermittentfasting, r/fasting
- **Muscle gain focused:** r/Brogress, r/gainit, r/bodybuilding, r/naturalbodybuilding
- **Mixed:** r/progresspics, r/BTFC

---

## 4. Age Distribution

| Age Range | Count | Percentage |
|-----------|-------|------------|
| < 20 | 178 | 6.6% |
| 20-29 | 1,410 | **52.7%** |
| 30-39 | 795 | **29.7%** |
| 40-49 | 189 | 7.1% |
| 50-59 | 50 | 1.9% |
| 60+ | 56 | 2.1% |

**Key Finding:** Heavily skewed toward 20-39 year olds (82.4%). Very limited data for 40+ age groups.

---

## 5. Timeline Distribution

| Duration | Count | Percentage |
|----------|-------|------------|
| < 3 months | 297 | 7.8% |
| 3-6 months | 435 | 11.4% |
| 6-12 months | 812 | 21.3% |
| 1-2 years | 752 | 19.7% |
| 2+ years | 1,524 | **39.9%** |

**Key Finding:** 40% of transformations are 2+ years, which may not be practical for user expectations.

---

## 6. The 3 Critical Data Gaps

### Gap #1: Metadata Completeness (Priority: CRITICAL)
- **Issue:** Only 32.6% of posts have complete metadata
- **Impact:** Model cannot learn from incomplete examples
- **Missing:** 2,406 posts need gender extraction, 2,899 need age parsing

### Gap #2: Muscle Gain Examples (Priority: HIGH)
- **Issue:** Severe underrepresentation of bulking/muscle gain (2.2% vs 10.0% weight loss)
- **Impact:** Model will be biased toward weight loss predictions
- **Ratio:** 4.6:1 loss-to-gain imbalance

### Gap #3: Age Diversity (Priority: MEDIUM)
- **Issue:** 82.4% of data is ages 20-39; very few 40+ examples
- **Impact:** Poor performance predicting transformations for older users
- **Gap:** Need 3-5x more 40+ age examples for balanced representation

---

## 7. Recommended Scraping Targets

To fill these gaps, prioritize scraping from:

### For More Male Data (Gap #1):
1. **r/fitness** - General fitness, balanced demographics
2. **r/bodyweightfitness** - Male-skewed, good metadata
3. **r/leangains** - Male-focused, detailed progress posts
4. **r/powerlifting** - Male-dominated, strength focus

### For Muscle Gain Examples (Gap #2):
1. **r/gainit** - Dedicated to gaining weight/muscle
2. **r/bodybuilding** - Muscle-focused transformations
3. **r/naturalbodybuilding** - Natural muscle gain progress
4. **r/weightlifting** - Strength gain focus
5. **r/leangains** - Lean muscle building
6. **r/bulkorcut** - Bulking decisions and progress

### For Age Diversity (Gap #3):
1. **r/progresspics** (filter by older ages in titles)
2. **r/fitness30plus** - Specifically 30+ fitness
3. **r/loseit** (older users)
4. Cross-reference with age-specific keywords: "40s", "50s", "60s", "over 40"

### For Better Metadata (All Gaps):
1. **r/BTFC** (Body Transformation Fitness Challenge) - Standardized format
2. Filter posts with patterns like:
   - `M/##/#'#"` or `F/##/#'#"` (gender/age/height)
   - `[### > ### = ###lbs]` (weight change)
   - `(## months/years)` (timeline)

---

## 8. Quick Wins

1. **Improve Parser:** Update regex to catch more gender/age/height patterns (e.g., "T/" for trans, "X/" for unspecified)
2. **Subreddit Prioritization:** Focus scraping on r/gainit, r/bodybuilding, r/fitness before other subs
3. **Age Filtering:** Add keyword filters to target 40+ age posts specifically
4. **Timeline Standardization:** Normalize all timelines to days for consistency

---

## Appendix: Source Breakdown

| Source | Count |
|--------|-------|
| Reddit | 5,598 |
| Kaggle | 6 |
| NHANES | 5 |
| **Total** | **5,609** |

### Top Subreddits
| Subreddit | Posts |
|-----------|-------|
| r/progresspics | 1,482 |
| r/Brogress | 747 |
| r/intermittentfasting | 369 |
| r/fasting | 295 |
| r/uglyduckling | 287 |
| r/GettingShredded | 275 |
| r/StrongCurves | 262 |
| r/FTMFitness | 240 |
| r/gainit | 228 |
| r/veganfitness | 221 |
