/**
 * PhysiqAI Founder Dashboard - Backend Server
 * 
 * This is NOT the production app. This is a testing/debugging interface
 * for the founder to see everything happening under the hood.
 * 
 * Features:
 * - Upload test images
 * - See full prompts used
 * - See all calculations and reasoning
 * - Track costs per generation
 * - View model parameters
 * - Comprehensive logging
 * 
 * Run: node server.js
 * Access: http://localhost:3456
 */

const http = require('http');
const fs = require('fs');
const path = require('path');
const https = require('https');
const { URL } = require('url');

// Load environment variables
require('dotenv').config({ path: path.join(__dirname, '..', '.env') });

const PORT = 3456;
const FAL_KEY = process.env.FAL_KEY;
const GOOGLE_AI_KEY = process.env.GOOGLE_AI_KEY;

// ============================================================
// LOGGING SYSTEM
// ============================================================

const LOG_DIR = path.join(__dirname, 'logs');
const BUGS_FILE = path.join(LOG_DIR, 'bugs.json');
const GENERATIONS_FILE = path.join(LOG_DIR, 'generations.json');
const COSTS_FILE = path.join(LOG_DIR, 'costs.json');

// Ensure log directory exists
if (!fs.existsSync(LOG_DIR)) {
  fs.mkdirSync(LOG_DIR, { recursive: true });
}

// Initialize log files if they don't exist
if (!fs.existsSync(BUGS_FILE)) {
  fs.writeFileSync(BUGS_FILE, JSON.stringify([], null, 2));
}
if (!fs.existsSync(GENERATIONS_FILE)) {
  fs.writeFileSync(GENERATIONS_FILE, JSON.stringify([], null, 2));
}
if (!fs.existsSync(COSTS_FILE)) {
  fs.writeFileSync(COSTS_FILE, JSON.stringify({ total: 0, generations: [] }, null, 2));
}

function log(level, message, data = {}) {
  const timestamp = new Date().toISOString();
  const logEntry = { timestamp, level, message, data };
  console.log(`[${timestamp}] [${level}] ${message}`, data);
  
  // Append to daily log file
  const dateStr = timestamp.split('T')[0];
  const logFile = path.join(LOG_DIR, `${dateStr}.log`);
  fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
  
  return logEntry;
}

function logBug(bug) {
  const bugs = JSON.parse(fs.readFileSync(BUGS_FILE));
  bug.id = `BUG-${Date.now()}`;
  bug.status = 'open';
  bug.createdAt = new Date().toISOString();
  bug.testWritten = false;
  bug.testPassing = false;
  bugs.push(bug);
  fs.writeFileSync(BUGS_FILE, JSON.stringify(bugs, null, 2));
  log('BUG', `New bug reported: ${bug.id}`, bug);
  return bug;
}

function logGeneration(generation) {
  const generations = JSON.parse(fs.readFileSync(GENERATIONS_FILE));
  generation.id = `GEN-${Date.now()}`;
  generation.createdAt = new Date().toISOString();
  generations.push(generation);
  fs.writeFileSync(GENERATIONS_FILE, JSON.stringify(generations, null, 2));
  
  // Update costs
  const costs = JSON.parse(fs.readFileSync(COSTS_FILE));
  const cost = generation.cost || 0.04; // Default fal.ai cost
  costs.total += cost;
  costs.generations.push({
    id: generation.id,
    cost,
    model: generation.model,
    timestamp: generation.createdAt
  });
  fs.writeFileSync(COSTS_FILE, JSON.stringify(costs, null, 2));
  
  log('GENERATION', `New generation: ${generation.id}`, { cost, model: generation.model });
  return generation;
}

// ============================================================
// PHYSIOLOGY ENGINE (from research)
// ============================================================

