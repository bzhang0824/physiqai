/**
 * Body Calculator - Data Pipeline Engine
 * Connects workout data to body changes using physics-based formulas
 * 
 * Core Logic Chain:
 * 1. Workout Volume → Muscle Stimulus
 * 2. Protein Intake → Muscle Synthesis
 * 3. Calorie Deficit/Surplus → Weight Change
 * 4. Timeline → Progress Curve
 */

class BodyCalculator {
  constructor() {
    // Constants for calculations
    this.VOLUME_THRESHOLD = 10000; // lbs/week for muscle gain potential
    this.PROTEIN_THRESHOLD = 0.8; // g/lb bodyweight for good synthesis
    this.CALORIES_PER_LB_FAT = 3500; // caloric equivalent of 1 lb fat
    this.CALORIES_PER_LB_MUSCLE = 2500; // caloric equivalent of 1 lb muscle (approx)
    this.MAX_MUSCLE_GAIN_RATE = 0.5; // lbs/week max natural muscle gain
    this.MAX_FAT_LOSS_RATE = 2.0; // lbs/week max recommended fat loss
  }

  // ============================================
  // 1. WORKOUT VOLUME → MUSCLE STIMULUS
  // ============================================
  
  /**
   * Calculate muscle stimulus from weekly workout volume
   * @param {number} weeklyVolumeLbs - Total weight moved per week
   * @param {number} bodyweight - User's bodyweight in lbs
   * @returns {Object} Stimulus metrics
   */
  calculateMuscleStimulus(weeklyVolumeLbs, bodyweight) {
    // Volume per lb of bodyweight (relative intensity)
    const volumePerLb = weeklyVolumeLbs / bodyweight;
    
    // Stimulus score (0-1 scale)
    const stimulusScore = Math.min(weeklyVolumeLbs / this.VOLUME_THRESHOLD, 1.2);
    
    // Volume category
    let volumeCategory;
    if (weeklyVolumeLbs < 5000) {
      volumeCategory = 'maintenance';
    } else if (weeklyVolumeLbs < this.VOLUME_THRESHOLD) {
      volumeCategory = 'moderate_growth';
    } else if (weeklyVolumeLbs < 20000) {
      volumeCategory = 'optimal_growth';
    } else {
      volumeCategory = 'high_volume';
    }
    
    // Muscle gain potential flag
    const hasGainPotential = weeklyVolumeLbs >= this.VOLUME_THRESHOLD;
    
    return {
      weeklyVolume: weeklyVolumeLbs,
      volumePerLb,
      stimulusScore: Math.round(stimulusScore * 100) / 100,
      volumeCategory,
      hasGainPotential,
      volumeProgress: Math.min(weeklyVolumeLbs / this.VOLUME_THRESHOLD, 1)
    };
  }

  /**
   * Calculate volume from workout sets
   * @param {Array} workouts - Array of workout objects with exercises
   * @returns {number} Total weekly volume in lbs
   */
  calculateWeeklyVolume(workouts) {
    let totalVolume = 0;
    
    for (const workout of workouts) {
      for (const exercise of workout.exercises || []) {
        for (const set of exercise.sets || []) {
          // Volume = weight × reps
          totalVolume += (set.weight || 0) * (set.reps || 0);
        }
      }
    }
    
    return totalVolume;
  }

  // ============================================
  // 2. PROTEIN INTAKE → MUSCLE SYNTHESIS
  // ============================================
  
