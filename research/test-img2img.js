// Test image-to-image body transformation with Gemini
const https = require('https');
const fs = require('fs');

const GOOGLE_KEY = 'AIzaSyBHijUPujDY9tmVnCAr51caEMJB4x5Bzq0';
const TEST_IMAGE_URL = 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800';

// Download image and convert to base64
function downloadImage(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : require('http');
    
    const makeRequest = (requestUrl) => {
      protocol.get(requestUrl, (res) => {
        if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
          makeRequest(res.headers.location);
          return;
        }
        
        const chunks = [];
        res.on('data', chunk => chunks.push(chunk));
        res.on('end', () => {
          const buffer = Buffer.concat(chunks);
          resolve({
            base64: buffer.toString('base64'),
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

async function testBodyTransformation(imageData) {
  console.log('Test: Body Transformation (img2img)\n');
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{
        parts: [
          {
            inlineData: {
              mimeType: imageData.mimeType,
              data: imageData.base64
            }
          },
          {
            text: "Edit this image: Make this person's arms and shoulders significantly more muscular while keeping their exact face, expression, pose, background, and clothing identical. The transformation should look like a realistic 6-month fitness transformation. Only modify the arm and shoulder muscles - everything else must stay exactly the same."
          }
        ]
      }],
      generationConfig: {
        responseModalities: ["IMAGE", "TEXT"]
      }
    }
  );
  
  console.log('Status:', result.status);
  
  if (result.data.error) {
    console.log('Error:', JSON.stringify(result.data.error, null, 2));
    return null;
  }
  
  if (result.data.candidates) {
    const parts = result.data.candidates[0]?.content?.parts || [];
    for (const part of parts) {
      if (part.inlineData) {
        console.log('SUCCESS! Got transformed image');
        console.log('MIME:', part.inlineData.mimeType);
        fs.writeFileSync('body-transform-output.png', Buffer.from(part.inlineData.data, 'base64'));
        console.log('Saved: body-transform-output.png');
        return part.inlineData;
      } else if (part.text) {
        console.log('Text response:', part.text);
      }
    }
  }
  
  console.log('Full response:', JSON.stringify(result.data, null, 2).slice(0, 2000));
  return null;
}

async function testSpecificMuscleGroups(imageData) {
  console.log('\n\nTest: Specific Muscle Group Enhancement (arms only)\n');
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{
        parts: [
          {
            inlineData: {
              mimeType: imageData.mimeType,
              data: imageData.base64
            }
          },
          {
            text: "Edit this image to show the same person with noticeably larger biceps and triceps ONLY. Do not change: face, torso size, legs, background, lighting, clothing, or pose. The arm muscles should look about 20% bigger, with more visible definition and vascularity. This should look like a real person who has been doing arm workouts for 3 months."
          }
        ]
      }],
      generationConfig: {
        responseModalities: ["IMAGE", "TEXT"]
      }
    }
  );
  
  console.log('Status:', result.status);
  
  if (result.data.candidates) {
    const parts = result.data.candidates[0]?.content?.parts || [];
    for (const part of parts) {
      if (part.inlineData) {
        console.log('SUCCESS! Got arm-specific transformation');
        fs.writeFileSync('arm-transform-output.png', Buffer.from(part.inlineData.data, 'base64'));
        console.log('Saved: arm-transform-output.png');
        return;
      } else if (part.text) {
        console.log('Text:', part.text);
      }
    }
  }
  
  if (result.data.error) {
    console.log('Error:', JSON.stringify(result.data.error, null, 2));
  }
}

async function main() {
  console.log('=== PhysiqAI Body Transformation Test ===\n');
  console.log('Downloading test image:', TEST_IMAGE_URL);
  
  const imageData = await downloadImage(TEST_IMAGE_URL);
  console.log('Image downloaded, size:', Math.round(imageData.base64.length / 1024), 'KB');
  console.log('MIME type:', imageData.mimeType);
  console.log('');
  
  // Save original for comparison
  fs.writeFileSync('original-input.jpg', Buffer.from(imageData.base64, 'base64'));
  console.log('Saved original as: original-input.jpg\n');
  
  await testBodyTransformation(imageData);
  await testSpecificMuscleGroups(imageData);
  
  console.log('\n=== Done! Compare original-input.jpg with outputs ===');
}

main().catch(console.error);