const PHYSIOLOGY = {
  // Base monthly gain rates (kg) by experience - Aragon/Helms model
  baseGainRates: {
    beginner: 0.0125,     // 1.25% bodyweight/month
    intermediate: 0.0075, // 0.75%
    advanced: 0.00375     // 0.375%
  },
  
  // Gender modifier - Roberts 2020
  genderModifier: (gender) => {
    return gender === 'female' ? 0.5 : 1.0;
  },
  
  // Age modifier - Feldman 2002, ~1% decline per year after 30
  ageModifier: (age) => {
    if (age <= 30) return 1.0;
    const yearsOver30 = age - 30;
    return Math.max(0.5, 1.0 - (yearsOver30 * 0.01));
  },
  
  // Sleep modifier - Lamon 2021: 18% reduction if poor
  sleepModifier: (quality) => {
    const mods = { poor: 0.82, average: 0.91, good: 1.0 };
    return mods[quality] || 0.91;
  },
  
  // Frequency modifier - Schoenfeld 2016
  frequencyModifier: (timesPerWeek) => {
    if (timesPerWeek < 2) return 0.7;
    if (timesPerWeek === 2) return 0.85;
    if (timesPerWeek === 3) return 0.95;
    if (timesPerWeek >= 4) return 1.0;
    return 0.9;
  },
  
  // Nutrition modifier
  nutritionModifier: (goal) => {
    const mods = { cut: 0.3, maintain: 0.7, bulk: 1.0 };
    return mods[goal] || 0.7;
  }
};

function calculateProjections(profile, horizonWeeks) {
  log('CALC', 'Starting projection calculation', { profile, horizonWeeks });
  
  const steps = [];
  
  // Step 1: Base rate
  const baseRate = PHYSIOLOGY.baseGainRates[profile.experienceLevel] || 0.0075;
  const baseMonthlyGain = profile.weightKg * baseRate;
  steps.push({
    step: 1,
    name: 'Base Rate (Aragon/Helms)',
    calculation: `${profile.weightKg}kg × ${baseRate} = ${baseMonthlyGain.toFixed(3)}kg/month`,
    source: 'Aragon & Helms model (JISSN 2014)',
    value: baseMonthlyGain
  });
  
  // Step 2: Apply modifiers
  const genderMod = PHYSIOLOGY.genderModifier(profile.gender);
  steps.push({
    step: 2,
    name: 'Gender Modifier',
    calculation: `${profile.gender} = ${genderMod}`,
    source: 'Roberts et al. 2020 (PMID: 32218059)',
    value: genderMod
  });
  
  const ageMod = PHYSIOLOGY.ageModifier(profile.age);
  steps.push({
    step: 3,
    name: 'Age Modifier',
    calculation: `Age ${profile.age} = ${ageMod.toFixed(2)}`,
    source: 'Feldman et al. 2002 - ~1%/year decline after 30',
    value: ageMod
  });
  
  const sleepMod = PHYSIOLOGY.sleepModifier(profile.sleepQuality);
  steps.push({
    step: 4,
    name: 'Sleep Modifier',
    calculation: `${profile.sleepQuality} sleep = ${sleepMod}`,
    source: 'Lamon et al. 2021 (PMC7785053) - 18% MPS reduction',
    value: sleepMod
  });
  
  const freqMod = PHYSIOLOGY.frequencyModifier(profile.workoutsPerWeek);
  steps.push({
    step: 5,
    name: 'Frequency Modifier',
    calculation: `${profile.workoutsPerWeek}x/week = ${freqMod}`,
    source: 'Schoenfeld et al. 2016 (PMID: 27102172)',
    value: freqMod
  });
  
  const nutritionMod = PHYSIOLOGY.nutritionModifier(profile.nutritionGoal);
  steps.push({
    step: 6,
    name: 'Nutrition Modifier',
    calculation: `${profile.nutritionGoal} = ${nutritionMod}`,
    source: 'Slater et al. 2019 (PMC6710320)',
    value: nutritionMod
  });
  
  // Step 3: Calculate final
  const totalModifier = genderMod * ageMod * sleepMod * freqMod * nutritionMod;
  const adjustedMonthlyGain = baseMonthlyGain * totalModifier;
  const months = horizonWeeks / 4;
  const totalGainKg = adjustedMonthlyGain * months;
  const totalGainLbs = totalGainKg * 2.205;
  
  steps.push({
    step: 7,
    name: 'Final Calculation',
    calculation: `${baseMonthlyGain.toFixed(3)} × ${totalModifier.toFixed(3)} × ${months} months = ${totalGainKg.toFixed(2)}kg (${totalGainLbs.toFixed(1)}lbs)`,
    source: 'Combined modifiers',
    value: totalGainKg
  });
  
  const result = {
    monthlyGainKg: adjustedMonthlyGain,
    totalGainKg,
    totalGainLbs,
    totalModifier,
    horizonWeeks,
    steps,
    confidence: calculateConfidence(profile)
  };
  
  log('CALC', 'Projection complete', result);
  return result;
}