  /**
   * Calculate muscle synthesis capability from protein intake
   * @param {number} dailyProteinG - Daily protein in grams
   * @param {number} bodyweight - Bodyweight in lbs
   * @returns {Object} Synthesis metrics
   */
  calculateMuscleSynthesis(dailyProteinG, bodyweight) {
    // Protein per lb of bodyweight
    const proteinPerLb = dailyProteinG / bodyweight;
    
    // Synthesis efficiency (0-1 scale based on threshold)
    let synthesisEfficiency;
    if (proteinPerLb >= this.PROTEIN_THRESHOLD) {
      synthesisEfficiency = 1.0;
    } else if (proteinPerLb >= 0.5) {
      // Linear scale between 0.5 and 0.8 g/lb
      synthesisEfficiency = (proteinPerLb - 0.5) / (this.PROTEIN_THRESHOLD - 0.5);
    } else {
      synthesisEfficiency = 0.3; // Minimum baseline
    }
    
    // Protein category
    let proteinCategory;
    if (proteinPerLb < 0.5) {
      proteinCategory = 'insufficient';
    } else if (proteinPerLb < this.PROTEIN_THRESHOLD) {
      proteinCategory = 'adequate';
    } else if (proteinPerLb < 1.0) {
      proteinCategory = 'optimal';
    } else {
      proteinCategory = 'high';
    }
    
    // Muscle building capacity multiplier
    const buildingCapacity = Math.min(synthesisEfficiency * 1.2, 1.0);
    
    return {
      dailyProtein: dailyProteinG,
      proteinPerLb: Math.round(proteinPerLb * 100) / 100,
      synthesisEfficiency: Math.round(synthesisEfficiency * 100) / 100,
      proteinCategory,
      buildingCapacity: Math.round(buildingCapacity * 100) / 100,
      meetsThreshold: proteinPerLb >= this.PROTEIN_THRESHOLD
    };
  }

  // ============================================
  // 3. CALORIE DEFICIT/SURPLUS → WEIGHT CHANGE
  // ============================================
  
  /**
   * Calculate expected weight change from calorie balance
   * @param {number} dailyCalories - Daily calorie intake
   * @param {number} tdee - Total Daily Energy Expenditure (maintenance)
   * @param {number} days - Time period in days
   * @param {Object} synthesisData - From calculateMuscleSynthesis
   * @param {Object} stimulusData - From calculateMuscleStimulus
   * @returns {Object} Weight change projection
   */
  calculateWeightChange(dailyCalories, tdee, days, synthesisData, stimulusData) {
    const dailyDeficit = tdee - dailyCalories; // Positive = deficit, Negative = surplus
    const weeklyDeficit = dailyDeficit * 7;
    const totalDeficit = dailyDeficit * days;
    
    // Base fat change calculation
    const fatChangeLbs = totalDeficit / this.CALORIES_PER_LB_FAT;
    
    // Determine if we can build muscle (requires surplus + stimulus + protein)
    const canBuildMuscle = (
      dailyDeficit < 0 && // Caloric surplus
      stimulusData.hasGainPotential && // Enough volume
      synthesisData.meetsThreshold // Enough protein
    );
    
    // Muscle gain calculation (if conditions met)
    let muscleChangeLbs = 0;
    if (canBuildMuscle) {
      const surplusCalories = Math.abs(totalDeficit);
      const theoreticalMuscleGain = surplusCalories / this.CALORIES_PER_LB_MUSCLE;
      const maxGain = (days / 7) * this.MAX_MUSCLE_GAIN_RATE;
      
      // Adjust for synthesis efficiency
      muscleChangeLbs = Math.min(
        theoreticalMuscleGain * synthesisData.buildingCapacity,
        maxGain
      );
    }
    
    // Net weight change
    const netWeightChange = -fatChangeLbs + muscleChangeLbs; // Negative fat change = fat loss
    
    // Body composition change
    const bodyComposition = {
      fatLost: fatChangeLbs > 0 ? Math.round(fatChangeLbs * 100) / 100 : 0,
      muscleGained: Math.round(muscleChangeLbs * 100) / 100,
      netChange: Math.round(netWeightChange * 100) / 100
    };
    
    // Rate recommendations
    let rateRecommendation;
    const weeklyChange = netWeightChange / (days / 7);
    if (Math.abs(weeklyChange) > 2.5) {
      rateRecommendation = weeklyChange > 0 ? 'bulk_too_fast' : 'cut_too_fast';
    } else if (Math.abs(weeklyChange) > 1.5) {
      rateRecommendation = weeklyChange > 0 ? 'aggressive_bulk' : 'aggressive_cut';
    } else {
      rateRecommendation = 'optimal_rate';
    }
    
    return {
      dailyDeficit,
      weeklyDeficit,
      totalDeficit,
      fatChangeLbs: Math.round(fatChangeLbs * 100) / 100,
      muscleChangeLbs: Math.round(muscleChangeLbs * 100) / 100,
      netWeightChange: Math.round(netWeightChange * 100) / 100,
      bodyComposition,
      canBuildMuscle,
      weeklyRate: Math.round(weeklyChange * 100) / 100,
      rateRecommendation,
      phase: dailyDeficit > 0 ? 'cutting' : (dailyDeficit < 0 ? 'bulking' : 'maintenance')
    };
  }

