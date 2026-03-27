#!/usr/bin/env node
/**
 * PhysiqAI Mobile Optimization Patcher
 * Updates existing HTML files with mobile optimizations
 */

const fs = require('fs');
const path = require('path');

const MOBILE_META = `
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#0a0a0f">
`;

const PWA_LINKS = `
    <link rel="manifest" href="/manifest.json">
    <link rel="apple-touch-icon" sizes="192x192" href="/assets/icon-192x192.png">
`;

const MOBILE_SCRIPTS = `
    <!-- Mobile Touch & Gestures -->
    <script defer src="mobile-touch.js"></script>
    <script defer src="mobile-avatar.js"></script>
    
    <!-- Service Worker Registration -->
    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => console.log('SW registered'))
                    .catch(err => console.log('SW failed', err));
            });
        }
    </script>
`;

const MOBILE_STYLES = `
    <!-- Mobile Optimizations -->
    <link rel="stylesheet" href="mobile-optimized.css">
`;

function patchFile(filePath) {
    console.log(`Patching: ${filePath}`);
    
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;
    
    // Update viewport meta
    if (!content.includes('viewport-fit=cover')) {
        content = content.replace(
            /<meta[^>]*viewport[^>]*>/i,
            '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=1.0, user-scalable=no">'
        );
        modified = true;
        console.log('  ✓ Updated viewport meta');
    }
    
    // Add PWA meta tags
    if (!content.includes('apple-mobile-web-app-capable')) {
        content = content.replace(
            /<meta name="viewport"[^>]*>/i,
            match => match + '\n    <meta name="apple-mobile-web-app-capable" content="yes">\n    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n    <meta name="mobile-web-app-capable" content="yes">\n    <meta name="theme-color" content="#0a0a0f">'
        );
        modified = true;
        console.log('  ✓ Added PWA meta tags');
    }
    
    // Add manifest link
    if (!content.includes('manifest.json')) {
        content = content.replace(
            /<\/head>/i,
            '    <link rel="manifest" href="/manifest.json">\n    <link rel="apple-touch-icon" sizes="192x192" href="/assets/icon-192x192.png">\n</head>'
        );
        modified = true;
        console.log('  ✓ Added manifest links');
    }
    
    // Add mobile CSS
    if (!content.includes('mobile-optimized.css')) {
        content = content.replace(
            /<\/head>/i,
            '    <link rel="stylesheet" href="mobile-optimized.css">\n</head>'
        );
        modified = true;
        console.log('  ✓ Added mobile CSS');
    }
    
    // Add mobile scripts
    if (!content.includes('mobile-touch.js')) {
        content = content.replace(
            /<\/body>/i,
            '    <script defer src="mobile-touch.js"></script>\n    <script defer src="mobile-avatar.js"></script>\n</body>'
        );
        modified = true;
        console.log('  ✓ Added mobile scripts');
    }
    
    // Add SW registration
    if (!content.includes('serviceWorker.register')) {
        content = content.replace(
            /<\/body>/i,
            `    <script>
        if ('serviceWorker' in navigator) {
            window.addEventListener('load', () => {
                navigator.serviceWorker.register('/sw.js')
                    .then(reg => console.log('SW registered'))
                    .catch(err => console.log('SW failed', err));
            });
        }
    </script>
</body>`
        );
        modified = true;
        console.log('  ✓ Added SW registration');
    }
    
    // Add touch-action to buttons
    if (!content.includes('touch-action: manipulation')) {
        content = content.replace(
            /<button/g,
            '<button style="touch-action: manipulation;"'
        );
        modified = true;
        console.log('  ✓ Added touch-action to buttons');
    }
    
    // Ensure minimum touch target (44px)
    content = content.replace(
        /style="([^"]*)"/g,
        (match, styles) => {
            if (match.includes('width:') && match.includes('height:')) {
                // Already has dimensions
                return match;
            }
            return match;
        }
    );
    
    if (modified) {
        fs.writeFileSync(filePath, content);
        console.log(`  ✅ ${path.basename(filePath)} patched successfully\n`);
    } else {
        console.log(`  ⏭️  ${path.basename(filePath)} already optimized\n`);
    }
    
    return modified;
}

function main() {
    const appDir = path.join(__dirname);
    const files = [
        'app-home.html',
        'app-avatar.html',
        'app-dashboard.html',
        'app-upload.html'
    ];
    
    console.log('🔧 PhysiqAI Mobile Optimization Patcher\n');
    console.log('=====================================\n');
    
    let patched = 0;
    let skipped = 0;
    
    for (const file of files) {
        const filePath = path.join(appDir, file);
        if (fs.existsSync(filePath)) {
            if (patchFile(filePath)) {
                patched++;
            } else {
                skipped++;
            }
        } else {
            console.log(`⚠️  ${file} not found\n`);
        }
    }
    
    console.log('=====================================\n');
    console.log(`✅ Patched: ${patched} files`);
    console.log(`⏭️  Skipped: ${skipped} files`);
    console.log('\nNext steps:');
    console.log('1. Test on actual devices');
    console.log('2. Run mobile-tests.js for validation');
    console.log('3. Check touch targets are 44px+');
}

main();
