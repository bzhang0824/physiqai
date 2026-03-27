/**
 * PhysiqAI - Weight Physics Engine
 * Realistic weight change algorithms for body transformation simulation
 */

class WeightPhysics {
  constructor(options = {}) {
    // Configuration
    this.fatCaloriesPerLb = 3500;      // Classic estimate (revised science suggests ~3800-4200)
    this.muscleCaloriesPerLb = 2500;   // Less dense than fat, requires protein synthesis
    this.waterPerGlycogenLb = 3;       // Each lb of glycogen binds ~3 lbs water
    this.glycogenCapacity = 0.5;       // Max ~0.5-1% body weight in glycogen storage
    
    // Water weight parameters
    this.maxDailyWaterFluctuation = options.maxDailyWaterFluctuation || 3; // ±3 lbs
    this.waterVolatility = options.waterVolatility || 0.7; // Base daily noise
    
    // Plateau detection
    this.plateauWeeks = options.plateauWeeks || 2;
    this.plateauThreshold = options.plateauThreshold || 0.5; // lbs variation threshold
    
    // Whoosh effect
    this.whooshProbability = options.whooshProbability || 0.15; // 15% chance after plateau
    this.whooshMagnitude = options.whooshMagnitude || { min: 1.5, max: 4 };
    
    // Moving average configuration
    this.maWindowDays = options.maWindowDays || 7; // 7-day moving average
  }

  // ============================================================================
  // FAT LOSS CALCULATIONS
  // ============================================================================
  
  /**
   * Calculate expected fat loss rate based on caloric deficit
   * @param {number} dailyDeficit - Daily caloric deficit in calories
   * @param {number} currentBodyFat - Current body fat percentage (0-100)
   * @returns {number} Expected fat loss in lbs/week
   */
  calculateFatLossRate(dailyDeficit, currentBodyFat = 20) {
    // Theoretical max: 1 lb fat per 3500 cal deficit
    const theoreticalMax = (dailyDeficit * 7) / this.fatCaloriesPerLb;
    
    // Realistic constraints based on body fat percentage
    // Higher body fat = can sustain higher deficits
    // Lower body fat = adaptive thermogenesis kicks in
    let efficiency = 1.0;
    
    if (currentBodyFat < 10) {
      efficiency = 0.6; // Very lean - metabolic adaptation significant
    } else if (currentBodyFat < 15) {
      efficiency = 0.75;
    } else if (currentBodyFat < 20) {
      efficiency = 0.85;
    } else if (currentBodyFat < 25) {
      efficiency = 0.92;
    } else {
      efficiency = 0.95; // Higher body fat = better deficit tolerance
    }
    
    // Cap at realistic maximums
    const realisticMax = Math.min(theoreticalMax * efficiency, 2.5); // Hard cap at 2.5 lbs/week
    const realisticMin = Math.max(realisticMax, 0); // Can't gain fat in deficit
    
    return Math.min(Math.max(realisticMin, 0.5), 2.0); // Clamp to 0.5-2.0 lbs/week
  }

  /**
   * Get recommended deficit for target fat loss rate
   * @param {number} targetLossLbsPerWeek - Target weekly fat loss
   * @returns {number} Recommended daily caloric deficit
   */
  getDeficitForFatLoss(targetLossLbsPerWeek) {
    const clampedLoss = Math.max(0.5, Math.min(2.0, targetLossLbsPerWeek));
    return (clampedLoss * this.fatCaloriesPerLb) / 7;
  }

  // ============================================================================
  // MUSCLE GAIN CALCULATIONS
  // ============================================================================
  
