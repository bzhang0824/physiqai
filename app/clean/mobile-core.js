/**
 * PhysiqAI Mobile Touch & Interaction Handler
 * Fixes touch delays, adds haptic feedback, handles pull-to-refresh
 */

(function() {
  'use strict';

  // ==========================================
  // CONFIGURATION
  // ==========================================
  const CONFIG = {
    touchDelay: false,      // Disable 300ms tap delay
    hapticEnabled: true,    // Enable haptic feedback
    pullToRefresh: true,    // Enable pull-to-refresh
    minTouchTarget: 44,     // Minimum touch target size in px
    scrollMomentum: true    // Smooth scrolling
  };

  // ==========================================
  // HAPTIC FEEDBACK
  // ==========================================
  const Haptic = {
    light() {
      if (navigator.vibrate) navigator.vibrate(10);
    },
    medium() {
      if (navigator.vibrate) navigator.vibrate(20);
    },
    heavy() {
      if (navigator.vibrate) navigator.vibrate([30, 50, 30]);
    },
    success() {
      if (navigator.vibrate) navigator.vibrate([10, 30, 10]);
    },
    error() {
      if (navigator.vibrate) navigator.vibrate([50, 30, 50]);
    }
  };

  // ==========================================
  // TOUCH DELAY FIX
  // ==========================================
  function removeTouchDelay() {
    // Add touch-action CSS to all interactive elements
    const style = document.createElement('style');
    style.textContent = `
      * {
        touch-action: manipulation;
        -webkit-tap-highlight-color: transparent;
      }
      button, a, input, select, textarea, [role="button"] {
        touch-action: manipulation;
      }
    `;
    document.head.appendChild(style);

    // FastClick-style touch handling for old browsers
    let touchStartTime = 0;
    let touchStartX = 0;
    let touchStartY = 0;

    document.addEventListener('touchstart', (e) => {
      touchStartTime = Date.now();
      touchStartX = e.touches[0].clientX;
      touchStartY = e.touches[0].clientY;
    }, { passive: true });

    document.addEventListener('touchend', (e) => {
      const touchDuration = Date.now() - touchStartTime;
      const touchEndX = e.changedTouches[0].clientX;
      const touchEndY = e.changedTouches[0].clientY;
      const moveDistance = Math.sqrt(
        Math.pow(touchEndX - touchStartX, 2) + 
        Math.pow(touchEndY - touchStartY, 2)
      );

      // If quick tap with minimal movement, treat as click
      if (touchDuration < 200 && moveDistance < 10) {
        const target = e.target.closest('a, button, [role="button"], input, select, textarea, label');
        if (target && !target.disabled) {
          // Trigger haptic feedback
          if (CONFIG.hapticEnabled) {
            Haptic.light();
          }
        }
      }
    }, { passive: true });
  }

  // ==========================================
  // TOUCH TARGET SIZE VALIDATOR
  // ==========================================
  function validateTouchTargets() {
    const interactiveElements = document.querySelectorAll(
      'button, a, input, select, textarea, [role="button"], .btn, .nav-item, .toggle, .tab'
    );

    interactiveElements.forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.height > 0) {
        if (rect.width < CONFIG.minTouchTarget || rect.height < CONFIG.minTouchTarget) {
          // Add padding to make it 44px minimum
          const needsWidth = Math.max(0, CONFIG.minTouchTarget - rect.width);
          const needsHeight = Math.max(0, CONFIG.minTouchTarget - rect.height);
          
          el.style.minWidth = `${CONFIG.minTouchTarget}px`;
          el.style.minHeight = `${CONFIG.minTouchTarget}px`;
          el.dataset.touchFixed = 'true';
        }
      }
    });
  }

  // ==========================================
  // PULL TO REFRESH
  // ==========================================
  function initPullToRefresh() {
    if (!CONFIG.pullToRefresh) return;

    let startY = 0;
    let currentY = 0;
    let isPulling = false;
    let refreshIndicator = null;
    const PULL_THRESHOLD = 100;

    // Create refresh indicator
    function createIndicator() {
      const indicator = document.createElement('div');
      indicator.className = 'pull-to-refresh';
      indicator.innerHTML = `
        <div class="pull-spinner">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M23 4v6h-6M1 20v-6h6M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/>
          </svg>
        </div>
        <span class="pull-text">Pull to refresh</span>
      `;
      document.body.appendChild(indicator);
      return indicator;
    }

    // Check if we're at the top of the page
    function isAtTop() {
      return window.scrollY <= 0;
    }

    document.addEventListener('touchstart', (e) => {
      if (!isAtTop()) return;
      startY = e.touches[0].clientY;
      isPulling = true;
    }, { passive: true });

    document.addEventListener('touchmove', (e) => {
      if (!isPulling || !isAtTop()) return;

      currentY = e.touches[0].clientY;
      const pullDistance = currentY - startY;

      if (pullDistance > 0 && pullDistance < 300) {
        if (!refreshIndicator) {
          refreshIndicator = createIndicator();
        }
        refreshIndicator.style.transform = `translateY(${pullDistance * 0.5}px)`;
        refreshIndicator.classList.toggle('ready', pullDistance > PULL_THRESHOLD);
        
        const text = refreshIndicator.querySelector('.pull-text');
        if (text) {
          text.textContent = pullDistance > PULL_THRESHOLD ? 'Release to refresh' : 'Pull to refresh';
        }
      }
    }, { passive: true });

    document.addEventListener('touchend', () => {
      if (!isPulling) return;
      isPulling = false;

      const pullDistance = currentY - startY;
      
      if (pullDistance > PULL_THRESHOLD && isAtTop()) {
        // Trigger refresh
        if (refreshIndicator) {
          refreshIndicator.classList.add('refreshing');
          refreshIndicator.querySelector('.pull-text').textContent = 'Refreshing...';
        }
        
        Haptic.medium();
        
        // Reload page after brief delay
        setTimeout(() => {
          window.location.reload();
        }, 500);
      } else {
        // Reset
        if (refreshIndicator) {
          refreshIndicator.style.transform = 'translateY(-100%)';
          setTimeout(() => {
            refreshIndicator?.remove();
            refreshIndicator = null;
          }, 300);
        }
      }

      startY = 0;
      currentY = 0;
    }, { passive: true });
  }

  // ==========================================
  // BUTTON HAPTIC FEEDBACK
  // ==========================================
  function initButtonHaptics() {
    const buttons = document.querySelectorAll('button, .btn, [role="button"], a.btn, .nav-item');
    
    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        if (CONFIG.hapticEnabled) {
          Haptic.light();
        }
      });
    });

    // Success/error buttons get special haptics
    document.querySelectorAll('.btn-success, [data-haptic="success"]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (CONFIG.hapticEnabled) Haptic.success();
      });
    });

    document.querySelectorAll('.btn-danger, [data-haptic="error"]').forEach(btn => {
      btn.addEventListener('click', () => {
        if (CONFIG.hapticEnabled) Haptic.error();
      });
    });
  }

  // ==========================================
  // FORM INPUT ZOOM FIX
  // ==========================================
  function fixInputZoom() {
    // Prevent zoom on iOS when focusing inputs
    const style = document.createElement('style');
    style.textContent = `
      @media screen and (max-width: 768px) {
        input, select, textarea {
          font-size: 16px !important; /* Prevents iOS zoom */
        }
        input:focus, select:focus, textarea:focus {
          font-size: 16px !important;
        }
      }
    `;
    document.head.appendChild(style);

    // Add focus management for viewport
    const inputs = document.querySelectorAll('input, select, textarea');
    inputs.forEach(input => {
      input.addEventListener('focus', () => {
        // Ensure element is visible above keyboard
        setTimeout(() => {
          input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
      });
    });
  }

  // ==========================================
  // SMOOTH SCROLLING
  // ==========================================
  function initSmoothScrolling() {
    // Enable momentum scrolling on iOS
    const style = document.createElement('style');
    style.textContent = `
      * {
        -webkit-overflow-scrolling: touch;
      }
      html {
        scroll-behavior: smooth;
      }
      body {
        overscroll-behavior-y: contain;
      }
      @media (prefers-reduced-motion: reduce) {
        html {
          scroll-behavior: auto;
        }
      }
    `;
    document.head.appendChild(style);
  }

  // ==========================================
  // SAFE AREA INSETS (Notch Support)
  // ==========================================
  function initSafeAreaSupport() {
    const style = document.createElement('style');
    style.textContent = `
      /* Safe area insets for notched phones */
      .navbar, .bottom-nav, .header {
        padding-top: env(safe-area-inset-top);
        padding-left: env(safe-area-inset-left);
        padding-right: env(safe-area-inset-right);
      }
      
      .bottom-nav {
        padding-bottom: env(safe-area-inset-bottom);
      }
      
      .main-content, .auth-container {
        padding-left: max(16px, env(safe-area-inset-left));
        padding-right: max(16px, env(safe-area-inset-right));
        padding-bottom: max(80px, env(safe-area-inset-bottom) + 80px);
      }
      
      /* iOS standalone mode adjustments */
      @supports (-webkit-touch-callout: none) {
        .navbar, .header {
          padding-top: max(12px, env(safe-area-inset-top));
        }
      }
    `;
    document.head.appendChild(style);
  }

  // ==========================================
  // LOADING STATES
  // ==========================================
  function initLoadingStates() {
    // Add loading state management
    window.showLoading = function(element, text = 'Loading...') {
      if (typeof element === 'string') {
        element = document.querySelector(element);
      }
      if (!element) return;

      element.dataset.originalContent = element.innerHTML;
      element.disabled = true;
      element.innerHTML = `
        <span class="btn-spinner"></span>
        <span>${text}</span>
      `;
      element.classList.add('loading');
    };

    window.hideLoading = function(element) {
      if (typeof element === 'string') {
        element = document.querySelector(element);
      }
      if (!element) return;

      element.innerHTML = element.dataset.originalContent || '';
      element.disabled = false;
      element.classList.remove('loading');
    };

    // Add loading spinner styles
    const style = document.createElement('style');
    style.textContent = `
      .btn-spinner {
        display: inline-block;
        width: 16px;
        height: 16px;
        border: 2px solid currentColor;
        border-top-color: transparent;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
        margin-right: 8px;
      }
      @keyframes spin {
        to { transform: rotate(360deg); }
      }
      button.loading, .btn.loading {
        opacity: 0.7;
        cursor: not-allowed;
      }
    `;
    document.head.appendChild(style);
  }

  // ==========================================
  // HORIZONTAL SCROLL PREVENTION
  // ==========================================
  function preventHorizontalScroll() {
    const style = document.createElement('style');
    style.textContent = `
      html, body {
        overflow-x: hidden;
        max-width: 100vw;
      }
      * {
        max-width: 100%;
      }
      img, video, iframe {
        max-width: 100%;
        height: auto;
      }
    `;
    document.head.appendChild(style);

    // Prevent bounce scroll on iOS
    document.addEventListener('touchmove', (e) => {
      if (e.target.closest('.scrollable')) return;
      // Allow normal scroll but prevent horizontal overscroll
    }, { passive: true });
  }

  // ==========================================
  // LAZY LOADING FOR IMAGES
  // ==========================================
  function initLazyLoading() {
    // Add native lazy loading to images
    document.querySelectorAll('img:not([loading])').forEach(img => {
      img.loading = 'lazy';
      img.decoding = 'async';
    });

    // IntersectionObserver for custom lazy loading
    if ('IntersectionObserver' in window) {
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const img = entry.target;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
            }
            imageObserver.unobserve(img);
          }
        });
      }, { rootMargin: '50px' });

      document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
      });
    }
  }

  // ==========================================
  // BACK BUTTON HANDLING
  // ==========================================
  function initBackButton() {
    // Handle Android back button
    window.addEventListener('popstate', (e) => {
      // Close any open modals first
      const openModal = document.querySelector('.modal-overlay.active, .modal.active');
      if (openModal) {
        e.preventDefault();
        openModal.classList.remove('active');
        return;
      }

      // Close dropdowns
      const openDropdown = document.querySelector('.user-menu.active, .dropdown.active');
      if (openDropdown) {
        e.preventDefault();
        openDropdown.classList.remove('active');
        return;
      }
    });
  }

  // ==========================================
  // SERVICE WORKER REGISTRATION
  // ==========================================
  function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js')
        .then(registration => {
          console.log('[Mobile] SW registered:', registration.scope);
        })
        .catch(error => {
          console.log('[Mobile] SW registration failed:', error);
        });
    }
  }

  // ==========================================
  // INITIALIZE EVERYTHING
  // ==========================================
  function init() {
    // Wait for DOM ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', runInit);
    } else {
      runInit();
    }
  }

  function runInit() {
    removeTouchDelay();
    initSmoothScrolling();
    initSafeAreaSupport();
    initPullToRefresh();
    initButtonHaptics();
    fixInputZoom();
    initLoadingStates();
    preventHorizontalScroll();
    initLazyLoading();
    initBackButton();
    registerServiceWorker();

    // Validate touch targets after a short delay (for dynamically added content)
    setTimeout(validateTouchTargets, 100);
    
    // Re-validate on resize and new content
    let resizeTimeout;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(validateTouchTargets, 250);
    });

    // MutationObserver for dynamically added content
    const observer = new MutationObserver((mutations) => {
      let shouldValidate = false;
      mutations.forEach(mutation => {
        if (mutation.addedNodes.length > 0) {
          shouldValidate = true;
        }
      });
      if (shouldValidate) {
        setTimeout(validateTouchTargets, 50);
      }
    });

    observer.observe(document.body, { childList: true, subtree: true });

    console.log('[PhysiqAI Mobile] Initialized');
  }

  // Expose API globally
  window.PhysiqMobile = {
    Haptic,
    showLoading: window.showLoading,
    hideLoading: window.hideLoading,
    validateTouchTargets
  };

  // Start
  init();
})();
