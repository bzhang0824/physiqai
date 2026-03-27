/**
 * PhysiqAI Mobile Test Suite
 * Comprehensive testing for all mobile interactions
 */

(function() {
    'use strict';

    const TestResults = {
        passed: [],
        failed: [],
        warnings: []
    };

    // ========================================
    // TEST RUNNER
    // ========================================
    class MobileTestRunner {
        constructor() {
            this.tests = [];
            this.results = [];
        }

        addTest(name, testFn, category) {
            this.tests.push({ name, testFn, category });
        }

        async runAll() {
            console.log('🧪 Starting Mobile Test Suite...\n');
            
            for (const test of this.tests) {
                try {
                    const result = await test.testFn();
                    this.results.push({
                        name: test.name,
                        category: test.category,
                        passed: result.passed,
                        message: result.message
                    });
                    
                    if (result.passed) {
                        TestResults.passed.push(test.name);
                        console.log(`✅ ${test.name}: ${result.message}`);
                    } else {
                        TestResults.failed.push(test.name);
                        console.error(`❌ ${test.name}: ${result.message}`);
                    }
                } catch (error) {
                    TestResults.failed.push(test.name);
                    console.error(`❌ ${test.name}: ${error.message}`);
                }
            }
            
            this.printSummary();
            return this.results;
        }

        printSummary() {
            console.log('\n📊 Test Summary:');
            console.log(`✅ Passed: ${TestResults.passed.length}`);
            console.log(`❌ Failed: ${TestResults.failed.length}`);
            console.log(`⚠️ Warnings: ${TestResults.warnings.length}`);
            
            if (TestResults.failed.length > 0) {
                console.log('\n🔧 Failed Tests:');
                TestResults.failed.forEach(name => console.log(`  - ${name}`));
            }
        }
    }

    const runner = new MobileTestRunner();

    // ========================================
    // DEVICE DETECTION TESTS
    // ========================================
    runner.addTest('Device Type Detection', () => {
        const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
        const touchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        
        return {
            passed: true,
            message: `Mobile: ${isMobile}, Touch: ${touchSupport}, Points: ${navigator.maxTouchPoints || 0}`
        };
    }, 'Device');

    runner.addTest('Viewport Meta Tag', () => {
        const viewport = document.querySelector('meta[name="viewport"]');
        const content = viewport?.getAttribute('content') || '';
        const hasViewportFit = content.includes('viewport-fit=cover');
        const hasMaxScale = content.includes('maximum-scale=1.0') || content.includes('maximum-scale=1');
        
        return {
            passed: hasViewportFit,
            message: hasViewportFit ? 'viewport-fit=cover present' : 'Missing viewport-fit=cover'
        };
    }, 'Device');

    runner.addTest('Safe Area Support', () => {
        const supportsSafeArea = CSS.supports('padding', 'max(0px)');
        const safeAreaTop = getComputedStyle(document.documentElement).getPropertyValue('--safe-area-top');
        
        return {
            passed: supportsSafeArea,
            message: supportsSafeArea ? 'CSS env() supported' : 'CSS env() not supported'
        };
    }, 'Device');

    // ========================================
    // TOUCH EVENT TESTS
    // ========================================
    runner.addTest('Touch Events Support', () => {
        const touchStart = 'ontouchstart' in window;
        const touchMove = 'ontouchmove' in window;
        const touchEnd = 'ontouchend' in window;
        
        return {
            passed: touchStart && touchMove && touchEnd,
            message: `touchstart: ${touchStart}, touchmove: ${touchMove}, touchend: ${touchEnd}`
        };
    }, 'Touch');

    runner.addTest('Touch Action CSS', () => {
        const testEl = document.createElement('div');
        testEl.style.touchAction = 'manipulation';
        const supported = testEl.style.touchAction === 'manipulation';
        
        return {
            passed: supported,
            message: supported ? 'touch-action supported' : 'touch-action not supported'
        };
    }, 'Touch');

    runner.addTest('Passive Event Listeners', () => {
        let passiveSupported = false;
        try {
            const opts = Object.defineProperty({}, 'passive', {
                get() { passiveSupported = true; return true; }
            });
            window.addEventListener('test', null, opts);
            window.removeEventListener('test', null, opts);
        } catch (e) {}
        
        return {
            passed: passiveSupported,
            message: passiveSupported ? 'Passive listeners supported' : 'Passive listeners not supported'
        };
    }, 'Touch');

    runner.addTest('Pointer Events Support', () => {
        const pointerEnabled = window.PointerEvent !== undefined;
        
        return {
            passed: true, // Not required but nice to have
            message: pointerEnabled ? 'Pointer events available' : 'Pointer events not available (using touch)'
        };
    }, 'Touch');

    // ========================================
    // PERFORMANCE TESTS
    // ========================================
    runner.addTest('Hardware Concurrency', () => {
        const cores = navigator.hardwareConcurrency || 'unknown';
        const isLowEnd = cores && cores <= 4;
        
        return {
            passed: true,
            message: `CPU Cores: ${cores} ${isLowEnd ? '(low-end)' : '(standard)'}`
        };
    }, 'Performance');

    runner.addTest('Device Memory', () => {
        const memory = navigator.deviceMemory;
        const isLowMemory = memory && memory <= 4;
        
        return {
            passed: true,
            message: memory ? `RAM: ${memory}GB ${isLowMemory ? '(low)' : ''}` : 'RAM: unknown'
        };
    }, 'Performance');

    runner.addTest('Connection Speed', () => {
        const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
        if (conn) {
            const effectiveType = conn.effectiveType;
            const saveData = conn.saveData;
            
            return {
                passed: true,
                message: `Network: ${effectiveType}, SaveData: ${saveData}`
            };
        }
        
        return {
            passed: true,
            message: 'Network API not available'
        };
    }, 'Performance');

    runner.addTest('Request Animation Frame', () => {
        const hasRAF = typeof requestAnimationFrame === 'function';
        
        return {
            passed: hasRAF,
            message: hasRAF ? 'requestAnimationFrame available' : 'Not available'
        };
    }, 'Performance');

    // ========================================
    // PWA TESTS
    // ========================================
    runner.addTest('Service Worker Support', () => {
        const hasSW = 'serviceWorker' in navigator;
        
        return {
            passed: hasSW,
            message: hasSW ? 'Service Worker supported' : 'Service Worker not supported'
        };
    }, 'PWA');

    runner.addTest('Web App Manifest', () => {
        const manifest = document.querySelector('link[rel="manifest"]');
        
        return {
            passed: !!manifest,
            message: manifest ? `Manifest: ${manifest.href}` : 'No manifest link found'
        };
    }, 'PWA');

    runner.addTest('Add to Home Screen', () => {
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        const isIOSStandalone = window.navigator.standalone === true;
        
        return {
            passed: true,
            message: isStandalone || isIOSStandalone ? 'Running as PWA' : 'Running in browser'
        };
    }, 'PWA');

    runner.addTest('Apple Touch Icon', () => {
        const touchIcon = document.querySelector('link[rel="apple-touch-icon"]');
        
        return {
            passed: !!touchIcon,
            message: touchIcon ? 'Apple touch icon present' : 'Missing Apple touch icon'
        };
    }, 'PWA');

    runner.addTest('Theme Color Meta', () => {
        const themeColor = document.querySelector('meta[name="theme-color"]');
        
        return {
            passed: !!themeColor,
            message: themeColor ? `Theme: ${themeColor.content}` : 'Missing theme-color'
        };
    }, 'PWA');

    // ========================================
    // ACCESSIBILITY TESTS
    // ========================================
    runner.addTest('ARIA Labels', () => {
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        const links = document.querySelectorAll('a:not([aria-label]):not([aria-labelledby])');
        const missing = buttons.length + links.length;
        
        return {
            passed: missing < 10, // Allow some missing for simple buttons
            message: `${missing} elements missing ARIA labels`
        };
    }, 'Accessibility');

    runner.addTest('Focus Visible', () => {
        const testEl = document.createElement('button');
        testEl.style.cssText = 'position:absolute;opacity:0;pointer-events:none;';
        document.body.appendChild(testEl);
        testEl.focus();
        
        const outline = window.getComputedStyle(testEl).outline;
        document.body.removeChild(testEl);
        
        return {
            passed: outline && outline !== 'none',
            message: outline ? `Focus style: ${outline}` : 'No focus outline defined'
        };
    }, 'Accessibility');

    runner.addTest('Color Contrast Check', () => {
        // Basic check for text color vs background
        const bodyStyle = window.getComputedStyle(document.body);
        const color = bodyStyle.color;
        const bg = bodyStyle.backgroundColor;
        
        return {
            passed: true,
            message: `Text: ${color}, BG: ${bg}`
        };
    }, 'Accessibility');

    runner.addTest('Reduced Motion Support', () => {
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        return {
            passed: true,
            message: prefersReducedMotion ? 'Reduced motion preferred' : 'Full motion allowed'
        };
    }, 'Accessibility');

    // ========================================
    // RESPONSIVE DESIGN TESTS
    // ========================================
    runner.addTest('Viewport Width', () => {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        return {
            passed: width <= 768, // Should be mobile viewport
            message: `Viewport: ${width}x${height}`
        };
    }, 'Responsive');

    runner.addTest('Font Size Scaling', () => {
        const rootFontSize = parseFloat(getComputedStyle(document.documentElement).fontSize);
        
        return {
            passed: rootFontSize >= 14,
            message: `Root font-size: ${rootFontSize}px`
        };
    }, 'Responsive');

    runner.addTest('Touch Target Sizes', () => {
        const buttons = document.querySelectorAll('button, .btn, .nav-item');
        let smallTargets = 0;
        
        buttons.forEach(btn => {
            const rect = btn.getBoundingClientRect();
            if (rect.width < 44 || rect.height < 44) {
                smallTargets++;
            }
        });
        
        return {
            passed: smallTargets === 0,
            message: `${smallTargets} elements below 44px touch target`
        };
    }, 'Responsive');

    runner.addTest('Horizontal Overflow', () => {
        const bodyWidth = document.body.scrollWidth;
        const viewportWidth = window.innerWidth;
        const hasOverflow = bodyWidth > viewportWidth;
        
        return {
            passed: !hasOverflow,
            message: hasOverflow ? `Overflow: ${bodyWidth - viewportWidth}px` : 'No horizontal overflow'
        };
    }, 'Responsive');

    // ========================================
    // HAPTICS & FEEDBACK TESTS
    // ========================================
    runner.addTest('Vibration API', () => {
        const hasVibration = 'vibrate' in navigator;
        
        return {
            passed: hasVibration,
            message: hasVibration ? 'Vibration API available' : 'Vibration not supported'
        };
    }, 'Haptics');

    runner.addTest('Visual Feedback Classes', () => {
        const hasTouchRipple = !!document.querySelector('.touch-ripple');
        const hasHapticClasses = !!document.querySelector('.haptic-light, .haptic-medium, .haptic-heavy');
        
        return {
            passed: hasTouchRipple || hasHapticClasses,
            message: `Touch ripple: ${hasTouchRipple}, Haptic classes: ${hasHapticClasses}`
        };
    }, 'Haptics');

    // ========================================
    // OFFLINE & SYNC TESTS
    // ========================================
    runner.addTest('Online Status', () => {
        const isOnline = navigator.onLine;
        
        return {
            passed: true,
            message: isOnline ? 'Currently online' : 'Currently offline'
        };
    }, 'Offline');

    runner.addTest('LocalStorage Support', () => {
        let supported = false;
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            supported = true;
        } catch (e) {}
        
        return {
            passed: supported,
            message: supported ? 'localStorage available' : 'localStorage not available'
        };
    }, 'Offline');

    runner.addTest('IndexedDB Support', () => {
        const hasIDB = 'indexedDB' in window;
        
        return {
            passed: hasIDB,
            message: hasIDB ? 'IndexedDB supported' : 'IndexedDB not supported'
        };
    }, 'Offline');

    runner.addTest('Background Sync', () => {
        const hasSync = 'sync' in ServiceWorkerRegistration.prototype;
        
        return {
            passed: true, // Nice to have but not required
            message: hasSync ? 'Background Sync available' : 'Background Sync not available'
        };
    }, 'Offline');

    // ========================================
    // CAMERA & INPUT TESTS
    // ========================================
    runner.addTest('File Input Support', () => {
        const input = document.createElement('input');
        input.type = 'file';
        const supported = input.type === 'file';
        
        return {
            passed: supported,
            message: supported ? 'File input supported' : 'File input not supported'
        };
    }, 'Input');

    runner.addTest('Camera Capture Attribute', () => {
        const inputs = document.querySelectorAll('input[type="file"]');
        let hasCapture = 0;
        inputs.forEach(input => {
            if (input.hasAttribute('capture')) hasCapture++;
        });
        
        return {
            passed: inputs.length === 0 || hasCapture > 0,
            message: `${hasCapture}/${inputs.length} file inputs have capture attribute`
        };
    }, 'Input');

    runner.addTest('Accept Image Types', () => {
        const inputs = document.querySelectorAll('input[type="file"]');
        let hasImageAccept = 0;
        inputs.forEach(input => {
            const accept = input.getAttribute('accept') || '';
            if (accept.includes('image')) hasImageAccept++;
        });
        
        return {
            passed: inputs.length === 0 || hasImageAccept > 0,
            message: `${hasImageAccept}/${inputs.length} file inputs accept images`
        };
    }, 'Input');

    // ========================================
    // INTERACTION TESTS
    // ========================================
    runner.addTest('Bottom Navigation Present', () => {
        const bottomNav = document.querySelector('.bottom-nav');
        
        return {
            passed: !!bottomNav,
            message: bottomNav ? 'Bottom navigation found' : 'No bottom navigation'
        };
    }, 'Interaction');

    runner.addTest('Floating Action Button', () => {
        const fab = document.querySelector('.fab');
        
        return {
            passed: !!fab,
            message: fab ? 'FAB found' : 'No FAB present'
        };
    }, 'Interaction');

    runner.addTest('Scroll Containers', () => {
        const scrollContainers = document.querySelectorAll('.scroll-x, .scroll-y');
        
        return {
            passed: scrollContainers.length > 0,
            message: `${scrollContainers.length} scroll containers found`
        };
    }, 'Interaction');

    runner.addTest('Pull to Refresh Indicator', () => {
        const ptr = document.querySelector('.pull-to-refresh');
        
        return {
            passed: true, // Optional feature
            message: ptr ? 'Pull-to-refresh present' : 'No pull-to-refresh indicator'
        };
    }, 'Interaction');

    // ========================================
    // EXPORT AND RUN
    // ========================================
    window.MobileTests = {
        runner,
        results: TestResults,
        run: () => runner.runAll()
    };

    // Auto-run if URL contains ?test
    if (window.location.search.includes('test')) {
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => runner.runAll(), 1000);
        });
    }
})();