  /**
   * Calculate expected muscle gain rate based on training status and surplus
   * @param {number} trainingYears - Years of consistent training
   * @param {number} dailySurplus - Daily caloric surplus
   * @param {string} trainingIntensity - 'novice', 'intermediate', 'advanced'
   * @returns {number} Expected muscle gain in lbs/week
   */
  calculateMuscleGainRate(trainingYears = 0, dailySurplus = 300, trainingIntensity = 'intermediate') {
    // Natural muscle gain limits (Lyle McDonald / Alan Aragon models)
    const gainPotential = {
      novice: { rate: 0.5, period: 'first year' },      // ~25 lbs/year
      intermediate: { rate: 0.3, period: 'years 2-3' }, // ~12-15 lbs/year
      advanced: { rate: 0.15, period: 'years 4+' },     // ~6 lbs/year or less
      elite: { rate: 0.05, period: '5+ years' }         // Minimal gains
    };
    
    let baseRate = gainPotential[trainingIntensity]?.rate || 0.25;
    
    // Adjust based on surplus adequacy
    // Minimum ~200 cal surplus needed for any significant gain
    // Optimal ~300-500 cal for most
    // Diminishing returns above ~500 cal (more fat gain)
    let surplusMultiplier = 0;
    if (dailySurplus >= 200) {
      surplusMultiplier = Math.min(1.0, (dailySurplus - 100) / 300);
    }
    
    // Apply multiplier and genetic variance (±20%)
    const geneticVariance = 0.8 + (Math.random() * 0.4); // 0.8 to 1.2
    const adjustedRate = baseRate * surplusMultiplier * geneticVariance;
    
    return Math.min(Math.max(adjustedRate, 0), 0.5); // Clamp to 0-0.5 lbs/week
  }

  /**
   * Get recommended surplus for target muscle gain
   * @param {number} targetGainLbsPerWeek - Target weekly muscle gain
   * @returns {number} Recommended daily caloric surplus
   */
  getSurplusForMuscleGain(targetGainLbsPerWeek) {
    const clampedGain = Math.max(0.25, Math.min(0.5, targetGainLbsPerWeek));
    return (clampedGain * this.muscleCaloriesPerLb) / 7 + 100; // +100 for synthesis overhead
  }

  // ============================================================================
  // WATER WEIGHT FLUCTUATIONS
  // ============================================================================
  
  /**
   * Generate realistic daily water weight fluctuation
   * @param {number} bodyWeight - Current body weight in lbs
   * @param {Object} factors - Factors affecting water retention
   * @returns {number} Water weight change in lbs (can be positive or negative)
   */
  calculateWaterFluctuation(bodyWeight, factors = {}) {
    const {
      sodiumIntake = 'normal',      // 'low', 'normal', 'high'
      carbIntake = 'normal',        // 'low', 'normal', 'high'
      hydration = 'normal',         // 'dehydrated', 'normal', 'overhydrated'
      menstrualCycle = null,        // Day of cycle (0-28), null if N/A
      inflammation = 0,             // 0-10 scale (workout soreness, injury, etc)
      creatine = false,             // Taking creatine (increases intracellular water)
      alcohol = false               // Alcohol consumption (dehydration)
    } = factors;
    
    // Base daily noise (± up to 3 lbs)
    let waterChange = (Math.random() - 0.5) * 2 * this.maxDailyWaterFluctuation * this.waterVolatility;
    
    // Sodium effects (can add 2-4 lbs temporarily)
    const sodiumEffects = { low: -1, normal: 0, high: 1.5 };
    waterChange += sodiumEffects[sodiumIntake] || 0;
    
    // Carb/glycogen effects (1g glycogen binds ~3g water)
    // High carb day can add 1-3 lbs, low carb can drop 2-5 lbs quickly
    const carbEffects = { low: -2.5, normal: 0, high: 2 };
    waterChange += carbEffects[carbIntake] || 0;
    
    // Hydration status
    const hydrationEffects = { dehydrated: -1.5, normal: 0, overhydrated: 1 };
    waterChange += hydrationEffects[hydration] || 0;
    
    // Menstrual cycle water retention (for women)
    if (menstrualCycle !== null) {
      // Peak water retention ~week before period (days 21-28)
      if (menstrualCycle >= 21 && menstrualCycle <= 28) {
        waterChange += 1 + Math.random() * 2; // +1 to +3 lbs
      } else if (menstrualCycle >= 1 && menstrualCycle <= 5) {
        waterChange -= 0.5 + Math.random(); // Drop after period starts
      }
    }
    
    // Inflammation (workout recovery, injury)
    waterChange += (inflammation / 10) * 2; // Up to +2 lbs from inflammation
    
    // Creatine loading (can add 2-5 lbs water weight)
    if (creatine) {
      waterChange += 2 + Math.random() * 2;
    }
    
    // Alcohol (dehydration next day)
    if (alcohol) {
      waterChange -= 0.5 + Math.random();
    }
    
    return waterChange;
  }

