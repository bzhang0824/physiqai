/**
 * PhysiqAI - QA Test Suite
 * Automated testing for demo flows
 */

const QATests = {
    results: [],
    
    log(test, passed, message = '') {
        const result = { test, passed, message, timestamp: new Date().toISOString() };
        this.results.push(result);
        const icon = passed ? '✓' : '✗';
        const color = passed ? 'color: #10b981' : 'color: #ef4444';
        console.log(`%c${icon} ${test}`, color, message);
        return result;
    },
    
    // Test 1: Page Load Tests
    async testPageLoads() {
        const pages = ['index.html', 'dashboard.html', 'avatar.html', 'upload.html'];
        let allPassed = true;
        
        for (const page of pages) {
            try {
                const response = await fetch(page, { method: 'HEAD' });
                this.log(`Page Load: ${page}`, response.ok, response.statusText);
                if (!response.ok) allPassed = false;
            } catch (error) {
                this.log(`Page Load: ${page}`, false, error.message);
                allPassed = false;
            }
        }
        
        return allPassed;
    },
    
    // Test 2: Demo Data Load
    async testDemoData() {
        try {
            const response = await fetch('../data/demo-data.json');
            const data = await response.json();
            
            const hasUsers = data.demoUsers && data.demoUsers.length === 3;
            this.log('Demo Data: Has 3 users', hasUsers, `Found ${data.demoUsers?.length || 0} users`);
            
            const hasComparisons = data.comparisonData?.beforeAfter?.length === 3;
            this.log('Demo Data: Has comparisons', hasComparisons);
            
            const hasShowcase = data.landingPageShowcase?.heroTransformations?.length > 0;
            this.log('Demo Data: Has showcase', hasShowcase);
            
            return hasUsers && hasComparisons && hasShowcase;
        } catch (error) {
            this.log('Demo Data Load', false, error.message);
            return false;
        }
    },
    
    // Test 3: Demo Loader Initialization
    testDemoLoader() {
        const hasDemoLoader = typeof DemoLoader !== 'undefined';
        this.log('DemoLoader: Exists', hasDemoLoader);
        
        if (hasDemoLoader) {
            const hasInit = typeof DemoLoader.init === 'function';
            this.log('DemoLoader: Has init()', hasInit);
            
            const hasGetUser = typeof DemoLoader.getUser === 'function';
            this.log('DemoLoader: Has getUser()', hasGetUser);
            
            return hasInit && hasGetUser;
        }
        
        return false;
    },
    
    // Test 4: Toast System
    testToastSystem() {
        const hasToast = typeof ToastSystem !== 'undefined';
        this.log('ToastSystem: Exists', hasToast);
        
        if (hasToast) {
            // Test showing a toast
            const id = ToastSystem.info('QA Test Toast');
            const toastShown = document.querySelector('.toast') !== null;
            this.log('ToastSystem: Shows toast', toastShown);
            
            // Clean up
            ToastSystem.clear();
            
            return toastShown;
        }
        
        return false;
    },
    
    // Test 5: Error Handler
    testErrorHandler() {
        const hasErrorHandler = typeof ErrorHandler !== 'undefined';
        this.log('ErrorHandler: Exists', hasErrorHandler);
        
        if (hasErrorHandler) {
            const hasStorage = typeof ErrorHandler.storage !== 'undefined';
            this.log('ErrorHandler: Has storage module', hasStorage);
            
            const hasAPI = typeof ErrorHandler.api !== 'undefined';
            this.log('ErrorHandler: Has API module', hasAPI);
            
            return hasStorage && hasAPI;
        }
        
        return false;
    },
    
    // Test 6: LocalStorage
    testLocalStorage() {
        try {
            const testKey = '__qa_test__';
            const testValue = { test: true, timestamp: Date.now() };
            
            localStorage.setItem(testKey, JSON.stringify(testValue));
            const retrieved = JSON.parse(localStorage.getItem(testKey));
            localStorage.removeItem(testKey);
            
            const success = retrieved.test === true;
            this.log('LocalStorage: Read/Write', success);
            
            return success;
        } catch (error) {
            this.log('LocalStorage: Read/Write', false, error.message);
            return false;
        }
    },
    
    // Test 7: Session Storage
    testSessionStorage() {
        try {
            const testKey = '__qa_session_test__';
            sessionStorage.setItem(testKey, 'test');
            const value = sessionStorage.getItem(testKey);
            sessionStorage.removeItem(testKey);
            
            const success = value === 'test';
            this.log('SessionStorage: Read/Write', success);
            
            return success;
        } catch (error) {
            this.log('SessionStorage: Read/Write', false, error.message);
            return false;
        }
    },
    
    // Test 8: CSS Variables
    testCSSVariables() {
        const styles = getComputedStyle(document.documentElement);
        const primary = styles.getPropertyValue('--primary').trim();
        const hasPrimary = primary !== '';
        
        this.log('CSS: Primary variable exists', hasPrimary, primary);
        
        return hasPrimary;
    },
    
    // Test 9: Responsive Breakpoints
    testResponsive() {
        const width = window.innerWidth;
        const isMobile = width < 768;
        const isTablet = width >= 768 && width < 1024;
        const isDesktop = width >= 1024;
        
        this.log(`Responsive: Viewport ${width}px`, true, 
            `Mobile: ${isMobile}, Tablet: ${isTablet}, Desktop: ${isDesktop}`);
        
        return true;
    },
    
    // Test 10: Three.js Availability
    testThreeJS() {
        const hasThree = typeof THREE !== 'undefined';
        this.log('Three.js: Loaded', hasThree);
        
        if (hasThree) {
            const hasScene = typeof THREE.Scene === 'function';
            this.log('Three.js: Scene available', hasScene);
            
            return hasScene;
        }
        
        return false;
    },
    
    // Test 11: WebGL Support
    testWebGL() {
        try {
            const canvas = document.createElement('canvas');
            const hasWebGL = !!(window.WebGLRenderingContext && 
                (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
            
            this.log('WebGL: Supported', hasWebGL);
            return hasWebGL;
        } catch (error) {
            this.log('WebGL: Supported', false, error.message);
            return false;
        }
    },
    
    // Test 12: Touch Events (Mobile)
    testTouchEvents() {
        const hasTouch = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        this.log('Touch: Supported', hasTouch, `Touch points: ${navigator.maxTouchPoints || 0}`);
        return true; // Not a failure if no touch on desktop
    },
    
    // Test 13: Demo Mode Flow
    async testDemoFlow() {
        // Simulate loading a demo user
        if (typeof DemoLoader !== 'undefined') {
            const loaded = DemoLoader.loadUserIntoDashboard('demo_user_001');
            this.log('Demo Flow: Load User', loaded);
            
            const isDemo = DemoLoader.isDemoMode();
            this.log('Demo Flow: Demo Mode Active', isDemo);
            
            const user = DemoLoader.getCurrentDemoUser();
            this.log('Demo Flow: User Retrieved', user !== null, user?.name);
            
            return loaded && isDemo && user !== null;
        }
        
        this.log('Demo Flow: Skipped', true, 'DemoLoader not available');
        return true;
    },
    
    // Test 14: Animation CSS Loaded
    testAnimationCSS() {
        const linkExists = Array.from(document.querySelectorAll('link'))
            .some(link => link.href.includes('animations.css'));
        this.log('CSS: Animations loaded', linkExists);
        return linkExists;
    },
    
    // Test 15: Firebase Config Present
    testFirebaseConfig() {
        const scripts = Array.from(document.querySelectorAll('script'));
        const hasFirebase = scripts.some(s => s.src.includes('firebase')) || 
                            typeof firebase !== 'undefined';
        this.log('Firebase: Config present', hasFirebase);
        return hasFirebase;
    },
    
    // Run all tests
    async runAll() {
        console.log('%c🧪 PhysiqAI QA Test Suite', 'font-size: 20px; font-weight: bold; color: #6366f1');
        console.log('%cRunning tests...', 'color: #a1a1aa');
        console.log('');
        
        this.results = [];
        
        await this.testPageLoads();
        await this.testDemoData();
        this.testDemoLoader();
        this.testToastSystem();
        this.testErrorHandler();
        this.testLocalStorage();
        this.testSessionStorage();
        this.testCSSVariables();
        this.testResponsive();
        this.testThreeJS();
        this.testWebGL();
        this.testTouchEvents();
        await this.testDemoFlow();
        this.testAnimationCSS();
        this.testFirebaseConfig();
        
        this.printSummary();
        
        return this.results;
    },
    
    printSummary() {
        console.log('');
        console.log('%c📊 Test Summary', 'font-size: 16px; font-weight: bold;');
        
        const passed = this.results.filter(r => r.passed).length;
        const failed = this.results.filter(r => !r.passed).length;
        const total = this.results.length;
        
        console.log(`%cTotal: ${total} | Passed: ${passed} | Failed: ${failed}`, 
            failed === 0 ? 'color: #10b981' : 'color: #f59e0b');
        
        if (failed > 0) {
            console.log('%cFailed Tests:', 'color: #ef4444');
            this.results.filter(r => !r.passed).forEach(r => {
                console.log(`  ✗ ${r.test}: ${r.message}`);
            });
        }
        
        console.log('');
        console.log('%c✅ QA Test Complete', 'font-size: 14px; color: #10b981');
        
        // Return results for further processing
        return {
            total,
            passed,
            failed,
            results: this.results,
            success: failed === 0
        };
    },
    
    // Generate report
    generateReport() {
        const summary = this.printSummary();
        
        const report = {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            viewport: { width: window.innerWidth, height: window.innerHeight },
            ...summary
        };
        
        // Download report
        const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `physiqai-qa-report-${Date.now()}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        return report;
    }
};

// Auto-run on load if ?qa=true is in URL
if (window.location.search.includes('qa=true')) {
    window.addEventListener('load', () => {
        setTimeout(() => {
            QATests.runAll().then(() => {
                // Generate report after tests
                setTimeout(() => QATests.generateReport(), 1000);
            });
        }, 2000);
    });
}

// Expose globally
window.QATests = QATests;

console.log('%c🧪 QA Test Suite Ready', 'color: #6366f1');
console.log('Run: QATests.runAll()');
console.log('Or add ?qa=true to URL to auto-run');
