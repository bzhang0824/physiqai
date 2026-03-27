/**
 * Test and demonstration of WeightPhysics engine
 */

const WeightPhysics = require('./weight-physics');

const physics = new WeightPhysics({
  plateauWeeks: 2,
  whooshProbability: 0.15
});

console.log('╔══════════════════════════════════════════════════════════════╗');
console.log('║         PhysiqAI - Weight Physics Engine Demo                ║');
console.log('╚══════════════════════════════════════════════════════════════╝\n');

// ============================================================================
// 1. FAT LOSS CALCULATIONS
// ============================================================================
console.log('📉 FAT LOSS CALCULATIONS');
console.log('───────────────────────────────────────────────────────────────');

const deficits = [250, 500, 750, 1000, 1500];
deficits.forEach(deficit => {
  const rate20bf = physics.calculateFatLossRate(deficit, 20);
  const rate12bf = physics.calculateFatLossRate(deficit, 12);
  console.log(`  ${deficit} cal/day deficit:`);
  console.log(`    • At 20% body fat: ${rate20bf.toFixed(2)} lbs/week`);
  console.log(`    • At 12% body fat: ${rate12bf.toFixed(2)} lbs/week (slower due to metabolic adaptation)`);
});

console.log('\n  Recommended deficit for 1.5 lb/week loss: ' + 
  Math.round(physics.getDeficitForFatLoss(1.5)) + ' cal/day\n');

// ============================================================================
// 2. MUSCLE GAIN CALCULATIONS
// ============================================================================
console.log('💪 MUSCLE GAIN CALCULATIONS');
console.log('───────────────────────────────────────────────────────────────');

const levels = ['novice', 'intermediate', 'advanced', 'elite'];
levels.forEach(level => {
  const rate300 = physics.calculateMuscleGainRate(0, 300, level);
  const rate500 = physics.calculateMuscleGainRate(0, 500, level);
  console.log(`  ${level}:`);
  console.log(`    • 300 cal surplus: ~${rate300.toFixed(2)} lbs/week`);
  console.log(`    • 500 cal surplus: ~${rate500.toFixed(2)} lbs/week`);
});

// ============================================================================
// 3. WATER WEIGHT FLUCTUATIONS
// ============================================================================
console.log('\n💧 WATER WEIGHT FLUCTUATIONS');
console.log('───────────────────────────────────────────────────────────────');

const waterTests = [
  { name: 'Normal day', factors: {} },
  { name: 'High carb + sodium', factors: { carbIntake: 'high', sodiumIntake: 'high' } },
  { name: 'Low carb day', factors: { carbIntake: 'low' } },
  { name: 'Post-workout (inflammation)', factors: { inflammation: 6 } },
  { name: 'With creatine', factors: { creatine: true } },
  { name: 'After alcohol', factors: { alcohol: true, hydration: 'dehydrated' } },
  { name: 'Pre-menstrual (day 25)', factors: { menstrualCycle: 25 } }
];

waterTests.forEach(test => {
  const fluctuation = physics.calculateWaterFluctuation(180, test.factors);
  const sign = fluctuation >= 0 ? '+' : '';
  console.log(`  ${test.name}: ${sign}${fluctuation.toFixed(2)} lbs`);
});

const range = physics.getWaterFluctuationRange(180);
console.log(`\n  Expected daily range for 180 lb person: ${range.min} to +${range.max} lbs`);
console.log(`  Typical fluctuation: ${range.typical.min} to +${range.typical.max} lbs`);

// ============================================================================
// 4. PLATEAU DETECTION
// ============================================================================
console.log('\n📊 PLATEAU DETECTION');
console.log('───────────────────────────────────────────────────────────────');

// Simulate plateau data
function generatePlateauData(weight, days, variance = 0.3) {
  const data = [];
  for (let i = 0; i < days; i++) {
    data.push({
      date: new Date(Date.now() - (days - i) * 86400000).toISOString().split('T')[0],
      weight: weight + (Math.random() - 0.5) * variance
    });
  }
  return data;
}

const noPlateauData = generatePlateauData(180, 21);
// Add slight downward trend
noPlateauData.forEach((d, i) => d.weight -= i * 0.04);

const plateauData = generatePlateauData(175, 21, 0.5); // Nearly flat for 3 weeks

console.log('  Simulated weight loss (normal progress):');
const noPlateauCheck = physics.detectPlateau(noPlateauData);
console.log(`    • In plateau: ${noPlateauCheck.isPlateau}`);
console.log(`    • Trend slope: ${noPlateauCheck.trend.slope.toFixed(4)} lbs/day`);

console.log('\n  Simulated weight loss (stalled):');
const plateauCheck = physics.detectPlateau(plateauData);
console.log(`    • In plateau: ${plateauCheck.isPlateau}`);
console.log(`    • Trend slope: ${plateauCheck.trend.slope.toFixed(4)} lbs/day`);
console.log(`    • Days in plateau: ${plateauCheck.daysInPlateau}`);
if (plateauCheck.message) console.log(`    • Advice: "${plateauCheck.message}"`);

// ============================================================================
// 5. WHOOSH EFFECT
// ============================================================================
console.log('\n🌊 WHOOSH EFFECT');
console.log('───────────────────────────────────────────────────────────────');