  /**
   * Get expected water weight range for a given body weight
   * @param {number} bodyWeight - Body weight in lbs
   * @returns {Object} Min and max expected water fluctuation
   */
  getWaterFluctuationRange(bodyWeight) {
    return {
      min: -this.maxDailyWaterFluctuation,
      max: this.maxDailyWaterFluctuation,
      typical: {
        min: -2,
        max: 2
      }
    };
  }

  // ============================================================================
  // PLATEAU DETECTION
  // ============================================================================
  
  /**
   * Detect if the user is in a weight plateau
   * Uses moving average to filter out water weight noise
   * @param {Array} weightHistory - Array of {date, weight, movingAverage} objects (oldest first)
   * @param {boolean} useMA - Whether to use moving average (default: true)
   * @returns {Object} Plateau status and details
   */
  detectPlateau(weightHistory, useMA = true) {
    if (!weightHistory || weightHistory.length < this.plateauWeeks * 7) {
      return {
        isPlateau: false,
        daysInPlateau: 0,
        confidence: 0,
        trend: null
      };
    }
    
    // Get last N days
    const recentData = weightHistory.slice(-this.plateauWeeks * 7);
    // Use moving average if available, otherwise fall back to raw weight
    const weights = recentData.map(d => useMA && d.movingAverage !== undefined ? d.movingAverage : d.weight);
    
    // Calculate trend using linear regression
    const trend = this.calculateTrend(weights);
    
    // Check if trend is essentially flat
    const totalChange = Math.abs(weights[weights.length - 1] - weights[0]);
    const avgWeight = weights.reduce((a, b) => a + b, 0) / weights.length;
    
    // Plateau: less than 0.5 lb change over 2+ weeks AND slope near zero
    const isPlateau = totalChange < this.plateauThreshold && Math.abs(trend.slope) < 0.03;
    
    // Calculate confidence based on data consistency
    const variance = this.calculateVariance(weights);
    const confidence = isPlateau ? Math.min(1, 1 - (variance / 20)) : 0;
    
    return {
      isPlateau,
      daysInPlateau: isPlateau ? this.plateauWeeks * 7 : 0,
      confidence,
      trend,
      totalChange,
      avgWeight,
      message: isPlateau ? this.getPlateauMessage(trend.slope) : null
    };
  }

  /**
   * Get encouraging/informative message about plateau
   */
  getPlateauMessage(trendSlope) {
    const messages = [
      "Weight plateaus are normal! Your body may be recomposing (losing fat while gaining muscle).",
      "Consider checking: sodium intake, sleep quality, stress levels, and measuring tape progress.",
      "A whoosh effect may be coming - sudden drops often follow plateaus.",
      "If plateau continues 3+ weeks, consider a small adjustment to calories or activity."
    ];
    return messages[Math.floor(Math.random() * messages.length)];
  }

  // ============================================================================
  // WHOOSH EFFECT
  // ============================================================================
  