function calculateConfidence(profile) {
  let score = 100;
  const factors = [];
  
  // Deduct for auto body fat
  if (profile.bodyFatPercent === 'auto') {
    score -= 10;
    factors.push({ factor: 'Body fat auto-estimated', impact: -10 });
  }
  
  // Deduct for poor sleep
  if (profile.sleepQuality === 'poor') {
    score -= 5;
    factors.push({ factor: 'Poor sleep increases variance', impact: -5 });
  }
  
  // Deduct for extreme experience claims
  if (profile.experienceLevel === 'advanced' && profile.age < 25) {
    score -= 10;
    factors.push({ factor: 'Advanced at young age - verify', impact: -10 });
  }
  
  const level = score >= 80 ? 'high' : score >= 60 ? 'medium' : 'low';
  
  return { score, level, factors };
}

// ============================================================
// PROMPT GENERATION (ENHANCED v0.2)
// ============================================================

const MUSCLE_ANATOMY = {
  chest: {
    primary: "pectoralis major",
    regions: ["upper pectorals (clavicular head)", "mid chest (sternal head)", "lower chest"],
    visual_cues: ["increased chest fullness and thickness", "more defined sternum separation", "visible upper chest 'shelf'"],
    exercises: "bench press, incline press, flyes"
  },
  arms: {
    primary: "biceps brachii and triceps brachii",
    regions: ["bicep peak (long head)", "tricep horseshoe (lateral head)", "brachialis (outer arm)", "forearms"],
    visual_cues: ["fuller arm circumference", "more prominent bicep peak", "visible tricep definition", "forearm vascularity"],
    exercises: "curls, tricep extensions, chin-ups"
  },
  shoulders: {
    primary: "deltoids (all three heads)",
    regions: ["anterior deltoid (front)", "lateral deltoid (side caps)", "posterior deltoid (rear)"],
    visual_cues: ["rounder shoulder caps", "improved shoulder-to-waist ratio", "more 3D shoulder appearance"],
    exercises: "overhead press, lateral raises, rear delt flies"
  },
  back: {
    primary: "latissimus dorsi, trapezius, rhomboids, erector spinae",
    regions: ["upper back width", "lat spread and thickness", "lower lat insertion", "mid-back detail"],
    visual_cues: ["wider V-taper", "more visible lat wings from front", "improved back thickness"],
    exercises: "pull-ups, rows, deadlifts"
  },
  legs: {
    primary: "quadriceps, hamstrings, glutes, calves",
    regions: ["quad sweep (vastus lateralis)", "teardrop (vastus medialis)", "hamstring tie-in", "glute development", "calf size"],
    visual_cues: ["more leg separation and definition", "visible quad sweep", "improved leg-to-torso proportion"],
    exercises: "squats, leg press, Romanian deadlifts, calf raises"
  },
  core: {
    primary: "rectus abdominis, obliques, serratus anterior",
    regions: ["upper abs", "lower abs", "oblique lines", "serratus"],
    visual_cues: ["more visible ab definition", "serratus visibility", "tighter waistline"],
    exercises: "crunches, leg raises, planks, ab wheel"
  }
};

