# PhysiqAI Data Summary Report
## Generated: 2026-02-22

### Overview
- **Total posts in database:** 5,156
- **Posts with weight_change data:** 1,270
- **Percentage with weight_change:** 24.6%

### Key Findings

1. **Data Coverage**: About 1 in 4 posts (24.6%) have explicit weight_change data extracted from the metadata.

2. **Weight Change Range**: The data shows both weight loss (negative values) and weight gain (positive values):
   - Largest weight loss: -685 lbs
   - Largest weight gain: +350 lbs
   - Most common: Weight loss transformations

3. **Data Sources**: All posts with weight_change appear to be from Reddit's r/progresspics subreddit, which is the primary source for transformation data.

4. **Data Quality**: The posts include:
   - weight_before and weight_after values
   - Calculated weight_change values
   - Timeline information (where available)
   - Gender and age metadata (where extractable)

### Sample Entries with Weight Change:
| ID | Weight Change | Source |
|----|---------------|--------|
| reddit_1n57tv9 | -97 lbs | reddit |
| reddit_1onxhgk | -193 lbs | reddit |
| reddit_1l18hzi | -91 lbs | reddit |
| reddit_1joaj0k | -50 lbs | reddit |
| reddit_1m37lzd | -100 lbs | reddit |

### Recommendations
- Consider enriching the remaining ~75% of posts with weight_change data through better title parsing
- The NHANES datasets (nhanes_BMX_L, nhanes_BMX_J, etc.) don't have weight_change in metadata but contain raw body measurement data