  /**
   * Simulate potential whoosh effect after plateau
   * @param {boolean} inPlateau - Whether currently in plateau
   * @param {number} daysInPlateau - How many days in plateau
   * @param {number} bodyWeight - Current body weight
   * @returns {Object} Whoosh prediction
   */
  calculateWhooshEffect(inPlateau, daysInPlateau, bodyWeight) {
    if (!inPlateau || daysInPlateau < 14) {
      return {
        willWhoosh: false,
        expectedDrop: 0,
        probability: 0
      };
    }
    
    // Probability increases with plateau duration
    const baseProb = this.whooshProbability;
    const durationMultiplier = Math.min(2, 1 + (daysInPlateau - 14) / 14);
    const probability = Math.min(0.5, baseProb * durationMultiplier);
    
    // Magnitude varies
    const expectedDrop = this.whooshMagnitude.min + 
      Math.random() * (this.whooshMagnitude.max - this.whooshMagnitude.min);
    
    return {
      willWhoosh: Math.random() < probability,
      expectedDrop,
      probability,
      explanation: "Fat cells release fat but temporarily fill with water. Eventually they collapse (the 'whoosh')."
    };
  }

  /**
   * Trigger a whoosh effect (for simulation purposes)
   * @param {number} fatLostDuringPlateau - Actual fat lost during plateau period
   * @returns {number} Sudden weight drop amount
   */
  triggerWhoosh(fatLostDuringPlateau) {
    // Whoosh typically releases water equal to or greater than fat lost during plateau
    const whooshMultiplier = 1 + (Math.random() * 0.5); // 1x to 1.5x
    return fatLostDuringPlateau * whooshMultiplier;
  }

  // ============================================================================
  // MOVING AVERAGE
  // ============================================================================
  
  /**
   * Calculate moving average for weight data
   * @param {Array} weightHistory - Array of {date, weight} objects
   * @param {number} windowDays - Window size (default: 7 days)
   * @returns {Array} Array of {date, weight, ma} objects
   */
  calculateMovingAverage(weightHistory, windowDays = this.maWindowDays) {
    if (!weightHistory || weightHistory.length === 0) return [];
    
    const result = [];
    
    for (let i = 0; i < weightHistory.length; i++) {
      const windowStart = Math.max(0, i - windowDays + 1);
      const window = weightHistory.slice(windowStart, i + 1);
      const weights = window.map(d => d.weight);
      const ma = weights.reduce((a, b) => a + b, 0) / weights.length;
      
      result.push({
        ...weightHistory[i],
        movingAverage: parseFloat(ma.toFixed(2)),
        trend: window.length >= 7 ? this.calculateTrend(weights).slope : null
      });
    }
    
    return result;
  }

  /**
   * Get trend direction and rate from moving average
   * @param {Array} maData - Data with moving averages
   * @returns {Object} Trend analysis
   */
  analyzeTrend(maData) {
    if (!maData || maData.length < 14) {
      return { direction: 'insufficient_data', rate: 0 };
    }
    
    const recent = maData.slice(-7);
    const older = maData.slice(-14, -7);
    
    const recentAvg = recent.reduce((a, b) => a + b.movingAverage, 0) / recent.length;
    const olderAvg = older.reduce((a, b) => a + b.movingAverage, 0) / older.length;
    
    const diff = recentAvg - olderAvg;
    const weeklyRate = diff; // Since comparing 7-day periods
    
    let direction = 'stable';
    if (weeklyRate < -0.25) direction = 'losing';
    if (weeklyRate > 0.25) direction = 'gaining';
    
    return {
      direction,
      weeklyRate: parseFloat(weeklyRate.toFixed(2)),
      dailyRate: parseFloat((weeklyRate / 7).toFixed(3)),
      recentAvg: parseFloat(recentAvg.toFixed(2)),
      olderAvg: parseFloat(olderAvg.toFixed(2))
    };
  }

  // ============================================================================
  // COMPLETE WEIGHT SIMULATION
  // ============================================================================
  
