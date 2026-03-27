/**
 * PhysiqAI - Firebase Integration Layer
 * 
 * Replaces localStorage with Firebase Firestore
 * Provides seamless migration from localStorage to cloud storage
 * Falls back to localStorage when offline
 */

import {
  saveWeight,
  getWeightHistory,
  getLatestWeight,
  saveWorkout,
  getWorkouts,
  savePhoto,
  getPhotos,
  getAvatarState,
  updateAvatarParams,
  getUserProfile,
  onAuthChange,
  getCurrentUserId
} from './firebase-api.js';

// ============================================================================
// Firebase Data Store - Drop-in replacement for PhysiqDataStore
// ============================================================================

class FirebaseDataStore {
  constructor() {
    this.STORAGE_KEYS = {
      WEIGHT: 'weight_tracker_data_v1',
      SETTINGS: 'weight_tracker_settings_v1',
      WORKOUTS: 'physiq_workouts_v1',
      PHOTOS: 'physiq_photos_v1',
      PREDICTIONS: 'physiq_predictions_v1',
      INSIGHTS: 'physiq_insights_v1',
      AVATAR_STATE: 'physiq_avatar_state_v1',
      TIMELINE: 'physiq_timeline_v1'
    };
    this.cache = {};
    this.subscribers = {};
    this.userId = null;
    this.isOnline = navigator.onLine;
    
    // Listen for auth changes
    onAuthChange((user) => {
      this.userId = user?.uid || null;
      if (this.userId) {
        this.hydrate();
      }
    });
    
    // Listen for online/offline changes
    window.addEventListener('online', () => { this.isOnline = true; });
    window.addEventListener('offline', () => { this.isOnline = false; });
  }

  /**
   * Get data from Firebase (with localStorage fallback)
   */
  async get(key, defaultValue = null) {
    // Check cache first
    if (this.cache[key] !== undefined) return this.cache[key];
    
    // If no user is logged in, fall back to localStorage
    if (!this.userId) {
      return this._getFromLocalStorage(key, defaultValue);
    }
    
    // If offline, use localStorage
    if (!this.isOnline) {
      return this._getFromLocalStorage(key, defaultValue);
    }
    
    try {
      let data;
      
      switch (key) {
        case this.STORAGE_KEYS.WEIGHT:
          const { logs } = await getWeightHistory(this.userId);
          data = this._transformWeightLogs(logs);
          break;
          
        case this.STORAGE_KEYS.WORKOUTS:
          const { workouts } = await getWorkouts(this.userId);
          data = workouts;
          break;
          
        case this.STORAGE_KEYS.PHOTOS:
          const { photos } = await getPhotos(this.userId);
          data = photos;
          break;
          
        case this.STORAGE_KEYS.AVATAR_STATE:
          const { state } = await getAvatarState(this.userId);
          data = state;
          break;
          
        case this.STORAGE_KEYS.SETTINGS:
          const { profile } = await getUserProfile(this.userId);
          data = profile?.settings || defaultValue;
          break;
          
        default:
          data = this._getFromLocalStorage(key, defaultValue);
      }
      
      this.cache[key] = data;
      return data;
    } catch (error) {
      console.warn(`Firebase get failed for ${key}, falling back to localStorage:`, error);
      return this._getFromLocalStorage(key, defaultValue);
    }
  }

  /**
   * Set data to Firebase (with localStorage backup)
   */
  async set(key, value, emitEvent = true) {
    this.cache[key] = value;
    
    // Always save to localStorage as backup
    this._setToLocalStorage(key, value);
    
    // If no user or offline, don't try Firebase
    if (!this.userId || !this.isOnline) {
      if (emitEvent) this._emitEvent(key, value);
      return true;
    }
    
    try {
      switch (key) {
        case this.STORAGE_KEYS.WEIGHT:
          // Weight data is saved via logWeight, not set
          break;
          
        case this.STORAGE_KEYS.WORKOUTS:
          // Workouts saved via saveWorkout
          break;
          
        case this.STORAGE_KEYS.AVATAR_STATE:
          if (value.current_params) {
            await updateAvatarParams(this.userId, value.current_params);
          }
          break;
          
        default:
          // For other data, just keep in localStorage
          break;
      }
      
      if (emitEvent) this._emitEvent(key, value);
      
      // Notify subscribers
      if (this.subscribers[key]) {
        this.subscribers[key].forEach(cb => cb(value));
      }
      
      return true;
    } catch (error) {
      console.error(`Firebase set failed for ${key}:`, error);
      // Data is still in localStorage as backup
      return true;
    }
  }

