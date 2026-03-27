/**
 * PhysiqAI Service Worker - Clean Build
 * Provides offline support, caching, and background sync
 * Version: 3.0.0
 */

const CACHE_VERSION = '3';
const CACHE_PREFIX = 'physiqai-clean';
const STATIC_CACHE = `${CACHE_PREFIX}-static-v${CACHE_VERSION}`;
const DYNAMIC_CACHE = `${CACHE_PREFIX}-dynamic-v${CACHE_VERSION}`;
const IMAGE_CACHE = `${CACHE_PREFIX}-images-v${CACHE_VERSION}`;

// ========================================
// STATIC ASSETS TO CACHE
// ========================================
const STATIC_ASSETS = [
  // Core pages
  '/projects/physiqai/app/clean/home.html',
  '/projects/physiqai/app/clean/login.html',
  '/projects/physiqai/app/clean/signup.html',
  '/projects/physiqai/app/clean/dashboard.html',
  '/projects/physiqai/app/clean/profile.html',
  '/projects/physiqai/app/clean/settings.html',
  '/projects/physiqai/app/clean/avatar.html',
  '/projects/physiqai/app/clean/upload.html',
  '/projects/physiqai/app/clean/timeline.html',
  '/projects/physiqai/app/clean/weight-tracker.html',
  
  // Core styles
  '/projects/physiqai/app/clean/mobile-styles.css',
  
  // Core scripts
  '/projects/physiqai/app/clean/mobile-core.js',
  '/projects/physiqai/app/clean/firebase-api.js',
  
  // Root fallback
  '/',
  '/index.html'
];

// External resources to cache with CORS
const EXTERNAL_RESOURCES = [
  'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap',
  'https://fonts.gstatic.com/s/inter/v18/UcCO3FwrK3iLTcviYwY.woff2'
];

// ========================================
// INSTALL EVENT
// ========================================
self.addEventListener('install', (event) => {
  console.log('[SW] Installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        // Use addAll with error handling for each asset
        return Promise.all(
          STATIC_ASSETS.map(url => 
            cache.add(url).catch(err => {
              console.warn('[SW] Failed to cache:', url, err.message);
              // Continue even if one fails
              return Promise.resolve();
            })
          )
        );
      })
      .then(() => {
        console.log('[SW] Static assets cached');
        return self.skipWaiting();
      })
      .catch((err) => {
        console.error('[SW] Install failed:', err);
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
              // Delete old versioned caches
              return name.startsWith(CACHE_PREFIX) && 
                     !name.includes(`-v${CACHE_VERSION}`);
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
      url.hostname.includes('firebaseio.com') ||
      url.hostname.includes('google-analytics')) {
    return;
  }
  
  // Skip API calls
  if (url.pathname.includes('/api/')) {
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
// CACHING STRATEGIES
// ========================================

// Cache First - For static assets (CSS, JS, HTML)
async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  if (cached) {
    return cached;
  }
  
  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.error('[SW] Network fetch failed:', error);
    // Return offline fallback if available
    return caches.match('/projects/physiqai/app/clean/home.html');
  }
}

// Network First - For dynamic content
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  
  try {
    const networkResponse = await fetch(request);
    if (networkResponse && networkResponse.ok) {
      cache.put(request, networkResponse.clone());
    }
    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache...');
    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }
    // Return offline page
    return caches.match('/projects/physiqai/app/clean/home.html');
  }
}

// Stale While Revalidate - For images
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  
  const fetchPromise = fetch(request)
    .then((response) => {
      if (response && response.ok) {
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
  const staticExtensions = ['.css', '.js', '.html', '.json', '.woff2', '.woff', '.ttf'];
  return staticExtensions.some(ext => request.url.toLowerCase().endsWith(ext));
}

function isImage(request) {
  const imageExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.avif'];
  return request.destination === 'image' || 
         imageExtensions.some(ext => request.url.toLowerCase().endsWith(ext));
}

// ========================================
// BACKGROUND SYNC
// ========================================
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-weight') {
    event.waitUntil(syncWeightData());
  } else if (event.tag === 'sync-photos') {
    event.waitUntil(syncPhotoUploads());
  }
});

