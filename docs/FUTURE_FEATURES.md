# PhysiqAI — Future Features & Ideas

*Ideas to implement post-MVP*

---

## Reverse Engineering Feature (from BZ feedback)

### Concept
Instead of: "Here's what you'll look like with your current plan"
Also offer: "Here's the plan to get the physique you want"

### Flow
```
User shows desired outcome → We analyze the delta → 
We recommend training plan to get there
```

### Implementation Ideas
1. User uploads "goal physique" photo (themselves transformed, or inspiration)
2. We analyze what's different (more chest, less body fat, bigger shoulders)
3. We reverse-calculate: "To get this in 12 weeks, you'd need..."
   - Training: 5x/week, chest focus, high volume
   - Nutrition: 300 cal surplus, 1.8g/kg protein
   - Timeline: Achievable in X weeks (or "this would take 6+ months")

### Value Proposition
- Bridges visualization to action
- Answers "HOW do I get there?" not just "what will I look like?"
- Creates stickiness (they come back to track progress toward goal)

### Technical Considerations
- Need to assess feasibility (is the goal physique achievable naturally?)
- Cap at FFMI limits
- Warn if goal is unrealistic for timeframe

### Priority
Post-MVP, after core transformation engine is solid.

---

## Iterative Refinement → Plan Adjustment (from BZ feedback)

### Concept
If user adjusts their projected result (e.g., "I want more arm development"), the system should suggest training plan changes to match.

### Flow
```
Original plan: PPL, balanced focus
User adjusts: "More arms"
System suggests: "To achieve this, add 4 sets of bicep isolation 2x/week"
```

### Why This Matters
- Connects visualization to action
- Makes the tool prescriptive, not just descriptive
- Increases engagement (back-and-forth dialogue)

---

## Other Ideas Captured

### Time-Lapse Video Generation
- Morph from current → projected
- More shareable than static images
- Tech: Runway ML, similar tools

### "What If" Scenarios
- Compare different plans side-by-side
- "What if I trained 3x vs 5x per week?"
- "What if I cut instead of bulked?"

### Progress Tracking Integration
- User returns with new photo
- Compare actual progress to projection
- Adjust future projections based on real data
- "Living Avatar" concept

### Genetics Estimation
- Frame size analysis
- Predict natural ceiling
- "Based on your structure, max potential is approximately..."

### Supplement/Nutrition Tie-In
- After projection, show nutrition targets
- "To maximize this, you need X protein, Y calories"

---

*Last updated: 2026-02-03*
