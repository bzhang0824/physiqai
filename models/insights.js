/**
 * Insights Engine for PhysiqAI
 * Analyzes weight data and generates encouraging, actionable insights
 * Rule-based analysis - no ML required
 */

/**
 * Calculate trend from weight entries
 * @param {Array} entries - Array of {date: string, weight: number} objects
 * @returns {Object} Trend analysis result
 */
function calculateTrend(entries) {
  if (!entries || entries.length < 2) {
    return { slope: 0, trend: 'stable', weeklyChange: 0 };
  }

  // Sort by date
  const sorted = [...entries].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  const n = sorted.length;
  const sumX = sorted.reduce((sum, _, i) => sum + i, 0);
  const sumY = sorted.reduce((sum, entry) => sum + entry.weight, 0);
  const sumXY = sorted.reduce((sum, entry, i) => sum + i * entry.weight, 0);
  const sumX2 = sorted.reduce((sum, _, i) => sum + i * i, 0);

  // Linear regression slope (weight change per entry)
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
  
  // Convert to weekly change (assuming daily entries, adjust if needed)
  const daysSpan = (new Date(sorted[n-1].date) - new Date(sorted[0].date)) / (1000 * 60 * 60 * 24);
  const entriesPerWeek = daysSpan > 0 ? (n - 1) / (daysSpan / 7) : 7;
  const weeklyChange = slope * entriesPerWeek;

  let trend;
  if (weeklyChange < -0.1) trend = 'decreasing';
  else if (weeklyChange > 0.1) trend = 'increasing';
  else trend = 'stable';

  return { slope, trend, weeklyChange };
}

/**
 * Detect plateau in weight data
 * @param {Array} entries - Recent weight entries
 * @param {number} threshold - Max variation for plateau (default 1 lb)
 * @returns {boolean} True if plateau detected
 */
function detectPlateau(entries, threshold = 1.0) {
  if (!entries || entries.length < 7) return false;
  
  const recent = entries.slice(-7);
  const weights = recent.map(e => e.weight);
  const min = Math.min(...weights);
  const max = Math.max(...weights);
  
  return (max - min) < threshold;
}

/**
 * Check if current weight is a new low
 * @param {number} currentWeight 
 * @param {Array} allEntries - All historical entries
 * @returns {boolean}
 */
function isNewLow(currentWeight, allEntries) {
  if (!allEntries || allEntries.length < 2) return false;
  
  const previousLow = Math.min(...allEntries.slice(0, -1).map(e => e.weight));
  return currentWeight < previousLow;
}

/**
 * Compare current period to previous period
 * @param {Array} entries - All entries
 * @param {number} periodDays - Days per period (default 7 for weekly)
 * @returns {Object} Comparison data
 */
function comparePeriods(entries, periodDays = 7) {
  if (!entries || entries.length < periodDays * 2) {
    return { hasData: false };
  }

  const sorted = [...entries].sort((a, b) => new Date(a.date) - new Date(b.date));
  
  const currentPeriod = sorted.slice(-periodDays);
  const previousPeriod = sorted.slice(-periodDays * 2, -periodDays);
  
  const currentAvg = currentPeriod.reduce((s, e) => s + e.weight, 0) / currentPeriod.length;
  const previousAvg = previousPeriod.reduce((s, e) => s + e.weight, 0) / previousPeriod.length;
  
  const difference = currentAvg - previousAvg;
  
  return {
    hasData: true,
    currentAvg: round(currentAvg),
    previousAvg: round(previousAvg),
    difference: round(difference),
    better: difference < 0,
    periodLabel: periodDays === 7 ? 'week' : periodDays === 30 ? 'month' : 'period'
  };
}

/**
 * Get time-based greeting/message
 * @returns {string}
 */
function getTimeGreeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

/**
 * Round to 1 decimal place
 */
function round(num) {
  return Math.round(num * 10) / 10;
}

/**
 * Format weight with unit
 */
function formatWeight(weight) {
  return `${round(weight)} lbs`;
}

// ============================================
// INSIGHT GENERATORS
// ============================================

/**
 * Generate main insight based on current progress
 */