  // ============================================
  // 4. TIMELINE → PROGRESS CURVE
  // ============================================
  
  /**
   * Generate progress projection over time
   * @param {Object} currentState - Current body metrics
   * @param {Object} targets - Target body metrics
   * @param {Object} dailyInputs - Daily calorie/protein inputs
   * @param {number} weeks - Projection timeframe
   * @returns {Array} Weekly progress snapshots
   */
  generateProgressCurve(currentState, targets, dailyInputs, weeks = 12) {
    const curve = [];
    let currentWeight = currentState.weight;
    let currentBodyFat = currentState.bodyFat || 20;
    
    // Calculate components once
    const synthesis = this.calculateMuscleSynthesis(
      dailyInputs.dailyProtein,
      currentState.weight
    );
    const stimulus = this.calculateMuscleStimulus(
      dailyInputs.weeklyVolume,
      currentState.weight
    );
    
    for (let week = 0; week <= weeks; week++) {
      // Calculate weekly change
      const weeklyChange = this.calculateWeightChange(
        dailyInputs.dailyCalories,
        dailyInputs.tdee,
        7,
        synthesis,
        stimulus
      );
      
      // Update body composition
      currentWeight += weeklyChange.netWeightChange;
      const fatMass = (currentWeight * (currentBodyFat / 100)) - weeklyChange.bodyComposition.fatLost;
      currentBodyFat = (fatMass / currentWeight) * 100;
      
      // Progress toward target
      const weightProgress = targets.weight ? 
        1 - Math.abs(currentWeight - targets.weight) / Math.abs(currentState.weight - targets.weight) : 0;
      
      curve.push({
        week,
        weight: Math.round(currentWeight * 10) / 10,
        bodyFat: Math.round(currentBodyFat * 10) / 10,
        fatMass: Math.round(fatMass * 10) / 10,
        leanMass: Math.round((currentWeight - fatMass) * 10) / 10,
        weeklyChange: weeklyChange.netWeightChange,
        weightProgress: Math.max(0, Math.min(1, weightProgress)),
        phase: weeklyChange.phase,
        adherence: this.calculateAdherence(synthesis, stimulus)
      });
    }
    
    return curve;
  }

  /**
   * Calculate adherence score based on protocol compliance
   */
  calculateAdherence(synthesis, stimulus) {
    const proteinScore = synthesis.synthesisEfficiency;
    const volumeScore = stimulus.stimulusScore;
    
    return {
      overall: Math.round(((proteinScore + volumeScore) / 2) * 100),
      protein: Math.round(proteinScore * 100),
      training: Math.round(Math.min(volumeScore, 1) * 100)
    };
  }

  // ============================================
  // 5. COMPOSITE ANALYSIS
  // ============================================
  
