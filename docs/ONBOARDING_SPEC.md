# PhysiqAI — Onboarding Input Spec (Maximize Calibration)

> Brian's directive: ask as many well-chosen inputs as possible so the physique morph is as
> deterministic as it can be (never 100%, but maximize signal). Every question below either (a) feeds
> the physiology engine directly, or (b) raises the confidence score. Nothing is asked "just because."
> Grouped into a progressive, low-friction flow (the way Macrofactor / RP / Carbon onboard).

Legend: **[engine]** = direct model input · **[conf]** = improves confidence/CI · *default* = used if skipped.

## Step 1 — About you (identity & body)
1. **Age** **[engine]** — gain/loss rate + recovery modifiers.
2. **Sex (M/F)** **[engine]** — rate, fat distribution, body-fat floors.
3. **Height** (ft/in or cm) **[engine]** — BMR, FFMI ceiling.
4. **Current weight** (lb or kg) **[engine]** — everything.
5. **Body-fat %** — TWO ways, take whichever they give (both → blend):
   - **Body-type picker** (5-6 reference silhouettes per sex → ~8-12% / 14-17% / 18-22% / 25%+) **[engine]** *default*
   - **Optional numeric BF%** (if known: DEXA / calipers / smart scale) **[engine][conf]** (DEXA known → big confidence bump)
6. **Photo upload** — for the visual morph; later, optional AI BF cross-check (flagged as estimate, not a measurement).

## Step 2 — Training history & plan
7. **Years training seriously** **[engine]** → beginner/intermediate/advanced (the single biggest rate factor).
8. **Training days/week** **[engine]** — activity factor (TDEE) + frequency modifier.
9. **Sets per muscle / week** (or simple "low / moderate / high volume") **[engine]** — Schoenfeld volume dose-response.
10. **Training intensity / effort** (going-through-motions ↔ progressive overload every session) **[engine][conf]** — highest-variance factor for intermediates.
11. **Cardio days/week** **[engine]** — TDEE + fat-loss support.
12. **Focus muscle groups** (chest/back/shoulders/arms/legs/core) **[engine]** — regional measurement allocation.

## Step 3 — Nutrition
13. **Goal** — fat loss / muscle gain / recomp / maintenance **[engine]** (drives mode).
14. **Bulk preference** (if gaining): **lean / standard / aggressive** **[engine]** — surplus size (per Brian's Q3).
15. **Daily calories** (if they track; else inferred from goal+TDEE) **[engine]**.
16. **Daily protein** (g, or "high/medium/low") **[engine]** — Morton 1.6 g/kg threshold modifier.
17. **Nutrition tracking method** — weighing / app / eyeballing / none **[conf]** — biggest single confidence driver (30-50% intake error untracked).
18. **Diet quality / adherence** (1-5) **[conf]**.

## Step 4 — Recovery & lifestyle
19. **Sleep hours/night** **[engine]** — Lamon 2021 MPS modifier.
20. **Stress level** (1-10) **[engine]** — bounded recovery modifier.
21. **(Optional) Self-rated genetic potential / how easily you gain** **[engine]** — low/avg/high (small, bounded).

## Step 5 — The ask
22. **Time horizon** — 4wk / 12wk / 6mo / 1yr (or several to compare) **[engine]**.

## Notes
- **Progressive disclosure:** Steps 1-3 are required; Step 4 (recovery) and the optional items can be
  skippable with sensible defaults — each skipped item *lowers the confidence score* (and we tell them
  that, gently: "add your sleep for a more accurate projection").
- **Everything maps to the engine schemas** (`UserProfile / GoalSpec / NutritionSpec / TrainingSpec`) — no orphan questions.
- **Honest framing:** "The more you tell us, the more accurate and personal your projection — but it's a
  science-based estimate, not a guarantee." On-brand with the honesty wedge.