function buildPrompt(profile, projections) {
  log('PROMPT', 'Building ENHANCED transformation prompt', { profile, projections });
  
  const timeDesc = projections.horizonWeeks <= 12 
    ? `${projections.horizonWeeks} weeks` 
    : `${Math.round(projections.horizonWeeks / 4)} months`;
  
  const gainLbs = Math.round(projections.totalGainLbs * 10) / 10;
  
  // Build anatomically specific muscle instructions
  let muscleInstructions = [];
  (profile.focusAreas || []).forEach(area => {
    const anatomy = MUSCLE_ANATOMY[area];
    if (anatomy) {
      muscleInstructions.push(`
${area.toUpperCase()} DEVELOPMENT (${anatomy.primary}):
- Target regions: ${anatomy.regions.join(', ')}
- Expected visual changes: ${anatomy.visual_cues.join('; ')}
- Consistent with ${anatomy.exercises} training stimulus`);
    }
  });
  
  // Build nutrition-specific instructions
  let bodyCompInstructions = '';
  if (profile.nutritionGoal === 'cut') {
    bodyCompInstructions = `
BODY COMPOSITION - CUTTING PHASE:
- Reduce visible subcutaneous body fat
- Increase muscle definition and separation between muscle groups
- Show enhanced vascularity, especially in forearms, biceps, and deltoids
- More visible serratus anterior, intercostals, and oblique lines
- Skin appears tighter and more shrink-wrapped around muscle bellies
- Maintain muscle fullness despite caloric deficit (no flat/depleted look)`;
  } else if (profile.nutritionGoal === 'bulk') {
    bodyCompInstructions = `
BODY COMPOSITION - BULKING PHASE:
- Show increased overall muscle volume and fullness
- Muscles appear fuller, rounder, and more pumped
- Slight smoothing of extreme definition is acceptable (caloric surplus)
- Overall larger, more imposing physique
- Emphasize SIZE and MASS over razor-sharp definition`;
  } else {
    bodyCompInstructions = `
BODY COMPOSITION - MAINTENANCE/RECOMPOSITION:
- Subtle improvement in overall muscle definition
- Slight increase in muscle fullness in trained areas
- Maintain current body fat level while improving composition
- Gradual positive changes concentrated in focus areas`;
  }
  
  // Experience level context
  let experienceContext = '';
  if (profile.experienceLevel === 'beginner') {
    experienceContext = `
EXPERIENCE CONTEXT - BEGINNER (Research: Aragon/Helms JISSN 2014):
- This person is in the "newbie gains" window with rapid adaptation potential
- Show NOTICEABLE and EXCITING visible changes
- Muscle growth should be clearly visible but not extreme
- Expected rate: 1-1.5% bodyweight per month in lean mass`;
  } else if (profile.experienceLevel === 'intermediate') {
    experienceContext = `
EXPERIENCE CONTEXT - INTERMEDIATE (Research: McDonald Model):
- This person has 1-3 years training experience
- Show CONTINUED but MODERATE progress (diminishing returns beginning)
- Changes are real but less dramatic than a beginner would see
- Expected rate: 0.5-1% bodyweight per month in lean mass`;
  } else {
    experienceContext = `
EXPERIENCE CONTEXT - ADVANCED (Research: Natural muscular potential ceiling):
- This person is approaching their genetic potential
- Show SUBTLE REFINEMENT rather than dramatic size changes
- Focus on improvements in conditioning, symmetry, and weak points
- Expected rate: 0.25-0.5% bodyweight per month (very slow gains)`;
  }
  
  // InstantID handles face preservation automatically, so focus prompt on body transformation
  const prompt = `Realistic fitness transformation photograph showing ${timeDesc} of dedicated strength training.

TRANSFORMATION TARGET:
Add approximately ${gainLbs} lbs of lean muscle mass (science-based projection)
Training focus areas: ${profile.focusAreas?.join(', ') || 'general development'}

${experienceContext}

SPECIFIC MUSCLE DEVELOPMENT:${muscleInstructions.join('')}

${bodyCompInstructions}

REALISM REQUIREMENTS:
- Natural, achievable muscle development for ${timeDesc} timeframe
- Subtle but noticeable changes (not dramatic transformation)
- Maintain realistic proportions and natural appearance
- Keep same lighting, pose, and clothing
- Result should look like a genuine progress photo
- No fantasy bodybuilder proportions or artificial enhancement

SCIENTIFIC BASIS:
Base projection from Aragon & Helms model (JISSN 2014), adjusted for age (Feldman 2002), training frequency (Schoenfeld PMID: 27102172), sleep quality (Lamon PMC7785053), and nutrition phase (Slater PMC6710320).

This represents realistic, natural progress achievable through consistent training and proper recovery.`;

  log('PROMPT', 'Enhanced prompt built', { promptLength: prompt.length, focusAreas: profile.focusAreas });
  return prompt;
}

