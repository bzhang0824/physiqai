// Test Google Gemini/Imagen for body transformation
const https = require('https');

const GOOGLE_KEY = 'AIzaSyBHijUPujDY9tmVnCAr51caEMJB4x5Bzq0';
const TEST_IMAGE = 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=512';

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

// Fetch image and convert to base64
async function fetchImageAsBase64(url) {
  return new Promise((resolve, reject) => {
    const parsedUrl = new URL(url);
    const protocol = parsedUrl.protocol === 'https:' ? https : require('http');
    
    protocol.get(url, (res) => {
      if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
        // Follow redirect
        return fetchImageAsBase64(res.headers.location).then(resolve).catch(reject);
      }
      
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        resolve(buffer.toString('base64'));
      });
      res.on('error', reject);
    }).on('error', reject);
  });
}

async function testGeminiImageEdit() {
  console.log('Test 1: Gemini 2.0 Flash Image Generation\n');
  
  // First test: text-to-image (generate a muscular person)
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{
        parts: [{
          text: "Generate a photorealistic image of an athletic muscular male fitness model, front pose, defined arms and chest, gym setting, high quality photograph"
        }]
      }],
      generationConfig: {
        responseModalities: ["TEXT", "IMAGE"]
      }
    }
  );
  
  console.log('Gemini Result status:', result.status);
  if (result.data.error) {
    console.log('Error:', JSON.stringify(result.data.error, null, 2));
  } else if (result.data.candidates) {
    const parts = result.data.candidates[0]?.content?.parts || [];
    for (const part of parts) {
      if (part.inlineData) {
        console.log('Got image! MIME type:', part.inlineData.mimeType);
        console.log('Base64 length:', part.inlineData.data?.length || 0);
        // Save to file
        if (part.inlineData.data) {
          const fs = require('fs');
          fs.writeFileSync('gemini-output.png', Buffer.from(part.inlineData.data, 'base64'));
          console.log('Saved to gemini-output.png');
        }
      } else if (part.text) {
        console.log('Text response:', part.text.slice(0, 500));
      }
    }
  } else {
    console.log('Response:', JSON.stringify(result.data, null, 2).slice(0, 1000));
  }
  
  return result;
}

async function testImagena3() {
  console.log('\n\nTest 2: Imagen 3 (if available)\n');
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key=${GOOGLE_KEY}`,
    {
      instances: [{
        prompt: "Photorealistic athletic muscular male fitness model with defined biceps and chest, gym setting, professional fitness photography"
      }],
      parameters: {
        sampleCount: 1
      }
    }
  );
  
  console.log('Imagen 3 status:', result.status);
  console.log('Response:', JSON.stringify(result.data, null, 2).slice(0, 1000));
}

async function main() {
  console.log('=== Google AI Tests for PhysiqAI ===\n');
  
  // List available models first
  console.log('Checking available models...\n');
  const models = await new Promise((resolve, reject) => {
    https.get(`https://generativelanguage.googleapis.com/v1beta/models?key=${GOOGLE_KEY}`, (res) => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => resolve(JSON.parse(body)));
    }).on('error', reject);
  });
  
  const imageModels = models.models?.filter(m => 
    m.name.includes('imagen') || 
    m.supportedGenerationMethods?.includes('generateImage') ||
    m.name.includes('gemini-2')
  ) || [];
  
  console.log('Image-capable models:', imageModels.map(m => m.name).join(', ') || 'None found');
  console.log('');
  
  await testGeminiImageEdit();
  // await testImagena3();
}

main().catch(console.error);