async function syncWeightData() {
  console.log('[SW] Syncing weight data...');
  
  try {
    const db = await openIndexedDB();
    const pending = await db.getAll('pendingWeights');
    
    for (const entry of pending) {
      try {
        const response = await fetch('/api/weight', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(entry)
        });
        
        if (response.ok) {
          await db.delete('pendingWeights', entry.id);
          console.log('[SW] Synced weight entry:', entry.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync weight:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Sync failed:', error);
  }
}

async function syncPhotoUploads() {
  console.log('[SW] Syncing photo uploads...');
  
  try {
    const db = await openIndexedDB();
    const pending = await db.getAll('pendingPhotos');
    
    for (const entry of pending) {
      try {
        const formData = new FormData();
        formData.append('photo', entry.blob);
        
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData
        });
        
        if (response.ok) {
          await db.delete('pendingPhotos', entry.id);
          console.log('[SW] Synced photo:', entry.id);
        }
      } catch (error) {
        console.error('[SW] Failed to sync photo:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Photo sync failed:', error);
  }
}

// ========================================
// PUSH NOTIFICATIONS
// ========================================
self.addEventListener('push', (event) => {
  let data = {};
  try {
    data = event.data.json();
  } catch (e) {
    data = {
      title: 'PhysiqAI',
      body: event.data.text()
    };
  }
  
  const options = {
    body: data.body || 'New notification',
    icon: '/assets/icon-192x192.png',
    badge: '/assets/badge-72x72.png',
    tag: data.tag || 'default',
    requireInteraction: data.requireInteraction || false,
    actions: data.actions || [],
    data: data.data || {},
    vibrate: [100, 50, 100]
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'PhysiqAI', options)
  );
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  const action = event.action;
  const data = event.notification.data;
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true })
      .then((clientList) => {
        // Try to focus existing window
        for (const client of clientList) {
          if (client.url.includes('physiqai') && 'focus' in client) {
            client.focus();
            client.postMessage({
              type: 'notification-click',
              action,
              data
            });
            return;
          }
        }
        // Open new window if none exists
        if (clients.openWindow) {
          clients.openWindow('/projects/physiqai/app/clean/home.html');
        }
      })
  );
});

// ========================================
// MESSAGE HANDLING
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
      clearAllCaches();
      break;
      
    case 'GET_CACHE_SIZE':
      getCacheSize().then(size => {
        if (event.ports && event.ports[0]) {
          event.ports[0].postMessage({ size });
        }
      });
      break;
      
    case 'CACHE_OFFLINE':
      // Cache for offline use
      if (payload && payload.url) {
        cacheOfflinePage(payload.url);
      }
      break;
  }
});

async function cacheUrls(urls) {
  const cache = await caches.open(DYNAMIC_CACHE);
  await Promise.all(
    urls.map(url => 
      fetch(url)
        .then(response => {
          if (response.ok) {
            return cache.put(url, response);
          }
        })
        .catch(err => console.error('[SW] Failed to cache:', url, err))
    )
  );
}

async function clearAllCaches() {
  const cacheNames = await caches.keys();
  await Promise.all(
    cacheNames
      .filter(name => name.startsWith(CACHE_PREFIX))
      .map(name => caches.delete(name))
  );
  console.log('[SW] All caches cleared');
}

async function getCacheSize() {
  let totalSize = 0;
  const cacheNames = await caches.keys();
  
  for (const name of cacheNames) {
    if (!name.startsWith(CACHE_PREFIX)) continue;
    
    const cache = await caches.open(name);
    const requests = await cache.keys();
    
    for (const request of requests) {
      try {
        const response = await cache.match(request);
        if (response) {
          const blob = await response.blob();
          totalSize += blob.size;
        }
      } catch (e) {
        // Ignore errors for individual items
      }
    }
  }
  
  return {
    bytes: totalSize,
    kb: Math.round(totalSize / 1024 * 100) / 100,
    mb: Math.round(totalSize / 1024 / 1024 * 100) / 100
  };
}

async function cacheOfflinePage(url) {
  const cache = await caches.open(STATIC_CACHE);
  try {
    const response = await fetch(url);
    if (response.ok) {
      await cache.put(url, response);
      console.log('[SW] Cached for offline:', url);
    }
  } catch (error) {
    console.error('[SW] Failed to cache for offline:', url, error);
  }
}

// ========================================
// INDEXEDDB HELPER
// ========================================
function openIndexedDB() {
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

// Add methods to IDBDatabase for easier usage
IDBDatabase.prototype.getAll = function(storeName) {
  return new Promise((resolve, reject) => {
    const transaction = this.transaction(storeName, 'readonly');
    const store = transaction.objectStore(storeName);
    const request = store.getAll();
    
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
};

IDBDatabase.prototype.delete = function(storeName, key) {
  return new Promise((resolve, reject) => {
    const transaction = this.transaction(storeName, 'readwrite');
    const store = transaction.objectStore(storeName);
    const request = store.delete(key);
    
    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};