// ============================================================
// IMAGE GENERATION (InstantID via Replicate)
// ============================================================

const REPLICATE_API_TOKEN = process.env.REPLICATE_API_TOKEN;

async function generateTransformation(imageBase64, prompt, modelSettings = {}) {
  const settings = {
    guidance_scale: modelSettings.guidance_scale || 4.5,  // More conservative
    num_inference_steps: modelSettings.num_inference_steps || 25,
    ip_adapter_scale: modelSettings.ip_adapter_scale || 0.8,      // High identity preservation
    controlnet_conditioning_scale: modelSettings.controlnet_conditioning_scale || 0.8,
    ...modelSettings
  };
  
  log('GENERATE', 'Starting InstantID generation', { settings, promptLength: prompt.length });
  
  const startTime = Date.now();
  
  // Convert base64 to data URL for Replicate
  const imageDataUrl = `data:image/jpeg;base64,${imageBase64}`;
  
  // Step 1: Submit to Replicate InstantID
  const requestBody = {
    input: {
      image: imageDataUrl,
      prompt: prompt,
      negative_prompt: "disfigured, bad anatomy, bad hands, missing fingers, extra fingers, low quality, normal quality, blurry, bad eyes, missing arms, missing legs, extra arms, extra legs, poorly drawn hands, poorly drawn feet, poorly drawn face, out of frame, mutation, mutated, extra limbs, extra heads, extra fingers, ugly, poorly drawn, deformed, blurred",
      
      // InstantID specific settings
      ip_adapter_scale: settings.ip_adapter_scale,
      controlnet_conditioning_scale: settings.controlnet_conditioning_scale,
      
      // Generation settings  
      guidance_scale: settings.guidance_scale,
      num_inference_steps: settings.num_inference_steps,
      
      // Output format
      width: 1024,
      height: 1024,
      style: "Photograph"
    }
  };

  log('GENERATE', 'Submitting to Replicate InstantID', { 
    ip_adapter_scale: settings.ip_adapter_scale,
    guidance_scale: settings.guidance_scale 
  });
  
  const result = await makeHttpRequest({
    hostname: 'api.replicate.com',
    path: '/v1/models/zsxkib/instant-id/predictions',
    method: 'POST',
    headers: {
      'Authorization': `Token ${REPLICATE_API_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  });
  
  log('GENERATE', 'Replicate request submitted', { id: result.id });
  
  // Step 2: Poll for completion
  let attempts = 0;
  const maxAttempts = 60;
  let finalResult = null;
  
  while (!finalResult && attempts < maxAttempts) {
    await sleep(2000);
    attempts++;
    
    const statusResponse = await makeHttpRequest({
      hostname: 'api.replicate.com', 
      path: `/v1/predictions/${result.id}`,
      method: 'GET',
      headers: {
        'Authorization': `Token ${REPLICATE_API_TOKEN}`,
      }
    });
    
    log('GENERATE', `Poll attempt ${attempts}`, { status: statusResponse.status });
    
    if (statusResponse.status === 'succeeded' && statusResponse.output) {
      finalResult = statusResponse;
    } else if (statusResponse.status === 'failed') {
      throw new Error(`InstantID generation failed: ${statusResponse.error || 'Unknown error'}`);
    }
  }
  
  if (!finalResult) {
    throw new Error('Generation timed out after 120 seconds');
  }
  
  const elapsedMs = Date.now() - startTime;
  const elapsedSec = (elapsedMs / 1000).toFixed(1);
  
  log('GENERATE', 'InstantID generation complete', { 
    elapsedSec, 
    imageUrl: finalResult.output ? finalResult.output.substring(0, 50) + '...' : 'no output'
  });
  
  return {
    imageUrl: Array.isArray(finalResult.output) ? finalResult.output[0] : finalResult.output,
    elapsedMs,
    elapsedSec,
    attempts,
    settings,
    cost: 0.023, // Replicate InstantID cost
    model: 'replicate/instant-id'
  };
}

// ============================================================
// HTTP HELPERS
// ============================================================

function makeHttpRequest(options) {
  return new Promise((resolve, reject) => {
    const body = options.body;
    delete options.body;
    
    if (body) {
      options.headers = options.headers || {};
      options.headers['Content-Length'] = Buffer.byteLength(body);
    }
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(data));
        } catch {
          resolve(data);
        }
      });
    });
    
    req.on('error', reject);
    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    if (body) req.write(body);
    req.end();
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================
// REQUEST HANDLER
// ============================================================

async function handleRequest(req, res) {
  const url = new URL(req.url, `http://localhost:${PORT}`);
  
  log('HTTP', `${req.method} ${url.pathname}`);
  
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  // Serve static files
  if (req.method === 'GET' && (url.pathname === '/' || url.pathname === '/index.html')) {
    const htmlPath = path.join(__dirname, 'index.html');
    const html = fs.readFileSync(htmlPath, 'utf-8');
    res.writeHead(200, { 'Content-Type': 'text/html' });
    res.end(html);
    return;
  }
  
  // API: Health check
  if (req.method === 'GET' && url.pathname === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ 
      status: 'ok', 
      timestamp: new Date().toISOString(),
      apiKeys: {
        fal: FAL_KEY ? '✓ configured' : '✗ missing',
        google: GOOGLE_AI_KEY ? '✓ configured' : '✗ missing'
      }
    }));
    return;
  }
  
  // API: Get logs
  if (req.method === 'GET' && url.pathname === '/api/logs') {
    const generations = JSON.parse(fs.readFileSync(GENERATIONS_FILE));
    const costs = JSON.parse(fs.readFileSync(COSTS_FILE));
    const bugs = JSON.parse(fs.readFileSync(BUGS_FILE));
    
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ generations, costs, bugs }));
    return;
  }
  
  // API: Report bug
  if (req.method === 'POST' && url.pathname === '/api/bugs') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', () => {
      const bug = JSON.parse(body);
      const saved = logBug(bug);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(saved));
    });
    return;
  }
  
  // API: Generate transformation
  if (req.method === 'POST' && url.pathname === '/api/generate') {
    let body = '';
    req.on('data', chunk => body += chunk);
    req.on('end', async () => {
      try {
        const data = JSON.parse(body);
        log('API', 'Generate request received', { hasImage: !!data.image, profile: data.profile });
        
        // Validate inputs
        if (!data.image) {
          throw new Error('No image provided');
        }
        if (!data.profile) {
          throw new Error('No profile provided');
        }
        
        // Step 1: Calculate projections
        const projections = calculateProjections(data.profile, data.horizonWeeks || 12);
        
        // Step 2: Build prompt
        const prompt = buildPrompt(data.profile, projections);
        
        // Step 3: Generate image
        const generation = await generateTransformation(
          data.image.replace(/^data:image\/\w+;base64,/, ''),
          prompt,
          data.modelSettings
        );
        
        // Step 4: Log everything
        const fullResult = {
          ...generation,
          profile: data.profile,
          projections,
          prompt,
          horizonWeeks: data.horizonWeeks || 12
        };
        
        logGeneration(fullResult);
        
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: true,
          data: fullResult
        }));
        
      } catch (error) {
        log('ERROR', 'Generation failed', { error: error.message, stack: error.stack });
        res.writeHead(500, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          success: false,
          error: error.message
        }));
      }
    });
    return;
  }
  
  // 404
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found' }));
}

// ============================================================
// START SERVER
// ============================================================

const server = http.createServer(handleRequest);

server.listen(PORT, () => {
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('   PhysiqAI Founder Dashboard');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  console.log(`   🌐 URL: http://localhost:${PORT}`);
  console.log('');
  console.log('   API Keys:');
  console.log(`   - FAL_KEY: ${FAL_KEY ? '✓ configured' : '✗ MISSING'}`);
  console.log(`   - GOOGLE_AI_KEY: ${GOOGLE_AI_KEY ? '✓ configured' : '✗ MISSING'}`);
  console.log('');
  console.log('   Logs: ./logs/');
  console.log('');
  console.log('═══════════════════════════════════════════════════════════');
  console.log('');
  
  log('SERVER', `Dashboard started on port ${PORT}`);
});
