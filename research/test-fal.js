// Test fal.ai image transformation capabilities
const https = require('https');
const fs = require('fs');

const FAL_KEY = 'e37a91e9-ad07-457d-8168-b8916c3cebc0:1241c52b5aa972d79e24be35c8845c59';

// Test image - fitness stock photo (male physique, front pose)
const TEST_IMAGE_URL = 'https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=512';

async function callFal(endpoint, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    
    const options = {
      hostname: 'queue.fal.run',
      path: endpoint,
      method: 'POST',
      headers: {
        'Authorization': `Key ${FAL_KEY}`,
        'Content-Type': 'application/json',
        'Content-Length': data.length
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

async function testGrokImagine() {
  console.log('Testing Grok Imagine Image Edit...\n');
  
  const result = await callFal('/fal-ai/grok-2-image/image-to-image', {
    image_url: TEST_IMAGE_URL,
    prompt: "Same person but with noticeably more muscular arms and broader shoulders, maintaining exact face and pose, photorealistic fitness transformation",
    strength: 0.6
  });
  
  console.log('Grok Result:', JSON.stringify(result, null, 2));
  return result;
}

async function testFluxImg2Img() {
  console.log('\nTesting Flux img2img...\n');
  
  const result = await callFal('/fal-ai/flux/dev/image-to-image', {
    image_url: TEST_IMAGE_URL,
    prompt: "Athletic muscular male with defined biceps and chest, same pose and setting, photorealistic",
    strength: 0.5,
    num_inference_steps: 28
  });
  
  console.log('Flux Result:', JSON.stringify(result, null, 2));
  return result;
}

async function main() {
  console.log('=== PhysiqAI Avatar Prototype Tests ===\n');
  console.log('Test image:', TEST_IMAGE_URL, '\n');
  
  try {
    await testGrokImagine();
  } catch (e) {
    console.log('Grok error:', e.message);
  }
  
  try {
    await testFluxImg2Img();
  } catch (e) {
    console.log('Flux error:', e.message);
  }
}

main();