  /**
   * Subscribe to data changes
   */
  subscribe(key, callback) {
    if (!this.subscribers[key]) this.subscribers[key] = [];
    this.subscribers[key].push(callback);
    
    // Get current value
    this.get(key).then(value => callback(value));
    
    // Return unsubscribe function
    return () => {
      this.subscribers[key] = this.subscribers[key].filter(cb => cb !== callback);
    };
  }

  /**
   * Hydrate cache from Firebase
   */
  async hydrate() {
    if (!this.userId) return;
    
    await Promise.all([
      this.get(this.STORAGE_KEYS.WEIGHT),
      this.get(this.STORAGE_KEYS.WORKOUTS),
      this.get(this.STORAGE_KEYS.PHOTOS),
      this.get(this.STORAGE_KEYS.AVATAR_STATE)
    ]);
  }

  // ============================================================================
  // Data Transformers
  // ============================================================================

  _transformWeightLogs(logs) {
    if (!logs || logs.length === 0) {
      return {
        entries: [],
        goal: { targetWeight: null, targetDate: null },
        milestones: []
      };
    }
    
    // Sort by date ascending
    const sorted = [...logs].sort((a, b) => a.date - b.date);
    const latest = sorted[sorted.length - 1];
    
    return {
      entries: sorted.map(log => ({
        id: log.id,
        weight: log.weight,
        date: log.date instanceof Date ? log.date.toISOString().split('T')[0] : log.date,
        notes: log.notes || '',
        timestamp: log.created_at?.toISOString() || new Date().toISOString()
      })),
      current: {
        weight: latest.weight,
        date: latest.date instanceof Date ? latest.date.toISOString().split('T')[0] : latest.date
      },
      goal: { targetWeight: null, targetDate: null },
      milestones: []
    };
  }

  // ============================================================================
  // LocalStorage Helpers (for fallback)
  // ============================================================================

  _getFromLocalStorage(key, defaultValue = null) {
    try {
      const stored = localStorage.getItem(key);
      return stored ? JSON.parse(stored) : defaultValue;
    } catch (e) {
      return defaultValue;
    }
  }

  _setToLocalStorage(key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
      return true;
    } catch (e) {
      return false;
    }
  }

  _emitEvent(key, value) {
    const eventName = key.replace('_v1', '').replace('physiq_', '').replace('weight_tracker_', '');
    if (window.physiqBus) {
      window.physiqBus.emit(`data:${eventName}`, { key, value });
    }
  }

  // ============================================================================
  // Convenience Methods
  // ============================================================================

  getWeightData() {
    return this.get(this.STORAGE_KEYS.WEIGHT, { 
      entries: [], 
      goal: { targetWeight: null, targetDate: null }, 
      milestones: [] 
    });
  }

  getSettings() { 
    return this.get(this.STORAGE_KEYS.SETTINGS, { unit: 'lbs', goalWeight: null }); 
  }
  
  getWorkouts() { 
    return this.get(this.STORAGE_KEYS.WORKOUTS, []); 
  }
  
  getPhotos() { 
    return this.get(this.STORAGE_KEYS.PHOTOS, []); 
  }
  
  getAvatarState() {
    return this.get(this.STORAGE_KEYS.AVATAR_STATE, { 
      currentWeight: 180, 
      targetWeight: 170, 
      morphLevel: 0, 
      lastUpdated: null 
    });
  }
}

// ============================================================================
// Firebase Integration - Drop-in replacement for PhysiqIntegration
// ============================================================================

class FirebaseIntegration {
  constructor() {
    this.store = new FirebaseDataStore();
    this.userId = null;
    
    onAuthChange((user) => {
      this.userId = user?.uid || null;
      if (this.userId) {
        this.store.hydrate();
      }
    });
  }

