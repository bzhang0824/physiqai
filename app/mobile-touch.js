/**
 * PhysiqAI Touch Gestures & Mobile Interactions
 * Handles swipes, pinches, pulls, and haptic feedback
 */

(function() {
    'use strict';

    // ========================================
    // CONFIGURATION
    // ========================================
    const CONFIG = {
        swipeThreshold: 50,
        swipeVelocity: 0.5,
        pinchThreshold: 0.1,
        pullThreshold: 80,
        longPressDelay: 500,
        doubleTapDelay: 300
    };

    // ========================================
    // TOUCH STATE MANAGEMENT
    // ========================================
    const TouchState = {
        startX: 0,
        startY: 0,
        startTime: 0,
        lastX: 0,
        lastY: 0,
        isDragging: false,
        isPinching: false,
        initialPinchDistance: 0,
        currentScale: 1,
        lastTapTime: 0,
        longPressTimer: null
    };

    // ========================================
    // HAPTIC FEEDBACK
    // ========================================
    const Haptics = {
        supported: 'vibrate' in navigator,
        
        light() {
            if (this.supported) navigator.vibrate(10);
        },
        
        medium() {
            if (this.supported) navigator.vibrate(20);
        },
        
        heavy() {
            if (this.supported) navigator.vibrate(30);
        },
        
        success() {
            if (this.supported) navigator.vibrate([10, 50, 10]);
        },
        
        error() {
            if (this.supported) navigator.vibrate([30, 50, 30]);
        }
    };

    // ========================================
    // SWIPE NAVIGATION
    // ========================================
    class SwipeNavigator {
        constructor() {
            this.pages = [
                { id: 'home', url: 'app-home.html', index: 0 },
                { id: 'avatar', url: 'app-avatar.html', index: 1 },
                { id: 'stats', url: 'app-dashboard.html', index: 2 }
            ];
            this.currentPage = this.getCurrentPage();
            this.init();
        }

        getCurrentPage() {
            const path = window.location.pathname;
            const page = this.pages.find(p => path.includes(p.url));
            return page || this.pages[0];
        }

        init() {
            document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
            document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: true });
            document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
        }

        handleTouchStart(e) {
            if (e.touches.length !== 1) return;
            
            TouchState.startX = e.touches[0].clientX;
            TouchState.startY = e.touches[0].clientY;
            TouchState.startTime = Date.now();
            TouchState.isDragging = false;
        }

        handleTouchMove(e) {
            if (e.touches.length !== 1) return;
            
            const dx = e.touches[0].clientX - TouchState.startX;
            const dy = e.touches[0].clientY - TouchState.startY;
            
            // Only start drag if horizontal movement exceeds threshold
            if (Math.abs(dx) > 10 && Math.abs(dx) > Math.abs(dy)) {
                TouchState.isDragging = true;
            }
            
            TouchState.lastX = e.touches[0].clientX;
            TouchState.lastY = e.touches[0].clientY;
        }

        handleTouchEnd(e) {
            if (!TouchState.isDragging) return;
            
            const dx = TouchState.lastX - TouchState.startX;
            const dy = TouchState.lastY - TouchState.startY;
            const dt = Date.now() - TouchState.startTime;
            const velocity = Math.abs(dx) / dt;
            
            // Check if it's a valid swipe
            if (Math.abs(dx) > CONFIG.swipeThreshold || velocity > CONFIG.swipeVelocity) {
                // Only swipe if horizontal movement dominates
                if (Math.abs(dx) > Math.abs(dy) * 1.5) {
                    if (dx > 0) {
                        this.swipeRight();
                    } else {
                        this.swipeLeft();
                    }
                }
            }
            
            TouchState.isDragging = false;
        }

        swipeLeft() {
            const nextIndex = this.currentPage.index + 1;
            if (nextIndex < this.pages.length) {
                Haptics.light();
                this.navigate(this.pages[nextIndex].url, 'left');
            }
        }

        swipeRight() {
            const prevIndex = this.currentPage.index - 1;
            if (prevIndex >= 0) {
                Haptics.light();
                this.navigate(this.pages[prevIndex].url, 'right');
            }
        }

        navigate(url, direction) {
            // Add transition class
            document.body.classList.add(`slide-${direction}`);
            
            setTimeout(() => {
                window.location.href = url;
            }, 150);
        }
    }

    // ========================================
    // PINCH TO ZOOM (for avatar)
    // ========================================
    class PinchZoom {
        constructor(element) {
            this.element = element;
            this.scale = 1;
            this.initialDistance = 0;
            this.init();
        }

        init() {
            this.element.addEventListener('touchstart', this.handleStart.bind(this), { passive: true });
            this.element.addEventListener('touchmove', this.handleMove.bind(this), { passive: true });
            this.element.addEventListener('touchend', this.handleEnd.bind(this), { passive: true });
            
            // Reset on double tap
            this.element.addEventListener('touchend', this.handleDoubleTap.bind(this), { passive: true });
        }

        getDistance(touches) {
            const dx = touches[0].clientX - touches[1].clientX;
            const dy = touches[0].clientY - touches[1].clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }

        handleStart(e) {
            if (e.touches.length === 2) {
                TouchState.isPinching = true;
                this.initialDistance = this.getDistance(e.touches);
                this.element.style.transition = 'none';
            }
        }

        handleMove(e) {
            if (!TouchState.isPinching || e.touches.length !== 2) return;
            
            e.preventDefault();
            
            const distance = this.getDistance(e.touches);
            const scale = (distance / this.initialDistance) * this.scale;
            
            // Clamp scale between 0.5 and 3
            const clampedScale = Math.min(Math.max(scale, 0.5), 3);
            
            this.element.style.transform = `scale(${clampedScale})`;
        }

        handleEnd(e) {
            if (e.touches.length < 2) {
                TouchState.isPinching = false;
                this.element.style.transition = 'transform 0.3s ease';
                
                // Reset if scale is too small
                const currentScale = parseFloat(this.element.style.transform.replace('scale(', '').replace(')', '')) || 1;
                if (currentScale < 0.8) {
                    this.element.style.transform = 'scale(1)';
                    this.scale = 1;
                } else {
                    this.scale = currentScale;
                }
            }
        }

        handleDoubleTap(e) {
            const now = Date.now();
            if (now - TouchState.lastTapTime < CONFIG.doubleTapDelay) {
                // Double tap detected - reset zoom
                Haptics.medium();
                this.scale = 1;
                this.element.style.transform = 'scale(1)';
                this.element.style.transition = 'transform 0.3s ease';
            }
            TouchState.lastTapTime = now;
        }
    }

    // ========================================
    // PULL TO REFRESH
    // ========================================
    class PullToRefresh {
        constructor(callback) {
            this.callback = callback;
            this.indicator = null;
            this.isPulling = false;
            this.startY = 0;
            this.currentY = 0;
            this.init();
        }

        init() {
            this.createIndicator();
            
            document.addEventListener('touchstart', this.handleStart.bind(this), { passive: true });
            document.addEventListener('touchmove', this.handleMove.bind(this), { passive: true });
            document.addEventListener('touchend', this.handleEnd.bind(this), { passive: true });
        }

        createIndicator() {
            this.indicator = document.createElement('div');
            this.indicator.className = 'pull-to-refresh';
            this.indicator.innerHTML = '<div class="pull-to-refresh-spinner"></div>';
            document.body.appendChild(this.indicator);
        }

        handleStart(e) {
            // Only trigger at top of page
            if (window.scrollY > 0) return;
            
            this.startY = e.touches[0].clientY;
            this.isPulling = true;
        }

        handleMove(e) {
            if (!this.isPulling) return;
            
            this.currentY = e.touches[0].clientY;
            const delta = this.currentY - this.startY;
            
            if (delta > 0 && delta < 150) {
                this.indicator.style.transform = `translateY(${Math.min(delta - 60, 0)}px)`;
                
                if (delta > CONFIG.pullThreshold) {
                    this.indicator.classList.add('ready');
                } else {
                    this.indicator.classList.remove('ready');
                }
            }
        }

        handleEnd(e) {
            if (!this.isPulling) return;
            
            this.isPulling = false;
            const delta = this.currentY - this.startY;
            
            if (delta > CONFIG.pullThreshold) {
                Haptics.medium();
                this.indicator.classList.add('visible');
                
                if (this.callback) {
                    this.callback().then(() => {
                        this.indicator.classList.remove('visible');
                        this.indicator.style.transform = 'translateY(-100%)';
                    });
                }
            } else {
                this.indicator.style.transform = 'translateY(-100%)';
            }
        }
    }

    // ========================================
    // RIPPLE EFFECT
    // ========================================
    class RippleEffect {
        constructor() {
            this.init();
        }

        init() {
            const elements = document.querySelectorAll('.btn, .nav-item, .card-elevated, .pose-card');
            
            elements.forEach(el => {
                el.addEventListener('touchstart', this.createRipple.bind(this), { passive: true });
            });
        }

        createRipple(e) {
            const element = e.currentTarget;
            const rect = element.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = e.touches[0].clientX - rect.left - size / 2;
            const y = e.touches[0].clientY - rect.top - size / 2;
            
            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 50%;
                transform: scale(0);
                animation: ripple-animation 0.4s ease-out;
                pointer-events: none;
            `;
            
            element.style.position = 'relative';
            element.style.overflow = 'hidden';
            element.appendChild(ripple);
            
            setTimeout(() => ripple.remove(), 400);
        }
    }

    // ========================================
    // NETWORK STATUS
    // ========================================
    class NetworkStatus {
        constructor() {
            this.indicator = null;
            this.init();
        }

        init() {
            this.createIndicator();
            
            window.addEventListener('online', () => this.showStatus(true));
            window.addEventListener('offline', () => this.showStatus(false));
        }

        createIndicator() {
            this.indicator = document.createElement('div');
            this.indicator.className = 'network-status';
            document.body.appendChild(this.indicator);
        }

        showStatus(online) {
            this.indicator.classList.add('visible');
            this.indicator.classList.toggle('online', online);
            this.indicator.textContent = online ? 'Back online' : 'No internet connection';
            
            Haptics.light();
            
            setTimeout(() => {
                this.indicator.classList.remove('visible');
            }, 3000);
        }
    }

    // ========================================
    // WEBGL CONTEXT HANDLER
    // ========================================
    class WebGLHandler {
        constructor() {
            this.canvas = document.querySelector('#three-canvas, canvas');
            if (this.canvas) {
                this.init();
            }
        }

        init() {
            // Handle context lost
            this.canvas.addEventListener('webglcontextlost', this.handleContextLost.bind(this));
            this.canvas.addEventListener('webglcontextrestored', this.handleContextRestored.bind(this));
            
            // Create overlay
            this.createOverlay();
        }

        createOverlay() {
            const container = this.canvas.parentElement;
            if (!container) return;
            
            this.overlay = document.createElement('div');
            this.overlay.className = 'webgl-context-lost';
            this.overlay.innerHTML = `
                <div style="text-align: center; padding: 20px;">
                    <div style="font-size: 48px; margin-bottom: 12px;">🔄</div>
                    <div style="font-weight: 600; margin-bottom: 8px;">Reloading 3D View</div>
                    <div style="color: var(--text-muted); font-size: 14px;">Please wait...</div>
                </div>
            `;
            container.appendChild(this.overlay);
        }

        handleContextLost(e) {
            e.preventDefault();
            this.overlay.classList.add('visible');
        }

        handleContextRestored() {
            this.overlay.classList.remove('visible');
            Haptics.success();
        }
    }

    // ========================================
    // INITIALIZE
    // ========================================
    document.addEventListener('DOMContentLoaded', () => {
        // Initialize swipe navigation
        new SwipeNavigator();
        
        // Initialize pinch zoom on avatar
        const avatarContainer = document.querySelector('.avatar-3d-container, .avatar-container');
        if (avatarContainer) {
            new PinchZoom(avatarContainer);
        }
        
        // Initialize pull to refresh
        new PullToRefresh(() => {
            return new Promise(resolve => {
                setTimeout(() => {
                    window.location.reload();
                    resolve();
                }, 1000);
            });
        });
        
        // Initialize ripple effects
        new RippleEffect();
        
        // Initialize network status
        new NetworkStatus();
        
        // Initialize WebGL handler
        new WebGLHandler();
        
        // Add ripple animation CSS
        const style = document.createElement('style');
        style.textContent = `
            @keyframes ripple-animation {
                to {
                    transform: scale(2);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    });

    // Expose to global scope
    window.PhysiqTouch = {
        Haptics,
        CONFIG,
        PinchZoom,
        SwipeNavigator
    };
})();
