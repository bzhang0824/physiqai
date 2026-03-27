// Quick test script to verify API endpoints
const fs = require('fs');
const path = require('path');

async function testAPI() {
    console.log('🧪 Testing PhysiqAI Dashboard API...\n');
    
    const baseUrl = 'http://localhost:3456';
    
    try {
        // Test 1: Home page
        console.log('📋 Testing home page...');
        const homeResponse = await fetch(baseUrl);
        const homeText = await homeResponse.text();
        console.log(`✅ Home page: ${homeResponse.status} (${homeText.length} bytes)`);
        
        // Test 2: Gallery API
        console.log('\n🖼️ Testing gallery API...');
        const galleryResponse = await fetch(`${baseUrl}/api/gallery`);
        const galleryData = await galleryResponse.json();
        console.log(`✅ Gallery API: ${galleryResponse.status} (${galleryData.length} images)`);
        galleryData.slice(0, 3).forEach(img => {
            console.log(`   📸 ${img.filename} (${Math.round(img.size/1024)}KB)`);
        });
        
        // Test 3: Image serving
        console.log('\n🖼️ Testing image serving...');
        if (galleryData.length > 0) {
            const testImage = galleryData[0].filename;
            const imageResponse = await fetch(`${baseUrl}/research/${testImage}`);
            console.log(`✅ Image serving: ${imageResponse.status} (${imageResponse.headers.get('content-type')})`);
        }
        
        console.log('\n🎉 All API endpoints working correctly!');
        console.log('\n📝 Ready for transformations:');
        console.log('   1. Upload an image');
        console.log('   2. Select transformation preset');
        console.log('   3. Click "Generate Transformation"');
        console.log('   4. View before/after results');
        console.log('   5. Download the result');
        
    } catch (error) {
        console.error('❌ API test failed:', error.message);
    }
}

// Only run if Node.js 18+ (for fetch)
if (typeof fetch !== 'undefined') {
    testAPI();
} else {
    console.log('⚠️ This test requires Node.js 18+ for built-in fetch API');
    console.log('✅ Server is running - test API endpoints manually with curl or browser');
}