  /**
   * Log a weight entry
   * @param {number} weight 
   * @param {string} date - YYYY-MM-DD
   * @param {string} notes 
   * @returns {Promise<object>}
   */
  async logWeight(weight, date = null, notes = '') {
    const userId = this.userId || getCurrentUserId();
    if (!userId) {
      console.warn('No user logged in, saving to localStorage only');
      return this._fallbackLogWeight(weight, date, notes);
    }
    
    const entryDate = date ? new Date(date) : new Date();
    
    try {
      const result = await saveWeight(userId, weight, entryDate, notes);
      
      if (result.error) throw new Error(result.error.message);
      
      // Update cache
      const weightData = await this.store.getWeightData();
      const newEntry = {
        id: result.id,
        weight: parseFloat(weight),
        date: entryDate.toISOString().split('T')[0],
        notes,
        timestamp: new Date().toISOString()
      };
      
      weightData.entries = weightData.entries || [];
      weightData.entries.push(newEntry);
      weightData.entries.sort((a, b) => new Date(a.date) - new Date(b.date));
      weightData.current = newEntry;
      
      await this.store.set(this.store.STORAGE_KEYS.WEIGHT, weightData);
      
      // Emit events
      if (window.physiqBus) {
        window.physiqBus.emit('weight:logged', { weight, date: newEntry.date, entry: newEntry });
      }
      
      return newEntry;
    } catch (error) {
      console.error('Failed to save weight to Firebase:', error);
      return this._fallbackLogWeight(weight, date, notes);
    }
  }

  /**
   * Save a workout
   * @param {object} workout 
   * @returns {Promise<object>}
   */
  async saveWorkout(workout) {
    const userId = this.userId || getCurrentUserId();
    if (!userId) {
      return this._fallbackSaveWorkout(workout);
    }
    
    try {
      const result = await saveWorkout(userId, workout);
      
      if (result.error) throw new Error(result.error.message);
      
      const newWorkout = {
        id: result.id,
        ...workout,
        timestamp: new Date().toISOString()
      };
      
      // Update cache
      const workouts = await this.store.getWorkouts();
      workouts.push(newWorkout);
      await this.store.set(this.store.STORAGE_KEYS.WORKOUTS, workouts);
      
      // Emit event
      if (window.physiqBus) {
        window.physiqBus.emit('workout:saved', newWorkout);
      }
      
      return newWorkout;
    } catch (error) {
      console.error('Failed to save workout to Firebase:', error);
      return this._fallbackSaveWorkout(workout);
    }
  }

  /**
   * Upload a photo
   * @param {object} photoData - { file, src, type, date }
   * @returns {Promise<object>}
   */
  async uploadPhoto(photoData) {
    const userId = this.userId || getCurrentUserId();
    if (!userId) {
      return this._fallbackUploadPhoto(photoData);
    }
    
    try {
      let result;
      
      if (photoData.file) {
        result = await savePhoto(userId, photoData.file, photoData.type || 'progress', 
          photoData.date ? new Date(photoData.date) : new Date());
      } else {
        // Data URL - convert to file
        const response = await fetch(photoData.src);
        const blob = await response.blob();
        const file = new File([blob], 'photo.jpg', { type: 'image/jpeg' });
        result = await savePhoto(userId, file, photoData.type || 'progress', 
          photoData.date ? new Date(photoData.date) : new Date());
      }
      
      if (result.error) throw new Error(result.error.message);
      
      const newPhoto = {
        id: result.id,
        url: result.url,
        src: result.url,
        type: photoData.type || 'progress',
        date: photoData.date || new Date().toISOString().split('T')[0],
        timestamp: new Date().toISOString()
      };
      
      // Update cache
      const photos = await this.store.getPhotos();
      photos.push(newPhoto);
      await this.store.set(this.store.STORAGE_KEYS.PHOTOS, photos);
      
      // Emit event
      if (window.physiqBus) {
        window.physiqBus.emit('photo:uploaded', newPhoto);
      }
      
      return newPhoto;
    } catch (error) {
      console.error('Failed to upload photo to Firebase:', error);
      return this._fallbackUploadPhoto(photoData);
    }
  }

