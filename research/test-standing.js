// Test with clear standing front pose (face fully visible)
const https = require('https');
const fs = require('fs');

const GOOGLE_KEY = 'AIzaSyBHijUPujDY9tmVnCAr51caEMJB4x5Bzq0';

// Standing front pose with clear face
const TEST_IMAGE = 'https://images.unsplash.com/photo-1581009146145-b5ef050c149a?w=800';

function downloadImage(url) {
  return new Promise((resolve, reject) => {
    const makeRequest = (requestUrl) => {
      https.get(requestUrl, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          makeRequest(res.headers.location);
          return;
        }
        const chunks = [];
        res.on('data', chunk => chunks.push(chunk));
        res.on('end', () => {
          resolve({
            base64: Buffer.concat(chunks).toString('base64'),
            mimeType: res.headers['content-type'] || 'image/jpeg'
          });
        });
      }).on('error', reject);
    };
    makeRequest(url);
  });
}

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

async function transform(imageData, outputName, prompt) {
  console.log(`\n→ ${outputName}`);
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{ parts: [
        { inlineData: { mimeType: imageData.mimeType, data: imageData.base64 } },
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
  console.log('=== Standing Pose Test (Face Preservation) ===\n');
  
  const imageData = await downloadImage(TEST_IMAGE);
  fs.writeFileSync('standing-original.jpg', Buffer.from(imageData.base64, 'base64'));
  console.log('Original saved: standing-original.jpg');
  
  // Key test: dramatic transformation while preserving exact face
  await transform(imageData, 'standing-muscular',
    "Transform this person to be significantly more muscular - " +
    "bigger biceps, broader shoulders, more defined chest and abs, " +
    "thicker legs. They should look like they've been bodybuilding for a year. " +
    "ABSOLUTELY CRITICAL: The face MUST remain EXACTLY identical - " +
    "same facial features, same expression, same skin tone, same eyes. " +
    "Keep the exact same pose, background, lighting, and clothing. " +
    "Only the body should change. Photorealistic quality."
  );
  
  // Test: specific muscle groups only
  await transform(imageData, 'standing-arms-only',
    "Make ONLY this person's arms more muscular - bigger biceps and triceps. " +
    "Do NOT change: face (must be identical), torso, legs, clothing, background, pose. " +
    "The arms should look noticeably bigger, like 3 months of arm-focused training."
  );
  
  console.log('\n=== Done - compare standing-original.jpg with outputs ===');
}

main().catch(console.error);