  /**
   * Full body change analysis combining all factors
   */
  analyze(data) {
    const {
      bodyweight,
      weeklyVolume,
      dailyProtein,
      dailyCalories,
      tdee,
      timeframeDays = 30,
      workouts = []
    } = data;
    
    // Calculate volume from workouts if provided
    const volume = workouts.length > 0 
      ? this.calculateWeeklyVolume(workouts) 
      : weeklyVolume;
    
    // Run all calculations
    const stimulus = this.calculateMuscleStimulus(volume, bodyweight);
    const synthesis = this.calculateMuscleSynthesis(dailyProtein, bodyweight);
    const weightChange = this.calculateWeightChange(
      dailyCalories,
      tdee,
      timeframeDays,
      synthesis,
      stimulus
    );
    
    // Generate recommendations
    const recommendations = this.generateRecommendations(stimulus, synthesis, weightChange);
    
    return {
      inputs: {
        bodyweight,
        weeklyVolume: volume,
        dailyProtein,
        dailyCalories,
        tdee,
        timeframeDays
      },
      stimulus,
      synthesis,
      weightChange,
      recommendations,
      projectedMonthlyChange: {
        weight: weightChange.netWeightChange,
        fat: weightChange.bodyComposition.fatLost,
        muscle: weightChange.bodyComposition.muscleGained
      }
    };
  }

  /**
   * Generate actionable recommendations
   */
  generateRecommendations(stimulus, synthesis, weightChange) {
    const recs = [];
    
    // Volume recommendations
    if (!stimulus.hasGainPotential) {
      const volumeGap = this.VOLUME_THRESHOLD - stimulus.weeklyVolume;
      recs.push({
        category: 'training',
        priority: 'high',
        message: `Increase weekly volume by ${Math.round(volumeGap)} lbs to reach muscle gain threshold`,
        action: 'add_sets_or_weight'
      });
    }
    
    // Protein recommendations
    if (!synthesis.meetsThreshold) {
      recs.push({
        category: 'nutrition',
        priority: 'high',
        message: `Increase protein to at least ${Math.round(0.8 * stimulus.weeklyVolume / stimulus.volumePerLb)}g daily`,
        action: 'increase_protein'
      });
    }
    
    // Calorie recommendations
    if (weightChange.rateRecommendation === 'cut_too_fast') {
      recs.push({
        category: 'nutrition',
        priority: 'medium',
        message: 'Deficit too aggressive - risk of muscle loss',
        action: 'increase_calories_slightly'
      });
    } else if (weightChange.rateRecommendation === 'bulk_too_fast') {
      recs.push({
        category: 'nutrition',
        priority: 'medium',
        message: 'Surplus too high - excess fat gain likely',
        action: 'reduce_calories_slightly'
      });
    }
    
    return recs;
  }

  // ============================================
  // 6. UTILITY FUNCTIONS
  // ============================================
  
  /**
   * Quick estimate of time to reach goal
   */
  estimateTimeToGoal(current, target, dailyDeficit) {
    const weightDiff = target - current;
    const caloriesNeeded = weightDiff * this.CALORIES_PER_LB_FAT;
    const days = Math.abs(caloriesNeeded / dailyDeficit);
    
    return {
      days: Math.round(days),
      weeks: Math.round(days / 7 * 10) / 10,
      months: Math.round(days / 30 * 10) / 10,
      date: new Date(Date.now() + days * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
    };
  }

  /**
   * Calculate TDEE using Mifflin-St Jeor equation with activity multiplier
   */
  calculateTDEE(weight, height, age, gender, activityLevel = 'moderate') {
    // Mifflin-St Jeor
    let bmr;
    if (gender === 'male') {
      bmr = (10 * weight * 0.453592) + (6.25 * height * 2.54) - (5 * age) + 5;
    } else {
      bmr = (10 * weight * 0.453592) + (6.25 * height * 2.54) - (5 * age) - 161;
    }
    
    const multipliers = {
      sedentary: 1.2,
      light: 1.375,
      moderate: 1.55,
      active: 1.725,
      very_active: 1.9
    };
    
    return Math.round(bmr * (multipliers[activityLevel] || 1.55));
  }
}

// Export for different module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = BodyCalculator;
}

if (typeof window !== 'undefined') {
  window.BodyCalculator = BodyCalculator;
}
