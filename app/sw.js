/**
 * PhysiqAI Service Worker
 * Provides offline support, caching, and background sync
 */

const CACHE_NAME = 'physiqai-v2';
const STATIC_CACHE = 'physiqai-static-v2';
const DYNAMIC_CACHE = 'physiqai-dynamic-v2';
const IMAGE_CACHE = 'physiqai-images-v2';

// Static assets to cache on install
const STATIC_ASSETS = [
    '/',
    '/app-home.html',
    '/app-avatar.html',
    '/app-dashboard.html',
    '/app-upload.html',
    '/design-system.css',
    '/mobile.css',
    '/mobile-optimized.css',
    '/mobile-touch.js',
    '/firebase-api.js',
    '/app.js'
];

// External resources to cache
const EXTERNAL_RESOURCES = [
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap'
];

// ========================================
// INSTALL EVENT - Cache static assets
// ========================================
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                return caches.open(STATIC_CACHE);
            })
            .then((cache) => {
                // Cache external resources with CORS handling
                return Promise.all(
                    EXTERNAL_RESOURCES.map(url => 
                        fetch(url, { mode: 'no-cors' })
                            .then(response => cache.put(url, response))
                            .catch(err => console.log('[SW] Failed to cache:', url, err))
                    )
                );
            })
            .then(() => {
                console.log('[SW] Static assets cached');
                return self.skipWaiting();
            })
            .catch((err) => {
                console.error('[SW] Cache failed:', err);
            })
    );
});

// ========================================
// ACTIVATE EVENT - Clean up old caches
// ========================================
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            return name.startsWith('physiqai-') && 
                                   !name.includes('v2');
                        })
                        .map((name) => {
                            console.log('[SW] Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Activated');
                return self.clients.claim();
            })
    );
});

// ========================================
// FETCH EVENT - Serve from cache or network
// ========================================
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests
    if (request.method !== 'GET') {
        return;
    }
    
    // Skip Firebase/Google API requests
    if (url.hostname.includes('googleapis.com') || 
        url.hostname.includes('firebase') ||
        url.hostname.includes('firebaseio.com')) {
        return;
    }
    
    // Handle different resource types
    if (isStaticAsset(request)) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
    } else if (isImage(request)) {
        event.respondWith(staleWhileRevalidate(request, IMAGE_CACHE));
    } else {
        event.respondWith(networkFirst(request, DYNAMIC_CACHE));
    }
});

// ========================================
// STRATEGIES
// ========================================

// Cache First - For static assets
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    if (cached) {
        return cached;
    }
    
    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[SW] Fetch failed:', error);
        throw error;
    }
}

// Network First - For dynamic content
async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }
        throw error;
    }
}

// Stale While Revalidate - For images
async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    
    const fetchPromise = fetch(request)
        .then((response) => {
            if (response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(() => cached);
    
    return cached || fetchPromise;
}

// ========================================
// HELPERS
// ========================================

function isStaticAsset(request) {
    const staticExtensions = ['.css', '.js', '.html', '.json', '.woff2', '.woff'];
    return staticExtensions.some(ext => request.url.endsWith(ext));
}

function isImage(request) {
    return request.destination === 'image' || 
           /\.(png|jpg|jpeg|gif|webp|svg)$/i.test(request.url);
}

// ========================================
// BACKGROUND SYNC - Queue actions when offline
// ========================================
const SYNC_QUEUE = [];

self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-weight') {
        event.waitUntil(syncWeightData());
    } else if (event.tag === 'sync-photos') {
        event.waitUntil(syncPhotoUploads());
    }
});

async function syncWeightData() {
    console.log('[SW] Syncing weight data...');
    
    const db = await openDB();
    const pending = await db.getAll('pendingWeights');
    
    for (const entry of pending) {
        try {
            await fetch('/api/weight', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(entry)
            });
            await db.delete('pendingWeights', entry.id);
        } catch (error) {
            console.error('[SW] Failed to sync weight:', error);
        }
    }
}

async function syncPhotoUploads() {
    console.log('[SW] Syncing photo uploads...');
    
    const db = await openDB();
    const pending = await db.getAll('pendingPhotos');
    
    for (const entry of pending) {
        try {
            const formData = new FormData();
            formData.append('photo', entry.blob);
            
            await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            await db.delete('pendingPhotos', entry.id);
        } catch (error) {
            console.error('[SW] Failed to sync photo:', error);
        }
    }
}

// ========================================
// PUSH NOTIFICATIONS
// ========================================
self.addEventListener('push', (event) => {
    const data = event.data.json();
    
    const options = {
        body: data.body,
        icon: '/assets/icon-192x192.png',
        badge: '/assets/badge-72x72.png',
        tag: data.tag || 'default',
        requireInteraction: data.requireInteraction || false,
        actions: data.actions || [],
        data: data.data || {}
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    
    const action = event.action;
    const data = event.notification.data;
    
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then((clientList) => {
                if (clientList.length > 0) {
                    clientList[0].focus();
                    clientList[0].postMessage({
                        type: 'notification-click',
                        action,
                        data
                    });
                } else {
                    clients.openWindow('/app-home.html');
                }
            })
    );
});

// ========================================
// MESSAGE HANDLING - From main thread
// ========================================
self.addEventListener('message', (event) => {
    const { type, payload } = event.data;
    
    switch (type) {
        case 'SKIP_WAITING':
            self.skipWaiting();
            break;
            
        case 'CACHE_URLS':
            cacheUrls(payload.urls);
            break;
            
        case 'CLEAR_CACHE':
            clearCache();
            break;
            
        case 'GET_CACHE_SIZE':
            getCacheSize().then(size => {
                event.ports[0].postMessage({ size });
            });
            break;
    }
});

async function cacheUrls(urls) {
    const cache = await caches.open(DYNAMIC_CACHE);
    await Promise.all(
        urls.map(url => 
            fetch(url)
                .then(response => cache.put(url, response))
                .catch(err => console.error('[SW] Failed to cache:', url, err))
        )
    );
}

async function clearCache() {
    const cacheNames = await caches.keys();
    await Promise.all(
        cacheNames.map(name => caches.delete(name))
    );
}

async function getCacheSize() {
    let totalSize = 0;
    const cacheNames = await caches.keys();
    
    for (const name of cacheNames) {
        const cache = await caches.open(name);
        const requests = await cache.keys();
        
        for (const request of requests) {
            const response = await cache.match(request);
            if (response) {
                const blob = await response.blob();
                totalSize += blob.size;
            }
        }
    }
    
    return totalSize;
}

// ========================================
// INDEXEDDB HELPER (simplified)
// ========================================
async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('PhysiqAI', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            
            if (!db.objectStoreNames.contains('pendingWeights')) {
                db.createObjectStore('pendingWeights', { keyPath: 'id', autoIncrement: true });
            }
            
            if (!db.objectStoreNames.contains('pendingPhotos')) {
                db.createObjectStore('pendingPhotos', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}
