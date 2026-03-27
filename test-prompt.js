/**
 * PhysiqAI Prompt Testing Script
 * 
 * Usage: node test-prompt.js <image-path> [horizon-weeks]
 * Example: node test-prompt.js test-images/male-lean-front.jpg 12
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// Load environment variables
require('dotenv').config();

const FAL_KEY = process.env.FAL_KEY;

if (!FAL_KEY) {
  console.error('❌ FAL_KEY not found in environment. Check your .env file.');
  process.exit(1);
}

// Test configuration - modify these for different tests
const TEST_CONFIG = {
  // User profile (adjust per test)
  profile: {
    age: 26,
    gender: 'male',
    ethnicity: 'white',
    heightCm: 178,
    weightKg: 75,
    bodyFatPercent: 18,
    experienceLevel: 'beginner', // beginner, intermediate, advanced
    split: 'ppl',
    focusAreas: ['chest', 'arms'],
    workoutsPerWeek: 5,
    cardioPerWeek: 2,
    sleepQuality: 'average', // poor, average, good
    nutritionGoal: 'bulk', // cut, maintain, bulk
  },
  
  // Model settings
  model: {
    guidance_scale: 7.5,
    num_inference_steps: 38,
  }
};

// Prompt templates - the core of what we're testing
function buildPrompt(profile, horizonWeeks) {
  const timeDesc = horizonWeeks <= 12 
    ? `${horizonWeeks} weeks` 
    : `${Math.round(horizonWeeks / 4)} months`;
  
  // Calculate projected changes (simplified for testing)
  const monthlyGainKg = profile.experienceLevel === 'beginner' ? 0.9 
    : profile.experienceLevel === 'intermediate' ? 0.45 : 0.22;
  const months = horizonWeeks / 4;
  const totalGainKg = monthlyGainKg * months;
  const totalGainLbs = Math.round(totalGainKg * 2.2);
  
  const focusDesc = profile.focusAreas.join(', ');
  
  return `Keep the exact same face, facial features, skin tone, and all distinguishing characteristics. Maintain the identical pose, camera angle, lighting, and background.

Transform this person's physique to show ${timeDesc} of dedicated strength training:

MUSCLE CHANGES:
- Add approximately ${totalGainLbs} pounds of lean muscle
- Emphasize muscle development in the ${focusDesc}
- Show fuller, more developed muscles in focused areas
- Slight improvements in overall musculature

BODY COMPOSITION:
${profile.nutritionGoal === 'cut' ? '- Reduce body fat, showing increased definition and vascularity' : ''}
${profile.nutritionGoal === 'bulk' ? '- Show fuller muscles, maintaining current body fat level' : ''}
${profile.nutritionGoal === 'maintain' ? '- Slight body recomposition, marginally leaner with more muscle' : ''}

CONSTRAINTS:
- The transformation must look like a realistic "${timeDesc}" after photo
- This should be achievable naturally, not enhanced proportions
- Preserve all tattoos, scars, body hair, and markings exactly
- Do not change clothing, background, or accessories
- Maintain the exact same skin tone and complexion`;
}

async function testPrompt(imagePath, horizonWeeks = 12) {
  console.log('\n🏋️ PhysiqAI Prompt Tester\n');
  console.log('━'.repeat(50));
  
  // Check image exists
  if (!fs.existsSync(imagePath)) {
    console.error(`❌ Image not found: ${imagePath}`);
    process.exit(1);
  }
  
  // Read and encode image
  console.log(`📸 Loading image: ${imagePath}`);
  const imageBuffer = fs.readFileSync(imagePath);
  const base64Image = imageBuffer.toString('base64');
  const mimeType = imagePath.endsWith('.png') ? 'image/png' : 'image/jpeg';
  
  // Build prompt
  const prompt = buildPrompt(TEST_CONFIG.profile, horizonWeeks);
  
  console.log(`\n📝 Prompt (${horizonWeeks} weeks):\n`);
  console.log('─'.repeat(50));
  console.log(prompt);
  console.log('─'.repeat(50));
  
  console.log(`\n⚙️  Model settings:`);
  console.log(`   guidance_scale: ${TEST_CONFIG.model.guidance_scale}`);
  console.log(`   num_inference_steps: ${TEST_CONFIG.model.num_inference_steps}`);
  
  console.log(`\n🚀 Calling fal.ai Flux Kontext Pro...`);
  console.log(`   (This takes 25-40 seconds)\n`);
  
  const startTime = Date.now();
  
  try {
    const result = await callFalApi({
      image: `data:${mimeType};base64,${base64Image}`,
      prompt: prompt,
      guidance_scale: TEST_CONFIG.model.guidance_scale,
      num_inference_steps: TEST_CONFIG.model.num_inference_steps,
    });
    
    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log(`✅ Generation complete in ${elapsed}s`);
    console.log(`\n🖼️  Result URL:`);
    console.log(result.images[0].url);
    
    // Save output
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const baseName = path.basename(imagePath, path.extname(imagePath));
    const outputName = `${baseName}_${horizonWeeks}wk_${timestamp}`;
    
    // Ensure output directory exists
    const outputDir = path.join(path.dirname(imagePath), '..', 'test-outputs');
    if (!fs.existsSync(outputDir)) {
      fs.mkdirSync(outputDir, { recursive: true });
    }
    
    // Download and save the generated image
    const outputPath = path.join(outputDir, `${outputName}.jpg`);
    await downloadImage(result.images[0].url, outputPath);
    
    console.log(`\n💾 Saved to: ${outputPath}`);
    
    // Save metadata
    const metaPath = path.join(outputDir, `${outputName}.json`);
    fs.writeFileSync(metaPath, JSON.stringify({
      input: {
        image: imagePath,
        horizonWeeks,
        profile: TEST_CONFIG.profile,
      },
      prompt,
      modelSettings: TEST_CONFIG.model,
      result: {
        url: result.images[0].url,
        generationTimeSeconds: parseFloat(elapsed),
      },
      timestamp: new Date().toISOString(),
    }, null, 2));
    
    console.log(`📋 Metadata: ${metaPath}`);
    console.log('\n' + '━'.repeat(50));
    console.log('Done! Compare original and generated images.');
    console.log('━'.repeat(50) + '\n');
    
    return { outputPath, elapsed, url: result.images[0].url };
    
  } catch (error) {
    console.error(`\n❌ Generation failed:`, error.message);
    if (error.response) {
      console.error('Response:', error.response);
    }
    process.exit(1);
  }
}

async function callFalApi(input) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify({ input });
    
    const options = {
      hostname: 'fal.run',
      path: '/fal-ai/flux-kontext/pro',
      method: 'POST',
      headers: {
        'Authorization': `Key ${FAL_KEY}`,
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
      },
    };
    
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(body));
        } else {
          reject({ message: `API error: ${res.statusCode}`, response: body });
        }
      });
    });
    
    req.on('error', reject);
    req.setTimeout(120000, () => {
      req.destroy();
      reject(new Error('Request timeout (120s)'));
    });
    
    req.write(data);
    req.end();
  });
}

async function downloadImage(url, outputPath) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(outputPath);
    https.get(url, (response) => {
      response.pipe(file);
      file.on('finish', () => {
        file.close();
        resolve();
      });
    }).on('error', (err) => {
      fs.unlink(outputPath, () => {});
      reject(err);
    });
  });
}

// Export for use as module
module.exports = { testPrompt, buildPrompt, TEST_CONFIG };

// Run if called directly
if (require.main === module) {
  const args = process.argv.slice(2);
  if (args.length === 0) {
    console.log(`
Usage: node test-prompt.js <image-path> [horizon-weeks]

Examples:
  node test-prompt.js test-images/male-lean-front.jpg
  node test-prompt.js test-images/male-lean-front.jpg 12
  node test-prompt.js test-images/female-avg-side.jpg 26

Edit TEST_CONFIG in this file to change user profile settings.
`);
    process.exit(0);
  }

  const imagePath = args[0];
  const horizonWeeks = parseInt(args[1]) || 12;

  testPrompt(imagePath, horizonWeeks);
}
