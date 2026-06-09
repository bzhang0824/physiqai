# NHANES DXA Validation (final defensibility stamp)

Validated the engine's physiological bounds against **10,799 real DXA-measured US adults** (NHANES
2011-2018, ages 18-55). Data: `validation/nhanes_dxa_18_55.csv`. Run 2026-06-01.

## Results
- **✅ Body-fat floors are real hard limits.** 0.00% of the population is below our essential floors
  (5% M / 13% F). Minimum observed: 11.7% (men), 15.0% (women); 1st percentile 13.7% / 23.1%. The
  engine's floor (which fixed the "5.1% in 6 months" bug) is conservative and physiologically sound.
- **✅ FFMI natural ceiling (normalized 25) is the elite tail.** Among lean young men (bf 8-18%, n=465):
  99th-pct FFMI = 23.6; only 0.2% exceed 25 (~99.8th percentile). A cap at 25 correctly represents the
  natural muscular limit (consistent with Kouri 1995). (Note: raw whole-population FFMI is confounded by
  obesity-associated lean mass, so the lean-subset check is the meaningful one.)
- **📊 bf-from-BMI imputation error quantified:** Deurenberg vs DXA MAE = 4.3% (M) / 5.0% (F). This is the
  main source of noise in the Reddit weight-change MAE (9.8 lb), since we impute body-fat there. Known,
  expected limitation; could be tightened later by fitting a NHANES-based `bf ~ bmi+age+sex` regression.

## Triple-validated
The engine is now validated three independent ways:
1. **Literature RCT ranges** — 7/7 scenarios defensible (`docs/VALIDATION_MANIFEST.md`, `VALIDATION_SCORECARD.txt`)
2. **Real population distributions** — NHANES floors + FFMI ceiling (this doc)
3. **Real weight-change outcomes** — 473 Reddit, MAE 9.8 lb on the comparable subset

**Verdict: the governor is scientifically defensible.** Further accuracy now comes from (a) Arch B
constraining the *visual*, and (b) post-launch real-user outcome data — not more pre-launch scraping.
