/**
 * ========================================
 * PhysiqAI - Comprehensive Error Handler
 * ========================================
 * 
 * Features:
 * - Global error catching (window.onerror, unhandledrejection)
 * - Safe localStorage operations with fallbacks
 * - Upload validation (file type, size)
 * - Network/offline detection and handling
 * - User-friendly error messages
 * - Graceful fallbacks for 3D viewer, API calls, etc.
 * - Error boundary component for React-like error isolation
 */

// ========================================
// ERROR HANDLER CONFIGURATION
// ========================================
const ErrorConfig = {
    maxFileSize: 10 * 1024 * 1024, // 10MB
    allowedImageTypes: ['image/jpeg', 'image/png', 'image/webp', 'image/jpg'],
    maxRetries: 3,
    retryDelay: 1000,
    errorDisplayDuration: 5000,
    debug: false
};

// ========================================
// ERROR TYPES
// ========================================
const ErrorTypes = {
    NETWORK: 'NETWORK_ERROR',
    STORAGE: 'STORAGE_ERROR',
    UPLOAD: 'UPLOAD_ERROR',
    RENDER: 'RENDER_ERROR',
    API: 'API_ERROR',
    VALIDATION: 'VALIDATION_ERROR',
    UNKNOWN: 'UNKNOWN_ERROR'
};

// ========================================
// ERROR BOUNDARY COMPONENT
// ========================================
class ErrorBoundary {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.fallbackHTML = options.fallbackHTML || this.getDefaultFallback();
        this.onError = options.onError || this.defaultErrorHandler;
        this.recoverable = options.recoverable !== false;
        this.componentName = options.componentName || 'Component';
    }

    getDefaultFallback() {
        return `
            <div class="error-boundary-fallback">
                <div class="error-icon">⚠️</div>
                <h3>Something went wrong</h3>
                <p>We're having trouble loading this component.</p>
                <button class="btn btn-primary" onclick="location.reload()">Reload Page</button>
            </div>
        `;
    }

    defaultErrorHandler(error, errorInfo) {
        ErrorHandler.logError(error, {
            type: ErrorTypes.RENDER,
            component: this.componentName,
            info: errorInfo
        });
    }

    wrap(fn) {
        return (...args) => {
            try {
                return fn.apply(this, args);
            } catch (error) {
                this.handleError(error);
                return null;
            }
        };
    }

    wrapAsync(fn) {
        return async (...args) => {
            try {
                return await fn.apply(this, args);
            } catch (error) {
                this.handleError(error);
                return null;
            }
        };
    }

    handleError(error, errorInfo = {}) {
        this.onError(error, errorInfo);
        if (this.container) {
            this.container.innerHTML = this.fallbackHTML;
            this.container.classList.add('error-boundary-active');
        }
        ErrorHandler.showUserMessage(`Error in ${this.componentName}: ${error.message}`, 'error');
    }

    recover() {
        if (this.container) {
            this.container.classList.remove('error-boundary-active');
        }
    }
}

