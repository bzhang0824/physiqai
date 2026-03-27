// Test transformations on our generated image (known good face)
const https = require('https');
const fs = require('fs');

const GOOGLE_KEY = 'AIzaSyBHijUPujDY9tmVnCAr51caEMJB4x5Bzq0';

function callGoogle(endpoint, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const url = new URL(endpoint);
    const options = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    };
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, data: JSON.parse(body) }); }
        catch (e) { resolve({ status: res.statusCode, data: body }); }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function transform(imageBase64, outputName, prompt) {
  console.log(`\n→ ${outputName}`);
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{ parts: [
        { inlineData: { mimeType: 'image/png', data: imageBase64 } },
        { text: prompt }
      ]}],
      generationConfig: { responseModalities: ["IMAGE", "TEXT"] }
    }
  );
  
  if (result.data.candidates) {
    for (const part of result.data.candidates[0]?.content?.parts || []) {
      if (part.inlineData) {
        fs.writeFileSync(`${outputName}.png`, Buffer.from(part.inlineData.data, 'base64'));
        console.log(`  ✓ Saved`);
        return true;
      }
      if (part.text) console.log(`  Text: ${part.text.slice(0, 200)}`);
    }
  }
  if (result.data.error) console.log(`  ✗ ${result.data.error.message}`);
  return false;
}

async function main() {
  console.log('=== Reverse Test: Make Muscular -> Less Muscular ===\n');
  console.log('Starting from our generated muscular image...\n');
  
  // Use our earlier generated muscular image as baseline
  const muscularImage = fs.readFileSync('gemini-flash-output-0.png');
  const base64 = muscularImage.toString('base64');
  
  // Test: Make less muscular (simulating a "before" state)
  await transform(base64, 'generated-leaner',
    "Transform this muscular person to appear less muscular and more lean/skinny - " +
    "smaller arms, narrower shoulders, less defined muscles, " +
    "like they haven't been working out and have a normal slim build. " +
    "CRITICAL: Keep the EXACT same face, expression, pose, background, and clothing. " +
    "The face must be 100% identical. Photorealistic."
  );
  
  // Test: Specific change - arms only smaller
  await transform(base64, 'generated-smaller-arms',
    "Make this person's arms noticeably smaller and less muscular. " +
    "Only change the arms - everything else must stay exactly the same: " +
    "same face, same torso size, same legs, same pose, same background. " +
    "The arms should look like a beginner who just started working out."
  );
  
  // Test: Fat gain simulation
  await transform(base64, 'generated-bulkier',
    "Transform this person to have more body fat - slightly thicker midsection, " +
    "less muscle definition, softer overall appearance, like they're in a bulking phase " +
    "eating a lot. Keep the EXACT same face and pose."
  );
  
  console.log('\n=== Done - compare gemini-flash-output-0.png with outputs ===');
}

main().catch(console.error);