  /**
   * Simulate realistic weight changes over time
   * @param {Object} params - Simulation parameters
   * @returns {Array} Daily weight data
   */
  simulateWeightChanges(params) {
    const {
      startWeight,
      startDate = new Date(),
      days = 90,
      dailyDeficit = 500,
      dailySurplus = 0,
      trainingIntensity = 'intermediate',
      bodyFatPercent = 20,
      waterFactors = {}
    } = params;
    
    const results = [];
    let currentWeight = startWeight;
    let fatMass = startWeight * (bodyFatPercent / 100);
    let leanMass = startWeight - fatMass;
    let inPlateau = false;
    let plateauDays = 0;
    let hiddenFatLoss = 0; // Fat lost but masked by water
    
    const startTime = new Date(startDate).getTime();
    
    for (let day = 0; day < days; day++) {
      const currentDate = new Date(startTime + day * 24 * 60 * 60 * 1000);
      
      // Calculate actual tissue changes
      let dailyFatChange = 0;
      let dailyMuscleChange = 0;
      
      if (dailyDeficit > 0) {
        // Fat loss (slightly less efficient than theoretical)
        const weeklyFatLoss = this.calculateFatLossRate(dailyDeficit, (fatMass / currentWeight) * 100);
        dailyFatChange = -(weeklyFatLoss / 7);
        hiddenFatLoss += Math.abs(dailyFatChange);
      }
      
      if (dailySurplus > 0) {
        // Muscle gain
        const weeklyMuscleGain = this.calculateMuscleGainRate(0, dailySurplus, trainingIntensity);
        dailyMuscleChange = weeklyMuscleGain / 7;
      }
      
      // Update composition
      fatMass = Math.max(10, fatMass + dailyFatChange); // Minimum essential fat
      leanMass = Math.max(50, leanMass + dailyMuscleChange);
      const tissueWeight = fatMass + leanMass;
      
      // Simulate periodic water retention cycles that mask fat loss (the whoosh pattern)
      // Fat loss is ~0.12 lbs/day at 600 cal deficit
      // Water needs to increase by ~0.12 lbs/day to mask this = ~0.8 lbs/week
      const waterCycleLength = 28; // ~4 week cycles
      const cyclePosition = day % waterCycleLength;
      let waterOffset = 0;
      
      // During fat loss, water often masks progress in cycles
      if (dailyDeficit > 300) {
        if (cyclePosition < 21) {
          // Accumulating phase: water increases to mask fat loss
          // Start at 0, increase to ~2.5 lbs over 3 weeks
          waterOffset = (cyclePosition / 21) * 2.5;
        } else {
          // Releasing phase: whoosh happens as water releases
          waterOffset = 2.5 - ((cyclePosition - 21) / 7) * 3; // Drops below 0
        }
      }
      
      const waterFluctuation = this.calculateWaterFluctuation(tissueWeight, {
        ...waterFactors,
        // Simulate cycle for women
        menstrualCycle: waterFactors.menstrualCycle ? (day % 28) : null
      }) + waterOffset;
      
      // Track hidden fat loss for whoosh effect
      if (dailyFatChange < 0) {
        hiddenFatLoss += Math.abs(dailyFatChange);
      }
      
      // Check for scale plateau (scale not moving despite fat loss)
      // Calculate 7-day MA on the fly for plateau detection
      let currentMA = currentWeight;
      if (day >= 6) {
        const recent7 = results.slice(-6).map(r => r.weight).concat([currentWeight]);
        currentMA = recent7.reduce((a, b) => a + b, 0) / 7;
      }
      
      // Use 7-day window to detect if scale has been essentially flat
      if (day >= 7) {
        const prevMA = results[day-7].movingAverage || results[day-7].weight;
        const maChange = Math.abs(currentMA - prevMA);
        
        // Plateau: 7-day MA changed less than 0.5 lbs over 1 week
        if (maChange < 0.5) {
          if (!inPlateau) {
            plateauDays = 1;
            inPlateau = true;
          } else {
            plateauDays++;
          }
        } else {
          plateauDays = 0;
          inPlateau = false;
          hiddenFatLoss = 0;
        }
      }
      
      // Check for whoosh effect - triggers deterministically when enough hidden fat loss accumulates
      let whooshDrop = 0;
      if (inPlateau && plateauDays >= 7 && hiddenFatLoss > 1.5) {
        // Whoosh triggers with increasing probability as plateau continues
        const baseProb = this.whooshProbability;
        const durationBonus = Math.min(0.3, plateauDays * 0.02); // +2% per day after 7
        const totalProb = Math.min(0.9, baseProb + durationBonus);
        
        if (Math.random() < totalProb) {
          whooshDrop = this.triggerWhoosh(hiddenFatLoss);
          hiddenFatLoss = 0;
          plateauDays = 0;
          inPlateau = false;
        }
      }
      
      // Calculate displayed weight
      currentWeight = tissueWeight + waterFluctuation - whooshDrop;
      
      results.push({
        day,
        date: currentDate.toISOString().split('T')[0],
        weight: parseFloat(currentWeight.toFixed(2)),
        movingAverage: parseFloat(currentMA.toFixed(2)),
        tissueWeight: parseFloat(tissueWeight.toFixed(2)),
        fatMass: parseFloat(fatMass.toFixed(2)),
        leanMass: parseFloat(leanMass.toFixed(2)),
        waterFluctuation: parseFloat(waterFluctuation.toFixed(2)),
        fatChange: parseFloat(dailyFatChange.toFixed(4)),
        muscleChange: parseFloat(dailyMuscleChange.toFixed(4)),
        inPlateau,
        plateauDays,
        whooshDrop: whooshDrop > 0 ? parseFloat(whooshDrop.toFixed(2)) : 0,
        isWhoosh: whooshDrop > 0
      });
    }
    
    // Moving averages already calculated during simulation
    return results;
  }

