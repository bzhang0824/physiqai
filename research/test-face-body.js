// Test with full body front-facing photo (face + body visible)
const https = require('https');
const fs = require('fs');

const GOOGLE_KEY = 'AIzaSyBHijUPujDY9tmVnCAr51caEMJB4x5Bzq0';

// Front-facing fitness photo with face visible
const TEST_IMAGES = [
  // Shirtless guy, front pose, face visible - average build
  'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800',
  // Male in tank top, gym setting
  'https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800'
];

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
        res.on('error', reject);
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
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data)
      }
    };
    const req = https.request(options, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, data: JSON.parse(body) });
        } catch (e) {
          resolve({ status: res.statusCode, data: body });
        }
      });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

async function transformBody(imageData, outputPrefix, prompt) {
  console.log(`\nTransformation: ${outputPrefix}`);
  console.log(`Prompt: ${prompt.slice(0, 100)}...`);
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{
        parts: [
          { inlineData: { mimeType: imageData.mimeType, data: imageData.base64 } },
          { text: prompt }
        ]
      }],
      generationConfig: { responseModalities: ["IMAGE", "TEXT"] }
    }
  );
  
  if (result.data.candidates) {
    const parts = result.data.candidates[0]?.content?.parts || [];
    for (const part of parts) {
      if (part.inlineData) {
        const filename = `${outputPrefix}.png`;
        fs.writeFileSync(filename, Buffer.from(part.inlineData.data, 'base64'));
        console.log(`✓ Saved: ${filename}`);
        return true;
      }
      if (part.text) console.log(`Text: ${part.text}`);
    }
  }
  
  if (result.data.error) {
    console.log(`✗ Error: ${result.data.error.message}`);
  }
  return false;
}

async function main() {
  console.log('=== Face + Body Transformation Tests ===\n');
  
  // Test with first image
  console.log('Downloading test image...');
  const imageData = await downloadImage(TEST_IMAGES[0]);
  console.log('Image size:', Math.round(imageData.base64.length / 1024), 'KB');
  
  // Save original
  fs.writeFileSync('face-body-original.jpg', Buffer.from(imageData.base64, 'base64'));
  console.log('Saved: face-body-original.jpg');
  
  // Test 1: Dramatic transformation (6 months)
  await transformBody(imageData, 'face-body-6month', 
    "Edit this image to show this EXACT same person after 6 months of intense bodybuilding. " +
    "Make their muscles significantly larger - bigger arms, broader shoulders, more defined chest and abs. " +
    "CRITICAL: Keep the exact same face, facial expression, hair, and background. " +
    "The face must be 100% identical. Only the body should change. Photorealistic quality."
  );
  
  // Test 2: Subtle transformation (3 months)
  await transformBody(imageData, 'face-body-3month',
    "Edit this image to show this EXACT same person after 3 months of consistent gym workouts. " +
    "Subtle but noticeable improvements: slightly bigger arms, more shoulder definition, hint of abs. " +
    "CRITICAL: The face must remain completely identical - same person, same expression. " +
    "The transformation should look realistic and achievable, not dramatic."
  );
  
  // Test 3: Regression (what if they stopped working out)
  await transformBody(imageData, 'face-body-regression',
    "Edit this image to show what this EXACT same person would look like if they stopped exercising " +
    "for 3 months - slightly softer muscles, less definition, small amount of fat gain around midsection. " +
    "CRITICAL: Keep the exact same face. The regression should be subtle but noticeable."
  );
  
  console.log('\n=== Compare all outputs with face-body-original.jpg ===');
}

main().catch(console.error);
