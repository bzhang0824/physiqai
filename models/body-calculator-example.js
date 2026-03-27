/**
 * Body Calculator Usage Examples
 * Demonstrates the data pipeline connecting workout data to body changes
 */

const BodyCalculator = require('./body-calculator');
const calc = new BodyCalculator();

console.log('='.repeat(60));
console.log('BODY CALCULATOR - DATA PIPELINE DEMONSTRATION');
console.log('='.repeat(60));

// ============================================
// EXAMPLE 1: Complete Analysis
// ============================================
console.log('\n📊 EXAMPLE 1: Complete User Analysis\n');

const userData = {
  bodyweight: 180,          // lbs
  weeklyVolume: 12500,      // lbs moved per week
  dailyProtein: 160,        // grams
  dailyCalories: 2800,      // kcal
  tdee: 2600,               // maintenance calories
  timeframeDays: 30
};

const analysis = calc.analyze(userData);

console.log('User Profile:');
console.log(`  Weight: ${analysis.inputs.bodyweight} lbs`);
console.log(`  Weekly Volume: ${analysis.inputs.weeklyVolume.toLocaleString()} lbs`);
console.log(`  Daily Protein: ${analysis.inputs.dailyProtein}g`);
console.log(`  Daily Calories: ${analysis.inputs.dailyCalories} kcal (TDEE: ${analysis.inputs.tdee})`);

console.log('\n--- 1. MUSCLE STIMULUS (Volume → Growth Signal) ---');
console.log(`  Volume per lb: ${analysis.stimulus.volumePerLb.toFixed(1)} lbs`);
console.log(`  Stimulus Score: ${(analysis.stimulus.stimulusScore * 100).toFixed(0)}%`);
console.log(`  Category: ${analysis.stimulus.volumeCategory}`);
console.log(`  Gain Potential: ${analysis.stimulus.hasGainPotential ? '✅ YES' : '❌ NO'}`);

console.log('\n--- 2. MUSCLE SYNTHESIS (Protein → Building Capacity) ---');
console.log(`  Protein per lb: ${analysis.synthesis.proteinPerLb}g`);
console.log(`  Synthesis Efficiency: ${(analysis.synthesis.synthesisEfficiency * 100).toFixed(0)}%`);
console.log(`  Category: ${analysis.synthesis.proteinCategory}`);
console.log(`  Building Capacity: ${(analysis.synthesis.buildingCapacity * 100).toFixed(0)}%`);

console.log('\n--- 3. WEIGHT CHANGE (Calories → Body Composition) ---');
console.log(`  Daily Deficit/Surplus: ${analysis.weightChange.dailyDeficit > 0 ? '+' : ''}${analysis.weightChange.dailyDeficit} kcal`);
console.log(`  Phase: ${analysis.weightChange.phase.toUpperCase()}`);
console.log(`  Projected Fat Loss: ${analysis.weightChange.bodyComposition.fatLost} lbs/month`);
console.log(`  Projected Muscle Gain: ${analysis.weightChange.bodyComposition.muscleGained} lbs/month`);
console.log(`  Net Weight Change: ${analysis.weightChange.netWeightChange > 0 ? '+' : ''}${analysis.weightChange.netWeightChange} lbs/month`);

console.log('\n--- 4. RECOMMENDATIONS ---');
analysis.recommendations.forEach((rec, i) => {
  console.log(`  ${i + 1}. [${rec.priority.toUpperCase()}] ${rec.message}`);
  console.log(`     Action: ${rec.action}`);
});

// ============================================
// EXAMPLE 2: Progress Curve Projection
// ============================================
console.log('\n\n📈 EXAMPLE 2: 8-Week Progress Curve\n');

const currentState = { weight: 200, bodyFat: 25 };
const targets = { weight: 185 };
const dailyInputs = {
  dailyCalories: 2200,
  tdee: 2700,
  dailyProtein: 180,
  weeklyVolume: 15000
};

const curve = calc.generateProgressCurve(currentState, targets, dailyInputs, 8);

console.log('Week | Weight | Body Fat | Lean Mass | Phase');
console.log('-'.repeat(55));
curve.forEach(point => {
  console.log(
    `${point.week.toString().padStart(4)} | ` +
    `${point.weight.toFixed(1)} lbs | ` +
    `${point.bodyFat.toFixed(1)}% | ` +
    `${point.leanMass.toFixed(1)} lbs | ` +
    `${point.phase}`
  );
});

// ============================================
// EXAMPLE 3: TDEE Calculation
// ============================================
console.log('\n\n🔥 EXAMPLE 3: TDEE Calculator\n');

const tdeeExamples = [
  { weight: 180, height: 70, age: 30, gender: 'male', activity: 'moderate' },
  { weight: 140, height: 65, age: 25, gender: 'female', activity: 'light' },
  { weight: 220, height: 72, age: 35, gender: 'male', activity: 'very_active' }
];

tdeeExamples.forEach(ex => {
  const tdee = calc.calculateTDEE(ex.weight, ex.height, ex.age, ex.gender, ex.activity);
  console.log(`${ex.gender}, ${ex.weight}lbs, ${ex.activity} activity → TDEE: ${tdee} kcal`);
});

// ============================================
// EXAMPLE 4: Time to Goal Estimate
// ============================================
console.log('\n\n⏱️ EXAMPLE 4: Time to Goal Estimates\n');

const scenarios = [
  { current: 200, target: 180, deficit: 500 },
  { current: 150, target: 165, deficit: -300 },
  { current: 180, target: 170, deficit: 750 }
];

scenarios.forEach(s => {
  const estimate = calc.estimateTimeToGoal(s.current, s.target, s.deficit);
  const direction = s.current > s.target ? 'lose' : 'gain';
  console.log(
    `${s.current} → ${s.target} lbs (${direction} ${Math.abs(s.target - s.current)} lbs) ` +
    `at ${Math.abs(s.deficit)} kcal/day: ~${estimate.weeks} weeks (target date: ${estimate.date})`
  );
});

console.log('\n' + '='.repeat(60));
console.log('BODY CALCULATOR PIPELINE COMPLETE ✓');
console.log('='.repeat(60));