const whooshScenarios = [
  { inPlateau: false, days: 0, desc: 'No plateau' },
  { inPlateau: true, days: 10, desc: 'Early plateau (10 days)' },
  { inPlateau: true, days: 14, desc: 'Minimum whoosh threshold (14 days)' },
  { inPlateau: true, days: 21, desc: 'Extended plateau (21 days)' },
  { inPlateau: true, days: 28, desc: 'Long plateau (28 days)' }
];

whooshScenarios.forEach(scenario => {
  const whoosh = physics.calculateWhooshEffect(scenario.inPlateau, scenario.days, 170);
  console.log(`  ${scenario.desc}:`);
  console.log(`    • Probability: ${(whoosh.probability * 100).toFixed(1)}%`);
  console.log(`    • Expected drop if occurs: ${whoosh.expectedDrop.toFixed(2)} lbs`);
});

// ============================================================================
// 6. MOVING AVERAGE
// ============================================================================
console.log('\n📈 MOVING AVERAGE & TREND ANALYSIS');
console.log('───────────────────────────────────────────────────────────────');

// Generate 30 days of realistic data
const testHistory = [];
let testWeight = 185;
for (let i = 0; i < 30; i++) {
  // Base trend: losing 0.2 lbs/day
  testWeight -= 0.2;
  // Add water noise
  const water = (Math.random() - 0.5) * 3;
  // Add weekend fluctuation (slight gain)
  const dayOfWeek = (i % 7);
  const weekendEffect = (dayOfWeek === 5 || dayOfWeek === 6) ? 0.5 : 0;
  
  testHistory.push({
    date: new Date(Date.now() - (30 - i) * 86400000).toISOString().split('T')[0],
    weight: testWeight + water + weekendEffect
  });
}

const withMA = physics.calculateMovingAverage(testHistory);
const trendAnalysis = physics.analyzeTrend(withMA);

console.log('  30-day simulation (target: -1.4 lbs/week):');
console.log(`    • Latest weight: ${withMA[withMA.length - 1].weight.toFixed(2)} lbs`);
console.log(`    • 7-day MA: ${withMA[withMA.length - 1].movingAverage.toFixed(2)} lbs`);
console.log(`    • Trend direction: ${trendAnalysis.direction}`);
console.log(`    • Actual weekly rate: ${trendAnalysis.weeklyRate.toFixed(2)} lbs/week`);

// ============================================================================
// 7. FULL SIMULATION
// ============================================================================
console.log('\n🎯 FULL WEIGHT LOSS SIMULATION (90 days)');
console.log('───────────────────────────────────────────────────────────────');

const simulation = physics.simulateWeightChanges({
  startWeight: 200,
  startDate: new Date(),
  days: 90,
  dailyDeficit: 600,
  dailySurplus: 0,
  trainingIntensity: 'intermediate',
  bodyFatPercent: 25,
  waterFactors: {}
});

const start = simulation[0];
const end = simulation[simulation.length - 1];
const whooshEvents = simulation.filter(d => d.isWhoosh);

console.log(`  Starting: ${start.weight.toFixed(1)} lbs (${start.fatMass.toFixed(1)} lbs fat, ${start.leanMass.toFixed(1)} lbs lean)`);
console.log(`  Ending: ${end.weight.toFixed(1)} lbs (${end.fatMass.toFixed(1)} lbs fat, ${end.leanMass.toFixed(1)} lbs lean)`);
console.log(`  Total lost: ${(start.weight - end.weight).toFixed(1)} lbs`);
console.log(`  Fat lost: ${(start.fatMass - end.fatMass).toFixed(1)} lbs`);
console.log(`  Whoosh events: ${whooshEvents.length}`);
if (whooshEvents.length > 0) {
  whooshEvents.forEach(w => {
    console.log(`    • Day ${w.day}: -${w.whooshDrop.toFixed(1)} lbs drop`);
  });
}

// Show sample days around a whoosh if one exists
if (whooshEvents.length > 0) {
  const whooshDay = whooshEvents[0].day;
  console.log(`\n  📅 Sample days around whoosh (day ${whooshDay}):`);
  for (let d = whooshDay - 2; d <= whooshDay + 2; d++) {
    if (d >= 0 && d < simulation.length) {
      const day = simulation[d];
      const marker = day.isWhoosh ? ' ← WHOOSH!' : '';
      console.log(`    Day ${day.day}: ${day.weight.toFixed(2)} lbs (MA: ${day.movingAverage.toFixed(2)})${marker}`);
    }
  }
}

// ============================================================================
// 8. PROJECTION
// ============================================================================
console.log('\n📅 WEIGHT LOSS PROJECTION');
console.log('───────────────────────────────────────────────────────────────');

const projection = physics.generateProjection(200, 170, 1.2);
console.log(`  Current: ${projection.startWeight} lbs → Goal: ${projection.goalWeight} lbs`);
console.log(`  Rate: ${projection.weeklyLoss} lbs/week`);
console.log(`  Time needed: ${projection.weeksNeeded} weeks (${projection.daysNeeded} days)`);
console.log(`  Estimated goal date: ${projection.estimatedGoalDate}`);
console.log(`  Realistic target: ${projection.isRealistic ? '✅ Yes' : '⚠️ Adjust rate to 0.5-2.0 lbs/week'}`);

console.log('\n═══════════════════════════════════════════════════════════════');
console.log('                    Demo Complete ✨');
console.log('═══════════════════════════════════════════════════════════════\n');