// ========================================
// MAIN ERROR HANDLER
// ========================================
const ErrorHandler = {
    _initialized: false,
    _errorLog: [],
    _maxLogSize: 50,
    _currentMessage: null,
    _messageTimeout: null,

    init() {
        if (this._initialized) return;
        this.setupGlobalErrorHandling();
        this.setupOfflineDetection();
        this.injectStyles();
        this._initialized = true;
        console.log('[ErrorHandler] Initialized');
    },

    setupGlobalErrorHandling() {
        window.onerror = (message, source, lineno, colno, error) => {
            this.handleGlobalError({ message, source, lineno, colno, error, type: ErrorTypes.UNKNOWN });
            return true;
        };

        window.addEventListener('unhandledrejection', (event) => {
            this.handleGlobalError({
                message: event.reason?.message || 'Unhandled Promise Rejection',
                error: event.reason,
                type: ErrorTypes.UNKNOWN,
                isPromise: true
            });
        });

        window.addEventListener('error', (event) => {
            if (event.target !== window) {
                const target = event.target;
                if (target.tagName === 'IMG') this.handleImageError(target);
                else if (target.tagName === 'SCRIPT') {
                    this.logError(new Error(`Failed to load script: ${target.src}`), { type: ErrorTypes.NETWORK });
                }
            }
        }, true);
    },

    handleGlobalError(errorInfo) {
        this.logError(errorInfo.error || new Error(errorInfo.message), errorInfo);
        if (ErrorConfig.debug) {
            this.showUserMessage(`Error: ${errorInfo.message}`, 'error', { duration: 3000 });
        }
    },

    setupOfflineDetection() {
        const updateOnlineStatus = () => {
            if (!navigator.onLine) {
                this.showUserMessage('You\'re offline. Some features may not work.', 'warning', { duration: 0 });
                document.body.classList.add('is-offline');
            } else {
                this.hideUserMessage();
                document.body.classList.remove('is-offline');
                this.showUserMessage('You\'re back online!', 'success', { duration: 3000 });
            }
        };

        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        if (!navigator.onLine) updateOnlineStatus();
    },

    // ========================================
    // SAFE LOCAL STORAGE OPERATIONS
    // ========================================
    storage: {
        get(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                if (item === null) return defaultValue;
                return JSON.parse(item);
            } catch (error) {
                ErrorHandler.handleStorageError(error, 'get', key);
                return defaultValue;
            }
        },

        set(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch (error) {
                ErrorHandler.handleStorageError(error, 'set', key);
                return false;
            }
        },

        remove(key) {
            try {
                localStorage.removeItem(key);
                return true;
            } catch (error) {
                ErrorHandler.handleStorageError(error, 'remove', key);
                return false;
            }
        },

        clear() {
            try {
                localStorage.clear();
                return true;
            } catch (error) {
                ErrorHandler.handleStorageError(error, 'clear');
                return false;
            }
        },

        isAvailable() {
            try {
                const test = '__storage_test__';
                localStorage.setItem(test, test);
                localStorage.removeItem(test);
                return true;
            } catch (e) {
                return false;
            }
        },

        getRemainingSpace() {
            try {
                let total = 0;
                for (let key in localStorage) {
                    if (localStorage.hasOwnProperty(key)) {
                        total += localStorage[key].length * 2;
                    }
                }
                return (5 * 1024 * 1024) - total;
            } catch (e) {
                return 0;
            }
        }
    },

    handleStorageError(error, operation, key = '') {
        let userMessage = 'Storage error occurred';
        let type = ErrorTypes.STORAGE;

        if (error.name === 'QuotaExceededError' || error.code === 22 || error.code === 1014) {
            userMessage = 'Storage is full. Please clear some data and try again.';
            this.showUserMessage('⚠️ Storage Full: Your browser storage is full.', 'error', { duration: 0 });
        } else if (error.name === 'NS_ERROR_FILE_CORRUPTED') {
            userMessage = 'Storage appears to be corrupted';
        } else if (error.name === 'SecurityError') {
            userMessage = 'Storage access denied (private browsing mode?)';
        }

        this.logError(error, { type, operation, key, userMessage });
    },

    // ========================================
    // UPLOAD VALIDATION
    // ========================================
    upload: {
        validate(file, options = {}) {
            const maxSize = options.maxSize || ErrorConfig.maxFileSize;
            const allowedTypes = options.allowedTypes || ErrorConfig.allowedImageTypes;

            if (!file) {
                return { valid: false, error: 'No file selected', type: ErrorTypes.VALIDATION };
            }

            if (!allowedTypes.includes(file.type)) {
                return { 
                    valid: false, 
                    error: `Invalid file type. Allowed: ${allowedTypes.map(t => t.replace('image/', '.')).join(', ')}`,
                    type: ErrorTypes.VALIDATION
                };
            }

            if (file.size > maxSize) {
                const maxSizeMB = (maxSize / (1024 * 1024)).toFixed(1);
                const fileSizeMB = (file.size / (1024 * 1024)).toFixed(1);
                return { 
                    valid: false, 
                    error: `File too large (${fileSizeMB}MB). Maximum: ${maxSizeMB}MB`,
                    type: ErrorTypes.VALIDATION
                };
            }

            if (file.size === 0) {
                return { valid: false, error: 'File appears to be empty', type: ErrorTypes.VALIDATION };
            }

            return { valid: true };
        },

        handleReadError(error, file) {
            let message = 'Failed to read file';
            if (error.name === 'NotFoundError') message = 'File not found. It may have been moved or deleted.';
            else if (error.name === 'NotReadableError') message = 'Cannot read file. It may be corrupted.';
            else if (error.name === 'AbortError') message = 'File reading was cancelled.';
            else if (error.name === 'SecurityError') message = 'Security error: Cannot access file.';

            ErrorHandler.showUserMessage(message, 'error');
            ErrorHandler.logError(error, { type: ErrorTypes.UPLOAD, fileName: file?.name });
            return { error: message };
        },

        readAsDataURL(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = () => {
                    const result = this.handleReadError(reader.error, file);
                    reject(new Error(result.error));
                };
                reader.onabort = () => reject(new Error('File reading aborted'));
                reader.readAsDataURL(file);
            });
        }
    },

    // ========================================
    // API ERROR HANDLING WITH RETRY
    // ========================================
    api: {
        async fetchWithRetry(url, options = {}) {
            const maxRetries = options.maxRetries || ErrorConfig.maxRetries;
            const retryDelay = options.retryDelay || ErrorConfig.retryDelay;
            const retryStatuses = options.retryStatuses || [408, 429, 500, 502, 503, 504];
            
            let lastError;
            for (let attempt = 0; attempt < maxRetries; attempt++) {
                try {
                    if (!navigator.onLine) throw new Error('No internet connection');
                    const response = await fetch(url, options);
                    if (!response.ok) {
                        if (retryStatuses.includes(response.status) && attempt < maxRetries - 1) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    return response;
                } catch (error) {
                    lastError = error;
                    if (error.message.includes('HTTP 4') && !retryStatuses.some(s => error.message.includes(`HTTP ${s}`))) break;
                    if (attempt < maxRetries - 1) {
                        const delay = retryDelay * Math.pow(2, attempt);
                        ErrorHandler.showUserMessage(`Connection issue. Retrying... (${attempt + 1}/${maxRetries})`, 'warning', { duration: delay });
                        await this.sleep(delay);
                    }
                }
            }
            throw lastError;
        },

        sleep(ms) {
            return new Promise(resolve => setTimeout(resolve, ms));
        },

        async fetchJSON(url, defaultValue = null) {
            try {
                const response = await this.fetchWithRetry(url);
                return await response.json();
            } catch (error) {
                ErrorHandler.handleAPIError(error, url);
                return defaultValue;
            }
        }
    },

    handleAPIError(error, url) {
        let userMessage = 'Failed to load data. Please try again.';
        let type = ErrorTypes.API;

        if (!navigator.onLine) {
            userMessage = 'You\'re offline. Please check your connection.';
            type = ErrorTypes.NETWORK;
        } else if (error.message.includes('HTTP 404')) userMessage = 'Resource not found.';
        else if (error.message.includes('HTTP 401') || error.message.includes('HTTP 403')) userMessage = 'Access denied. Please log in again.';
        else if (error.message.includes('HTTP 500')) userMessage = 'Server error. Please try again later.';
        else if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            userMessage = 'Network error. Please check your connection.';
            type = ErrorTypes.NETWORK;
        } else if (error.name === 'AbortError') userMessage = 'Request was cancelled.';
        else if (error.name === 'TimeoutError' || error.message.includes('timeout')) userMessage = 'Request timed out.';

        this.showUserMessage(userMessage, 'error');
        this.logError(error, { type, url, userMessage });
    },

    // ========================================
    // 3D VIEWER FALLBACKS
    // ========================================
    viewer3D: {
        isThreeAvailable() {
            return typeof THREE !== 'undefined';
        },

        isWebGLSupported() {
            try {
                const canvas = document.createElement('canvas');
                return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
            } catch (e) {
                return false;
            }
        },

        create2DFallback(containerId, options = {}) {
            const container = document.getElementById(containerId);
            if (!container) return;

            const placeholderImage = options.placeholderImage || '/assets/avatar-placeholder.svg';
            const errorReason = options.errorReason || 'WebGL not supported';

            const fallbackHTML = `
                <div class="viewer-2d-fallback">
                    <div class="fallback-notice">
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 9v2m0 4h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/>
                        </svg>
                        <span>3D view unavailable: ${errorReason}</span>
                    </div>
                    <div class="fallback-image-container">
                        <img src="${placeholderImage}" alt="3D Avatar (2D View)" class="fallback-avatar" onerror="ErrorHandler.handleImageError(this)">
                    </div>
                    <div class="fallback-actions">
                        <button class="btn btn-secondary" onclick="location.reload()">Try 3D Again</button>
                        <a href="dashboard.html" class="btn btn-primary">View Dashboard</a>
                    </div>
                </div>
            `;

            container.innerHTML = fallbackHTML;
            container.classList.add('viewer-2d-mode');
            ErrorHandler.logError(new Error(`3D viewer fallback: ${errorReason}`), { type: ErrorTypes.RENDER, containerId });
        },

        initWithFallback(containerId, init3DFn, fallbackOptions = {}) {
            if (!this.isThreeAvailable()) {
                this.create2DFallback(containerId, { ...fallbackOptions, errorReason: '3D library not loaded' });
                return false;
            }

            if (!this.isWebGLSupported()) {
                this.create2DFallback(containerId, { ...fallbackOptions, errorReason: 'WebGL not supported' });
                return false;
            }

            try {
                const result = init3DFn();
                return result !== false;
            } catch (error) {
                this.create2DFallback(containerId, { ...fallbackOptions, errorReason: '3D initialization failed' });
                ErrorHandler.logError(error, { type: ErrorTypes.RENDER, context: '3D viewer initialization' });
                return false;
            }
        }
    },

    handleImageError(img) {
        if (img.dataset.errorHandled) return;
        img.dataset.errorHandled = 'true';

        const wrapper = img.parentElement;
        const placeholder = document.createElement('div');
        placeholder.className = 'image-error-placeholder';
        placeholder.style.cssText = `
            width: 200px; height: 200px;
            background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
            display: flex; align-items: center; justify-content: center;
            color: white; font-size: 2rem; border-radius: 8px;
        `;
        placeholder.innerHTML = '⚠️';

        if (wrapper && wrapper !== document.body) {
            wrapper.replaceChild(placeholder, img);
        }

        this.logError(new Error(`Image failed to load: ${img.src}`), { type: ErrorTypes.NETWORK, src: img.src });
    },

    // ========================================
    // USER-FRIENDLY ERROR MESSAGES
    // ========================================
    showUserMessage(message, type = 'info', options = {}) {
        const duration = options.duration ?? ErrorConfig.errorDisplayDuration;
        const position = options.position || 'bottom-right';

        this.hideUserMessage();

        const messageEl = document.createElement('div');
        messageEl.className = `error-handler-message error-handler-message--${type} error-handler-message--${position}`;
        messageEl.setAttribute('role', 'alert');
        
        const icons = { error: '❌', warning: '⚠️', success: '✅', info: 'ℹ️' };

        messageEl.innerHTML = `
            <span class="message-icon">${icons[type] || icons.info}</span>
            <span class="message-text">${message}</span>
            <button class="message-close" aria-label="Close">&times;</button>
        `;

        document.body.appendChild(messageEl);
        this._currentMessage = messageEl;

        messageEl.querySelector('.message-close').addEventListener('click', () => this.hideUserMessage());

        if (duration > 0) {
            this._messageTimeout = setTimeout(() => this.hideUserMessage(), duration);
        }

        requestAnimationFrame(() => messageEl.classList.add('is-visible'));
    },

    hideUserMessage() {
        if (this._messageTimeout) {
            clearTimeout(this._messageTimeout);
            this._messageTimeout = null;
        }
        if (this._currentMessage) {
            this._currentMessage.classList.remove('is-visible');
            setTimeout(() => {
                this._currentMessage?.remove();
                this._currentMessage = null;
            }, 300);
        }
    },

    // ========================================
    // ERROR LOGGING
    // ========================================
    logError(error, context = {}) {
        const errorEntry = {
            timestamp: new Date().toISOString(),
            message: error.message || error,
            stack: error.stack,
            type: context.type || ErrorTypes.UNKNOWN,
            ...context
        };

        this._errorLog.unshift(errorEntry);
        if (this._errorLog.length > this._maxLogSize) this._errorLog.pop();

        if (ErrorConfig.debug) console.error('[ErrorHandler]', errorEntry);
    },

    getRecentErrors(count = 10) {
        return this._errorLog.slice(0, count);
    },

    clearErrorLog() {
        this._errorLog = [];
    },

    // ========================================
    // STYLES
    // ========================================
    injectStyles() {
        if (document.getElementById('error-handler-styles')) return;

        const styles = document.createElement('style');
        styles.id = 'error-handler-styles';
        styles.textContent = `
            .error-handler-message {
                position: fixed;
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 16px 20px;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
                font-family: var(--font-family, 'Inter', system-ui, sans-serif);
                font-size: 14px;
                font-weight: 500;
                z-index: 99999;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                max-width: 400px;
                pointer-events: all;
            }
            .error-handler-message.is-visible { opacity: 1; transform: translateY(0) scale(1); }
            .error-handler-message--error { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; }
            .error-handler-message--warning { background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); color: white; }
            .error-handler-message--success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; }
            .error-handler-message--info { background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%); color: white; }
            .error-handler-message--bottom-right { bottom: 24px; right: 24px; }
            .message-icon { font-size: 18px; flex-shrink: 0; }
            .message-text { flex: 1; line-height: 1.4; }
            .message-close {
                background: rgba(255, 255, 255, 0.2);
                border: none;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                cursor: pointer;
                font-size: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .message-close:hover { background: rgba(255, 255, 255, 0.3); }
            
            .error-boundary-fallback {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                padding: 48px 32px;
                text-align: center;
                background: var(--bg-secondary, #1a1a2e);
                border-radius: 16px;
                border: 1px dashed var(--border-color, #3d3d5c);
            }
            .error-boundary-fallback .error-icon { font-size: 48px; margin-bottom: 16px; }
            .error-boundary-fallback h3 { font-size: 20px; font-weight: 600; color: var(--text-primary, #fff); margin-bottom: 8px; }
            .error-boundary-fallback p { color: var(--text-secondary, #9ca3af); margin-bottom: 24px; }
            
            .viewer-2d-fallback {
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100%;
                padding: 32px;
                background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%);
                border-radius: 16px;
            }
            .fallback-notice {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 12px 20px;
                background: rgba(245, 158, 11, 0.1);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 8px;
                color: #f59e0b;
                font-size: 14px;
                margin-bottom: 24px;
            }
            .fallback-image-container { flex: 1; display: flex; align-items: center; justify-content: center; margin-bottom: 24px; }
            .fallback-avatar { max-width: 100%; max-height: 400px; border-radius: 12px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4); }
            .fallback-actions { display: flex; gap: 12px; }
            
            .is-offline .navbar { opacity: 0.8; }
            .is-offline::before {
                content: 'OFFLINE MODE';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                background: #f59e0b;
                color: #000;
                text-align: center;
                padding: 4px;
                font-size: 12px;
                font-weight: 600;
                z-index: 100000;
            }
        `;
        document.head.appendChild(styles);
    }
};

// ========================================
// AUTO-INITIALIZE
// ========================================
if (typeof window !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => ErrorHandler.init());
    } else {
        ErrorHandler.init();
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ErrorHandler, ErrorBoundary, ErrorTypes, ErrorConfig };
}