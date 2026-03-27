/**
 * PhysiqAI Mobile Avatar Viewer
 * Optimized 3D avatar display with touch controls
 */

(function() {
    'use strict';

    // ========================================
    // MOBILE AVATAR CONFIGURATION
    // ========================================
    const CONFIG = {
        // Performance settings
        mobileMaxVertices: 2000,
        desktopMaxVertices: 5000,
        frameSkip: 2, // Render every Nth frame on mobile
        
        // Touch settings
        rotationSensitivity: 0.5,
        pinchSensitivity: 0.01,
        minScale: 0.5,
        maxScale: 3,
        
        // Animation
        floatAmplitude: 8,
        floatSpeed: 0.002
    };

    // ========================================
    // AVATAR CONTROLLER
    // ========================================
    class MobileAvatarController {
        constructor(container) {
            this.container = container;
            this.avatar = container.querySelector('.avatar-figure');
            this.isMobile = window.matchMedia('(max-width: 768px)').matches;
            
            // State
            this.rotation = 0;
            this.scale = 1;
            this.targetRotation = 0;
            this.targetScale = 1;
            
            // Touch state
            this.touches = new Map();
            this.lastPinchDistance = 0;
            this.isDragging = false;
            
            this.init();
        }

        init() {
            this.setupEventListeners();
            this.optimizeForMobile();
            this.startAnimationLoop();
            
            // Apply initial rotation
            if (this.avatar) {
                this.avatar.style.transform = 'rotateY(0deg)';
            }
        }

        setupEventListeners() {
            // Touch events
            this.container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
            this.container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
            this.container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
            
            // Double tap to reset
            this.container.addEventListener('touchend', this.handleDoubleTap.bind(this), { passive: true });
            
            // Orientation change
            window.addEventListener('orientationchange', () => {
                setTimeout(() => this.handleOrientationChange(), 100);
            });
            
            // Visibility change (pause animations)
            document.addEventListener('visibilitychange', () => {
                this.isVisible = !document.hidden;
            });
        }

        handleTouchStart(e) {
            // Store all touches
            for (let touch of e.changedTouches) {
                this.touches.set(touch.identifier, {
                    startX: touch.clientX,
                    startY: touch.clientY,
                    startTime: Date.now()
                });
            }
            
            // Pinch zoom start
            if (e.touches.length === 2) {
                this.lastPinchDistance = this.getPinchDistance(e.touches);
                this.container.style.touchAction = 'none';
            }
        }

        handleTouchMove(e) {
            if (e.touches.length === 1 && this.touches.size === 1) {
                // Single touch - rotation
                const touch = e.touches[0];
                const stored = this.touches.get(touch.identifier);
                
                if (stored) {
                    const deltaX = touch.clientX - stored.startX;
                    
                    // Only rotate if horizontal movement dominates
                    if (Math.abs(deltaX) > 10) {
                        this.isDragging = true;
                        this.targetRotation += deltaX * CONFIG.rotationSensitivity;
                        
                        // Update start for continuous rotation
                        stored.startX = touch.clientX;
                    }
                }
            } else if (e.touches.length === 2) {
                // Pinch zoom
                e.preventDefault();
                
                const distance = this.getPinchDistance(e.touches);
                const delta = distance - this.lastPinchDistance;
                
                this.targetScale = Math.min(
                    Math.max(this.targetScale + delta * CONFIG.pinchSensitivity, CONFIG.minScale),
                    CONFIG.maxScale
                );
                
                this.lastPinchDistance = distance;
                
                // Trigger haptic feedback on scale change
                if (Math.abs(delta) > 5 && window.PhysiqTouch) {
                    window.PhysiqTouch.Haptics.light();
                }
            }
        }

        handleTouchEnd(e) {
            // Remove ended touches
            for (let touch of e.changedTouches) {
                this.touches.delete(touch.identifier);
            }
            
            // Reset state
            if (e.touches.length === 0) {
                this.isDragging = false;
                this.container.style.touchAction = 'pan-y pinch-zoom';
            } else if (e.touches.length === 1) {
                // Reset pinch distance for next pinch
                this.lastPinchDistance = 0;
            }
        }

        handleDoubleTap(e) {
            const now = Date.now();
            const lastTap = this.lastTapTime || 0;
            
            if (now - lastTap < 300) {
                // Double tap - reset view
                this.targetRotation = 0;
                this.targetScale = 1;
                
                if (window.PhysiqTouch) {
                    window.PhysiqTouch.Haptics.medium();
                }
                
                // Update rotation buttons
                this.updateRotationButtons(0);
            }
            
            this.lastTapTime = now;
        }

        getPinchDistance(touches) {
            const dx = touches[0].clientX - touches[1].clientX;
            const dy = touches[0].clientY - touches[1].clientY;
            return Math.sqrt(dx * dx + dy * dy);
        }

        startAnimationLoop() {
            let frameCount = 0;
            
            const animate = () => {
                if (!this.isVisible) {
                    requestAnimationFrame(animate);
                    return;
                }
                
                // Frame skipping for performance on mobile
                frameCount++;
                if (this.isMobile && frameCount % CONFIG.frameSkip !== 0) {
                    requestAnimationFrame(animate);
                    return;
                }
                
                // Smooth interpolation
                this.rotation += (this.targetRotation - this.rotation) * 0.1;
                this.scale += (this.targetScale - this.scale) * 0.1;
                
                // Apply transforms
                if (this.avatar) {
                    this.avatar.style.transform = `
                        rotateY(${this.rotation}deg)
                        scale(${this.scale})
                    `;
                }
                
                requestAnimationFrame(animate);
            };
            
            this.isVisible = true;
            requestAnimationFrame(animate);
        }

        optimizeForMobile() {
            if (!this.isMobile) return;
            
            // Reduce avatar complexity
            const avatarParts = this.avatar?.querySelectorAll('.avatar-head, .avatar-torso, .avatar-legs');
            if (avatarParts) {
                avatarParts.forEach(part => {
                    part.style.willChange = 'transform';
                });
            }
            
            // Disable expensive effects on low-end devices
            if (this.isLowEndDevice()) {
                this.container.classList.add('low-performance');
                
                // Reduce glow effects
                const glow = this.container.querySelector('.avatar-glow');
                if (glow) {
                    glow.style.animation = 'none';
                    glow.style.opacity = '0.3';
                }
            }
        }

        isLowEndDevice() {
            // Check for low-end device indicators
            const memory = navigator.deviceMemory;
            const cores = navigator.hardwareConcurrency;
            
            return (memory && memory <= 4) || (cores && cores <= 4);
        }

        handleOrientationChange() {
            // Reset transformations on orientation change
            setTimeout(() => {
                this.container.style.height = window.innerHeight * 0.5 + 'px';
            }, 300);
        }

        setRotation(degrees) {
            this.targetRotation = degrees;
            this.updateRotationButtons(degrees);
        }

        updateRotationButtons(activeDegrees) {
            const buttons = document.querySelectorAll('.slider-thumb');
            const rotations = [0, 45, 90, 135, 180];
            
            buttons.forEach((btn, index) => {
                btn.classList.toggle('active', rotations[index] === activeDegrees);
            });
        }

        // Public API
        zoomIn() {
            this.targetScale = Math.min(this.targetScale + 0.5, CONFIG.maxScale);
        }

        zoomOut() {
            this.targetScale = Math.max(this.targetScale - 0.5, CONFIG.minScale);
        }

        reset() {
            this.targetRotation = 0;
            this.targetScale = 1;
            this.updateRotationButtons(0);
        }
    }

    // ========================================
    // OFFLINE QUEUE MANAGER
    // ========================================
    class OfflineQueue {
        constructor() {
            this.db = null;
            this.init();
        }

        async init() {
            this.db = await this.openDB();
        }

        openDB() {
            return new Promise((resolve, reject) => {
                const request = indexedDB.open('PhysiqAIOffline', 1);
                
                request.onerror = () => reject(request.error);
                request.onsuccess = () => resolve(request.result);
                
                request.onupgradeneeded = (event) => {
                    const db = event.target.result;
                    
                    if (!db.objectStoreNames.contains('actions')) {
                        const store = db.createObjectStore('actions', { 
                            keyPath: 'id', 
                            autoIncrement: true 
                        });
                        store.createIndex('type', 'type', { unique: false });
                        store.createIndex('timestamp', 'timestamp', { unique: false });
                    }
                };
            });
        }

        async queueAction(type, data) {
            if (!this.db) await this.init();
            
            const action = {
                type,
                data,
                timestamp: Date.now(),
                synced: false
            };
            
            return new Promise((resolve, reject) => {
                const transaction = this.db.transaction(['actions'], 'readwrite');
                const store = transaction.objectStore('actions');
                const request = store.add(action);
                
                request.onsuccess = () => resolve(request.result);
                request.onerror = () => reject(request.error);
            });
        }

        async sync() {
            if (!this.db) await this.init();
            if (!navigator.onLine) return;
            
            const transaction = this.db.transaction(['actions'], 'readonly');
            const store = transaction.objectStore('actions');
            const index = store.index('synced');
            const request = index.getAll(false);
            
            request.onsuccess = async () => {
                const actions = request.result;
                
                for (const action of actions) {
                    try {
                        await this.processAction(action);
                        await this.markAsSynced(action.id);
                    } catch (error) {
                        console.error('Failed to sync action:', error);
                    }
                }
            };
        }

        async processAction(action) {
            switch (action.type) {
                case 'weight':
                    // Sync weight to Firebase
                    if (window.firebaseAPI) {
                        await window.firebaseAPI.saveWeight(action.data);
                    }
                    break;
                    
                case 'scan':
                    // Queue scan for upload
                    if (window.firebaseAPI) {
                        await window.firebaseAPI.uploadScan(action.data);
                    }
                    break;
            }
        }

        async markAsSynced(id) {
            const transaction = this.db.transaction(['actions'], 'readwrite');
            const store = transaction.objectStore('actions');
            const request = store.get(id);
            
            request.onsuccess = () => {
                const action = request.result;
                action.synced = true;
                store.put(action);
            };
        }
    }

    // ========================================
    // PERFORMANCE MONITOR
    // ========================================
    class PerformanceMonitor {
        constructor() {
            this.metrics = {
                fps: 0,
                frameTime: 0,
                memory: null
            };
            this.init();
        }

        init() {
            if (!this.isMobile()) return;
            
            this.monitorFPS();
            this.monitorMemory();
        }

        isMobile() {
            return window.matchMedia('(max-width: 768px)').matches;
        }

        monitorFPS() {
            let lastTime = performance.now();
            let frames = 0;
            
            const measure = () => {
                const now = performance.now();
                frames++;
                
                if (now >= lastTime + 1000) {
                    this.metrics.fps = frames;
                    this.metrics.frameTime = 1000 / frames;
                    frames = 0;
                    lastTime = now;
                    
                    // Reduce quality if FPS drops
                    if (this.metrics.fps < 30) {
                        document.body.classList.add('reduce-animations');
                    }
                }
                
                requestAnimationFrame(measure);
            };
            
            requestAnimationFrame(measure);
        }

        monitorMemory() {
            if (performance.memory) {
                setInterval(() => {
                    this.metrics.memory = {
                        used: performance.memory.usedJSHeapSize,
                        total: performance.memory.totalJSHeapSize,
                        limit: performance.memory.jsHeapSizeLimit
                    };
                    
                    // Warn if memory is high
                    const usage = this.metrics.memory.used / this.metrics.memory.limit;
                    if (usage > 0.8) {
                        console.warn('High memory usage detected');
                        document.body.classList.add('low-memory');
                    }
                }, 5000);
            }
        }
    }

    // ========================================
    // INITIALIZE
    // ========================================
    document.addEventListener('DOMContentLoaded', () => {
        // Initialize avatar controller
        const avatarContainer = document.querySelector('.avatar-3d-container');
        if (avatarContainer) {
            window.avatarController = new MobileAvatarController(avatarContainer);
        }
        
        // Initialize offline queue
        window.offlineQueue = new OfflineQueue();
        
        // Initialize performance monitor
        window.perfMonitor = new PerformanceMonitor();
        
        // Listen for online/offline
        window.addEventListener('online', () => {
            console.log('Back online - syncing...');
            if (window.offlineQueue) {
                window.offlineQueue.sync();
            }
            
            // Show toast notification
            if (window.showToast) {
                window.showToast('Back online', 'success');
            }
        });
        
        window.addEventListener('offline', () => {
            console.log('Gone offline - actions will be queued');
            if (window.showToast) {
                window.showToast('You\'re offline. Actions will sync when back online.', 'info');
            }
        });
    });

    // Expose API globally
    window.MobileAvatar = {
        CONFIG,
        MobileAvatarController,
        OfflineQueue,
        PerformanceMonitor
    };
})();
