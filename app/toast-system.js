/**
 * PhysiqAI - Toast Notification System
 * Production-ready notifications with queue management
 */

const ToastSystem = {
    container: null,
    queue: [],
    active: [],
    maxVisible: 3,
    defaultDuration: 5000,

    init() {
        if (this.container) return;
        this.container = document.createElement('div');
        this.container.className = 'toast-container';
        document.body.appendChild(this.container);
    },

    show(message, type = 'info', options = {}) {
        this.init();
        const duration = options.duration ?? this.defaultDuration;
        const id = Date.now() + Math.random();
        
        const toast = { id, message, type, duration, options };
        
        if (this.active.length >= this.maxVisible) {
            this.queue.push(toast);
        } else {
            this.display(toast);
        }
        
        return id;
    },

    display(toast) {
        const el = document.createElement('div');
        el.className = `toast toast--${toast.type}`;
        el.dataset.id = toast.id;
        
        const icons = {
            success: '✓',
            error: '✕',
            warning: '⚠',
            info: 'ℹ'
        };
        
        el.innerHTML = `
            <span class="toast-icon">${icons[toast.type]}</span>
            <span class="toast-text">${toast.message}</span>
            <button class="toast-close" onclick="ToastSystem.dismiss('${toast.id}')">×</button>
        `;
        
        this.container.appendChild(el);
        this.active.push(toast);
        
        // Trigger animation
        requestAnimationFrame(() => el.classList.add('show'));
        
        // Auto dismiss
        if (toast.duration > 0) {
            toast.timeout = setTimeout(() => this.dismiss(toast.id), toast.duration);
        }
    },

    dismiss(id) {
        const index = this.active.findIndex(t => t.id == id);
        if (index === -1) return;
        
        const toast = this.active[index];
        if (toast.timeout) clearTimeout(toast.timeout);
        
        const el = this.container.querySelector(`[data-id="${id}"]`);
        if (el) {
            el.classList.remove('show');
            setTimeout(() => el.remove(), 400);
        }
        
        this.active.splice(index, 1);
        
        // Show next from queue
        if (this.queue.length > 0 && this.active.length < this.maxVisible) {
            setTimeout(() => this.display(this.queue.shift()), 100);
        }
    },

    success(message, options) { return this.show(message, 'success', options); },
    error(message, options) { return this.show(message, 'error', options); },
    warning(message, options) { return this.show(message, 'warning', options); },
    info(message, options) { return this.show(message, 'info', options); },

    clear() {
        this.active.forEach(t => {
            if (t.timeout) clearTimeout(t.timeout);
        });
        this.active = [];
        this.queue = [];
        if (this.container) this.container.innerHTML = '';
    }
};

// Page Transition System
const PageTransition = {
    overlay: null,
    
    init() {
        if (this.overlay) return;
        this.overlay = document.createElement('div');
        this.overlay.className = 'page-transition';
        this.overlay.innerHTML = `
            <div class="page-transition-content">
                <div class="page-transition-spinner"></div>
                <p>Loading...</p>
            </div>
        `;
        document.body.appendChild(this.overlay);
        
        // Intercept link clicks
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (!link) return;
            
            const href = link.getAttribute('href');
            if (href.startsWith('#') || href.startsWith('http') || href.startsWith('mailto:')) return;
            if (link.dataset.noTransition) return;
            
            e.preventDefault();
            this.navigate(href);
        });
    },
    
    navigate(href) {
        this.show();
        setTimeout(() => {
            window.location.href = href;
        }, 300);
    },
    
    show() {
        this.init();
        this.overlay.classList.add('active');
    },
    
    hide() {
        if (this.overlay) {
            this.overlay.classList.remove('active');
        }
    }
};

// Lazy Loading for Images
const LazyLoader = {
    observer: null,
    
    init() {
        if (this.observer) return;
        
        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.load(entry.target);
                    this.observer.unobserve(entry.target);
                }
            });
        }, { rootMargin: '50px' });
        
        document.querySelectorAll('img[data-src]').forEach(img => {
            this.observer.observe(img);
        });
    },
    
    load(img) {
        const src = img.dataset.src;
        if (!src) return;
        
        img.classList.add('lazy-image');
        
        const tempImg = new Image();
        tempImg.onload = () => {
            img.src = src;
            img.classList.add('loaded');
            img.removeAttribute('data-src');
        };
        tempImg.onerror = () => {
            img.classList.add('error');
            console.error('Failed to load image:', src);
        };
        tempImg.src = src;
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    PageTransition.init();
    LazyLoader.init();
    
    // Hide transition after page load
    window.addEventListener('load', () => {
        setTimeout(() => PageTransition.hide(), 100);
    });
    
    // Skeleton loading removal
    document.querySelectorAll('.skeleton').forEach(el => {
        el.classList.remove('skeleton');
    });
});

// Export for use
window.ToastSystem = ToastSystem;
window.PageTransition = PageTransition;
window.LazyLoader = LazyLoader;
