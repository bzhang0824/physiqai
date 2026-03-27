/**
 * PhysiqAI Mobile Meta Tag Injector
 * Ensures all pages have proper mobile viewport and PWA meta tags
 */

(function() {
  'use strict';

  // Meta tags configuration
  const META_TAGS = [
    // Viewport - Critical for mobile
    { name: 'viewport', content: 'width=device-width, initial-scale=1.0, viewport-fit=cover, maximum-scale=5.0, user-scalable=yes' },
    
    // Theme colors
    { name: 'theme-color', content: '#3B82F6' },
    { name: 'msapplication-TileColor', content: '#3B82F6' },
    
    // iOS Web App
    { name: 'apple-mobile-web-app-capable', content: 'yes' },
    { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' },
    { name: 'apple-mobile-web-app-title', content: 'PhysiqAI' },
    
    // iOS Icons (default paths)
    { rel: 'apple-touch-icon', sizes: '180x180', href: '/assets/icon-180x180.png' },
    { rel: 'apple-touch-icon', sizes: '152x152', href: '/assets/icon-152x152.png' },
    { rel: 'apple-touch-icon', sizes: '120x120', href: '/assets/icon-120x120.png' },
    
    // PWA Manifest
    { rel: 'manifest', href: '/manifest.json' },
    
    // Preconnect to external resources
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: true }
  ];

  function injectMetaTags() {
    const head = document.head;
    
    META_TAGS.forEach(tag => {
      // Check if tag already exists
      let exists = false;
      
      if (tag.name) {
        exists = head.querySelector(`meta[name="${tag.name}"]`) !== null;
      } else if (tag.rel && tag.href) {
        exists = head.querySelector(`link[rel="${tag.rel}"][href="${tag.href}"]`) !== null;
      }
      
      if (!exists) {
        const element = document.createElement(tag.rel ? 'link' : 'meta');
        
        Object.keys(tag).forEach(key => {
          if (key === 'crossorigin') {
            element.setAttribute('crossorigin', tag[key]);
          } else {
            element.setAttribute(key, tag[key]);
          }
        });
        
        head.appendChild(element);
      }
    });
  }

  // iOS-specific fixes
  function applyIOSFixes() {
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    
    if (isIOS) {
      // Fix for iOS 100vh issue
      const style = document.createElement('style');
      style.textContent = `
        :root {
          --vh: 1vh;
        }
        
        .full-height {
          height: 100vh; /* Fallback */
          height: calc(var(--vh, 1vh) * 100);
        }
        
        /* iOS momentum scrolling */
        * {
          -webkit-overflow-scrolling: touch;
        }
        
        /* Prevent callout on long press */
        * {
          -webkit-touch-callout: none;
        }
        
        /* Prevent text size adjustment */
        html {
          -webkit-text-size-adjust: 100%;
        }
      `;
      document.head.appendChild(style);
      
      // Update --vh variable on resize
      function updateVH() {
        const vh = window.innerHeight * 0.01;
        document.documentElement.style.setProperty('--vh', `${vh}px`);
      }
      
      updateVH();
      window.addEventListener('resize', updateVH);
      window.addEventListener('orientationchange', () => {
        setTimeout(updateVH, 100);
      });
    }
  }

  // Android-specific fixes
  function applyAndroidFixes() {
    const isAndroid = /Android/.test(navigator.userAgent);
    
    if (isAndroid) {
      const style = document.createElement('style');
      style.textContent = `
        /* Android overscroll effect */
        body {
          overscroll-behavior-y: contain;
        }
        
        /* Android tap highlight */
        * {
          -webkit-tap-highlight-color: rgba(59, 130, 246, 0.1);
        }
      `;
      document.head.appendChild(style);
    }
  }

  // Standalone PWA detection
  function detectStandalone() {
    const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
                        window.navigator.standalone ||
                        document.referrer.includes('android-app://');
    
    if (isStandalone) {
      document.body.classList.add('pwa-standalone');
      
      const style = document.createElement('style');
      style.textContent = `
        .pwa-standalone .navbar {
          padding-top: env(safe-area-inset-top);
        }
        
        .pwa-standalone .bottom-nav {
          padding-bottom: env(safe-area-inset-bottom);
        }
      `;
      document.head.appendChild(style);
    }
  }

  // Initialize
  function init() {
    injectMetaTags();
    applyIOSFixes();
    applyAndroidFixes();
    detectStandalone();
    
    console.log('[PhysiqAI Mobile] Meta tags injected');
  }

  // Run immediately
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