  /**
   * Get timeline of all activities
   * @returns {Promise<array>}
   */
  async getTimeline() {
    const [photos, weightData, workouts] = await Promise.all([
      this.store.getPhotos(),
      this.store.getWeightData(),
      this.store.getWorkouts()
    ]);
    
    const timeline = [];
    
    photos.forEach(p => timeline.push({ 
      type: 'photo', 
      date: p.date, 
      data: p, 
      timestamp: new Date(p.timestamp || p.date).getTime() 
    }));
    
    weightData.entries?.forEach(e => timeline.push({ 
      type: 'weight', 
      date: e.date, 
      data: e, 
      timestamp: new Date(e.timestamp || e.date).getTime() 
    }));
    
    workouts.forEach(w => timeline.push({ 
      type: 'workout', 
      date: w.date || w.timestamp?.split('T')[0], 
      data: w, 
      timestamp: new Date(w.timestamp || w.date).getTime() 
    }));
    
    return timeline.sort((a, b) => b.timestamp - a.timestamp);
  }

  /**
   * Refresh all data from Firebase
   */
  async refresh() {
    await this.store.hydrate();
    if (window.physiqBus) {
      window.physiqBus.emit('data:refreshed', {});
    }
  }

  // ============================================================================
  // Fallback Methods (localStorage only)
  // ============================================================================

  _fallbackLogWeight(weight, date, notes) {
    const weightData = JSON.parse(localStorage.getItem(this.store.STORAGE_KEYS.WEIGHT) || '{}');
    const entries = weightData.entries || [];
    
    const entry = {
      id: Date.now().toString(),
      weight: parseFloat(weight),
      date: date || new Date().toISOString().split('T')[0],
      notes,
      timestamp: new Date().toISOString()
    };
    
    entries.push(entry);
    entries.sort((a, b) => new Date(a.date) - new Date(b.date));
    
    weightData.entries = entries;
    localStorage.setItem(this.store.STORAGE_KEYS.WEIGHT, JSON.stringify(weightData));
    
    if (window.physiqBus) {
      window.physiqBus.emit('weight:logged', { weight: entry.weight, date: entry.date, entry });
    }
    
    return entry;
  }

  _fallbackSaveWorkout(workout) {
    const workouts = JSON.parse(localStorage.getItem(this.store.STORAGE_KEYS.WORKOUTS) || '[]');
    const newWorkout = {
      id: Date.now().toString(),
      ...workout,
      timestamp: new Date().toISOString()
    };
    workouts.push(newWorkout);
    localStorage.setItem(this.store.STORAGE_KEYS.WORKOUTS, JSON.stringify(workouts));
    
    if (window.physiqBus) {
      window.physiqBus.emit('workout:saved', newWorkout);
    }
    
    return newWorkout;
  }

  _fallbackUploadPhoto(photoData) {
    const photos = JSON.parse(localStorage.getItem(this.store.STORAGE_KEYS.PHOTOS) || '[]');
    const newPhoto = {
      id: Date.now().toString(),
      ...photoData,
      timestamp: new Date().toISOString()
    };
    photos.push(newPhoto);
    localStorage.setItem(this.store.STORAGE_KEYS.PHOTOS, JSON.stringify(photos));
    
    if (window.physiqBus) {
      window.physiqBus.emit('photo:uploaded', newPhoto);
    }
    
    return newPhoto;
  }
}

// ============================================================================
// Initialize and Export
// ============================================================================

// Create global instance
const firebaseIntegration = new FirebaseIntegration();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    console.log('[FirebaseIntegration] Ready');
  });
} else {
  console.log('[FirebaseIntegration] Ready');
}

// Export for use as ES module
export { FirebaseDataStore, FirebaseIntegration, firebaseIntegration };

// Export global for non-module usage
if (typeof window !== 'undefined') {
  window.FirebaseIntegration = FirebaseIntegration;
  window.firebaseIntegration = firebaseIntegration;
  window.firebaseStore = firebaseIntegration.store;
}