  // ============================================================================
  // UTILITY FUNCTIONS
  // ============================================================================
  
  calculateTrend(values) {
    const n = values.length;
    if (n < 2) return { slope: 0, intercept: values[0] || 0 };
    
    const x = Array.from({ length: n }, (_, i) => i);
    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = values.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((acc, xi, i) => acc + xi * values[i], 0);
    const sumXX = x.reduce((acc, xi) => acc + xi * xi, 0);
    
    const slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;
    
    return { slope, intercept };
  }
  
  calculateVariance(values) {
    const mean = values.reduce((a, b) => a + b, 0) / values.length;
    const squaredDiffs = values.map(v => Math.pow(v - mean, 2));
    return squaredDiffs.reduce((a, b) => a + b, 0) / values.length;
  }
  
  /**
   * Generate weight loss projection
   * @param {number} currentWeight - Starting weight
   * @param {number} goalWeight - Target weight
   * @param {number} weeklyLoss - Expected weekly loss rate
   * @returns {Object} Projection details
   */
  generateProjection(currentWeight, goalWeight, weeklyLoss = 1) {
    const weightToLose = currentWeight - goalWeight;
    const weeksNeeded = weightToLose / weeklyLoss;
    const daysNeeded = weeksNeeded * 7;
    
    const goalDate = new Date();
    goalDate.setDate(goalDate.getDate() + daysNeeded);
    
    return {
      startWeight: currentWeight,
      goalWeight,
      weightToLose,
      weeklyLoss,
      weeksNeeded: Math.ceil(weeksNeeded),
      daysNeeded: Math.ceil(daysNeeded),
      estimatedGoalDate: goalDate.toISOString().split('T')[0],
      isRealistic: weeklyLoss >= 0.5 && weeklyLoss <= 2.0
    };
  }
}

// ============================================================================
// EXPORT
// ============================================================================

module.exports = WeightPhysics;

// Also export as ES module for modern environments
if (typeof exports !== 'undefined') {
  exports.WeightPhysics = WeightPhysics;
  exports.default = WeightPhysics;
}
