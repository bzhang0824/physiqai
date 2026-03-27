# Implementation Notes

*Tracking how research integrates into the system*

## Research → Code Integration

### Physiology Sources Document
- Location: `docs/PHYSIOLOGY_SOURCES.md`
- Status: Complete (912 lines, 15 peer-reviewed sources)
- Integration: Formulas will be implemented in `lib/physiology.ts`

### Key Formulas to Implement

1. **Monthly Muscle Gain** (Aragon/Helms)
   - Beginner: 1.0-1.5% bodyweight
   - Intermediate: 0.5-1.0%
   - Advanced: 0.25-0.5%

2. **Modifiers** (all research-backed)
   - Gender: 0.5x for women (absolute), 1.0x relative
   - Age: -1% per year after 30
   - Sleep: -18% if poor (Lamon 2021)
   - Frequency: 2x/week optimal (Schoenfeld 2016)
   - Volume: 10+ sets/muscle/week optimal

3. **Fat Loss Rate** (Garthe 2011)
   - Optimal: 0.7% bodyweight/week
   - Faster = muscle loss risk

### Prompt Generation
- Prompts should include specific muscle gain amounts
- Amounts derived from physiology calculations
- Regional distribution based on focus areas

### User-Facing Explanations
- Every projection cites its source
- PMID/DOI links available in "detailed" view
- Confidence score reflects input quality + research certainty

---

*Last updated: 2026-02-03*