function generateProgressInsight(entries, goalWeight = null) {
  const trend = calculateTrend(entries);
  const currentWeight = entries[entries.length - 1]?.weight;
  const previousWeight = entries[entries.length - 2]?.weight;
  const dailyChange = previousWeight ? currentWeight - previousWeight : 0;
  
  const weeklyChange = Math.abs(round(trend.weeklyChange));
  const direction = trend.weeklyChange < 0 ? 'losing' : trend.weeklyChange > 0 ? 'gaining' : 'maintaining';
  
  // New low check
  if (isNewLow(currentWeight, entries)) {
    return {
      type: 'milestone',
      icon: '🎉',
      title: 'New Low! Congrats! 🎉',
      message: `You've reached a new low of ${formatWeight(currentWeight)}! Keep up the fantastic work!`,
      tone: 'celebratory'
    };
  }
  
  // Plateau check (only if we have enough data and trend is stable)
  if (detectPlateau(entries) && trend.trend === 'stable') {
    return {
      type: 'plateau',
      icon: '📊',
      title: 'Plateau Detected',
      message: `Your weight has been steady around ${formatWeight(currentWeight)}. Consider reviewing your calorie intake or adding variety to your workouts. Small tweaks can restart progress!`,
      tone: 'encouraging'
    };
  }
  
  // On track (losing weight)
  if (trend.trend === 'decreasing') {
    const rateMessage = weeklyChange >= 1 
      ? `You're crushing it with ${weeklyChange} lbs/week!`
      : `You're losing ${weeklyChange} lbs/week - a healthy, sustainable pace!`;
    
    return {
      type: 'progress',
      icon: '🔥',
      title: 'On Track!',
      message: `${rateMessage} Keep doing what you're doing - it's working!`,
      tone: 'positive'
    };
  }
  
  // Trending up
  if (trend.trend === 'increasing' && trend.weeklyChange > 0.5) {
    return {
      type: 'warning',
      icon: '📈',
      title: 'Trending Up',
      message: `Your weight is up ${weeklyChange} lbs/week. Take a moment to review last week's habits - maybe reduce sodium, prioritize sleep, or check portion sizes. You've got this!`,
      tone: 'supportive'
    };
  }
  
  // Stable/maintenance
  return {
    type: 'stable',
    icon: '⚖️',
    title: 'Holding Steady',
    message: `Your weight is stable at ${formatWeight(currentWeight)}. ${goalWeight ? `You're ${formatWeight(currentWeight - goalWeight)} from your goal.` : 'Consistency is key - keep building those healthy habits!'}`,
    tone: 'neutral'
  };
}

/**
 * Generate weekly comparison insight
 */
function generateWeeklyComparison(entries) {
  const comparison = comparePeriods(entries, 7);
  
  if (!comparison.hasData) {
    return null;
  }
  
  if (comparison.better) {
    return {
      type: 'comparison',
      icon: '↘️',
      title: 'Week Over Week',
      message: `You're down ${formatWeight(Math.abs(comparison.difference))} from last week (${formatWeight(comparison.previousAvg)} → ${formatWeight(comparison.currentAvg)}). Awesome progress!`,
      tone: 'positive'
    };
  } else if (comparison.difference > 0.5) {
    return {
      type: 'comparison',
      icon: '↗️',
      title: 'Week Over Week',
      message: `You're up ${formatWeight(comparison.difference)} from last week. No worries - daily fluctuations are normal! Focus on the overall trend.`,
      tone: 'supportive'
    };
  }
  
  return {
    type: 'comparison',
    icon: '➡️',
    title: 'Week Over Week',
    message: `You're holding steady compared to last week. Consistency wins the race!`,
    tone: 'neutral'
  };
}

/**
 * Generate monthly comparison insight
 */
function generateMonthlyComparison(entries) {
  const comparison = comparePeriods(entries, 30);
  
  if (!comparison.hasData) {
    return null;
  }
  
  const totalChange = round(comparison.difference);
  
  if (totalChange < -2) {
    return {
      type: 'comparison',
      icon: '📉',
      title: 'Monthly Progress',
      message: `Great month! You're down ${formatWeight(Math.abs(totalChange))} since last month. That's ${formatWeight(Math.abs(totalChange) / 4)}/week on average!`,
      tone: 'positive'
    };
  } else if (totalChange > 2) {
    return {
      type: 'comparison',
      icon: '📊',
      title: 'Monthly Check-in',
      message: `You're up ${formatWeight(totalChange)} from last month. Remember, progress isn't always linear. What adjustments can you make this month?`,
      tone: 'supportive'
    };
  }
  
  return {
    type: 'comparison',
    icon: '📅',
    title: 'Monthly View',
    message: `You've maintained around ${formatWeight(comparison.currentAvg)} this month. Sometimes maintenance is a win too!`,
    tone: 'neutral'
  };
}

/**
 * Generate motivation/tip based on data patterns
 */
