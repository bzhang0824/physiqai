// Test Google Imagen 4.0 for body transformation
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

async function testImagen4() {
  console.log('Test: Imagen 4.0 Generate\n');
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:generateImages?key=${GOOGLE_KEY}`,
    {
      prompt: "Photorealistic photograph of an athletic muscular male fitness model with well-defined biceps and chest muscles, front pose, natural gym lighting, professional fitness photography, high detail",
      config: {
        numberOfImages: 1
      }
    }
  );
  
  console.log('Imagen 4 status:', result.status);
  
  if (result.data.error) {
    console.log('Error:', JSON.stringify(result.data.error, null, 2));
  } else if (result.data.generatedImages) {
    console.log('Success! Generated', result.data.generatedImages.length, 'image(s)');
    result.data.generatedImages.forEach((img, i) => {
      if (img.image?.imageBytes) {
        const filename = `imagen4-output-${i}.png`;
        fs.writeFileSync(filename, Buffer.from(img.image.imageBytes, 'base64'));
        console.log(`Saved: ${filename}`);
      }
    });
  } else {
    console.log('Response:', JSON.stringify(result.data, null, 2).slice(0, 2000));
  }
  
  return result;
}

async function testGeminiFlashImage() {
  console.log('\n\nTest: Gemini 2.5 Flash Image Generation\n');
  
  const result = await callGoogle(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-image:generateContent?key=${GOOGLE_KEY}`,
    {
      contents: [{
        parts: [{
          text: "Generate an image: Photorealistic photograph of an athletic muscular male fitness model with defined biceps and chest, front pose, gym setting"
        }]
      }],
      generationConfig: {
        responseModalities: ["IMAGE", "TEXT"]
      }
    }
  );
  
  console.log('Gemini Flash Image status:', result.status);
  
  if (result.data.error) {
    console.log('Error:', JSON.stringify(result.data.error, null, 2));
  } else if (result.data.candidates) {
    const parts = result.data.candidates[0]?.content?.parts || [];
    parts.forEach((part, i) => {
      if (part.inlineData) {
        console.log('Got image! MIME:', part.inlineData.mimeType);
        const filename = `gemini-flash-output-${i}.png`;
        fs.writeFileSync(filename, Buffer.from(part.inlineData.data, 'base64'));
        console.log(`Saved: ${filename}`);
      } else if (part.text) {
        console.log('Text:', part.text.slice(0, 300));
      }
    });
  } else {
    console.log('Response:', JSON.stringify(result.data, null, 2).slice(0, 1500));
  }
}

async function main() {
  console.log('=== Imagen/Gemini Image Generation Tests ===\n');
  
  await testImagen4();
  await testGeminiFlashImage();
}

main().catch(console.error);