function generateTip(entries) {
  const trend = calculateTrend(entries);
  const count = entries.length;
  
  // Logging streak encouragement
  if (count >= 7) {
    const recentEntries = entries.slice(-7);
    const daysWithData = recentEntries.length;
    if (daysWithData >= 5) {
      return {
        type: 'tip',
        icon: '✨',
        title: 'Great Consistency!',
        message: 'You\'ve been logging regularly - that habit alone puts you ahead of the game!',
        tone: 'positive'
      };
    }
  }
  
  // Encouragement for slower progress
  if (trend.trend === 'decreasing' && Math.abs(trend.weeklyChange) < 0.5) {
    return {
      type: 'tip',
      icon: '🐢',
      title: 'Slow and Steady',
      message: 'Losing 0.5-1 lb per week is ideal for long-term success. You\'re building habits that last!',
      tone: 'encouraging'
    };
  }
  
  // General encouragement
  const tips = [
    { icon: '💧', message: 'Stay hydrated! Sometimes thirst disguises itself as hunger.' },
    { icon: '😴', message: 'Prioritize sleep - it\'s when your body recovers and regulates hunger hormones.' },
    { icon: '🥗', message: 'Protein at every meal helps keep you full and supports your goals.' },
    { icon: '🚶', message: 'A 10-minute walk after meals can help with digestion and blood sugar.' },
    { icon: '🎯', message: 'Focus on progress, not perfection. Every healthy choice counts!' }
  ];
  
  const randomTip = tips[Math.floor(Math.random() * tips.length)];
  return {
    type: 'tip',
    icon: randomTip.icon,
    title: 'Quick Tip',
    message: randomTip.message,
    tone: 'helpful'
  };
}

// ============================================
// MAIN API
// ============================================

/**
 * Generate all insights for a user
 * @param {Object} data - User data object
 * @param {Array} data.entries - Weight entries {date, weight}
 * @param {number} data.goalWeight - Target weight (optional)
 * @returns {Object} Complete insights package
 */
function generateInsights(data) {
  const { entries, goalWeight } = data;
  
  if (!entries || entries.length === 0) {
    return {
      greeting: getTimeGreeting(),
      insights: [{
        type: 'welcome',
        icon: '👋',
        title: 'Welcome!',
        message: 'Start logging your weight daily to see personalized insights. You\'ve got this!',
        tone: 'welcome'
      }],
      stats: null
    };
  }

  const sorted = [...entries].sort((a, b) => new Date(a.date) - new Date(b.date));
  const currentWeight = sorted[sorted.length - 1].weight;
  const trend = calculateTrend(sorted);
  
  // Build insights array
  const insights = [];
  
  // Primary insight
  insights.push(generateProgressInsight(sorted, goalWeight));
  
  // Weekly comparison
  const weekly = generateWeeklyComparison(sorted);
  if (weekly) insights.push(weekly);
  
  // Monthly comparison (if enough data)
  if (sorted.length >= 14) {
    const monthly = generateMonthlyComparison(sorted);
    if (monthly) insights.push(monthly);
  }
  
  // Tip
  insights.push(generateTip(sorted));
  
  // Calculate stats
  const stats = {
    currentWeight: round(currentWeight),
    startingWeight: round(sorted[0].weight),
    totalChange: round(currentWeight - sorted[0].weight),
    weeklyTrend: round(trend.weeklyChange),
    entriesLogged: sorted.length,
    daysTracking: Math.round((new Date(sorted[sorted.length - 1].date) - new Date(sorted[0].date)) / (1000 * 60 * 60 * 24)),
    goalDistance: goalWeight ? round(currentWeight - goalWeight) : null
  };

  return {
    greeting: getTimeGreeting(),
    insights,
    stats,
    summary: generateSummary(stats, trend)
  };
}

/**
 * Generate one-line summary
 */
function generateSummary(stats, trend) {
  const { totalChange, weeklyTrend } = stats;
  
  if (stats.entriesLogged < 3) {
    return 'Keep logging daily to see your progress!';
  }
  
  if (totalChange < 0) {
    return `Down ${formatWeight(Math.abs(totalChange))} total (${formatWeight(Math.abs(weeklyTrend))}/week) - you're doing great!`;
  } else if (totalChange > 0) {
    return `Up ${formatWeight(totalChange)} since you started. Let's turn it around together!`;
  }
  
  return 'Maintaining your starting weight. Small changes add up!';
}

// ============================================
// EXPORTS
// ============================================

module.exports = {
  // Main API
  generateInsights,
  generateSummary,
  
  // Individual insight generators (for testing/custom use)
  generateProgressInsight,
  generateWeeklyComparison,
  generateMonthlyComparison,
  generateTip,
  
  // Utility functions
  calculateTrend,
  detectPlateau,
  isNewLow,
  comparePeriods,
  getTimeGreeting,
  
  // Formatting helpers
  formatWeight,
  round
};
