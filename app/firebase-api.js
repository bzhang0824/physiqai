/**
 * PhysiqAI - Firebase API (Browser-Compatible Version)
 * 
 * Uses Firebase v9+ modular SDK via CDN
 * Provides simple API wrapper functions for:
 * - Authentication (Email + Google)
 * - Weight logs
 * - Workouts  
 * - Photos
 * - Avatar state
 * 
 * Usage:
 *   <script type="module">
 *     import { saveWeight, getWeightHistory } from './firebase-api.js';
 *     await saveWeight(userId, 175.5, new Date());
 *   </script>
 */

// ============================================================================
// Firebase SDK Imports (CDN)
// ============================================================================
import { 
  initializeApp, 
  getApps, 
  getApp 
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-app.js";
import { 
  getAuth, 
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  onAuthStateChanged,
  updateProfile,
  sendPasswordResetEmail,
  sendEmailVerification,
  setPersistence,
  browserLocalPersistence,
  browserSessionPersistence
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-auth.js";
import { 
  getFirestore,
  collection,
  doc,
  setDoc,
  getDoc,
  getDocs,
  updateDoc,
  deleteDoc,
  query,
  where,
  orderBy,
  limit,
  Timestamp,
  serverTimestamp,
  enableIndexedDbPersistence
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-firestore.js";
import { 
  getStorage,
  ref,
  uploadBytes,
  uploadBytesResumable,
  getDownloadURL,
  deleteObject
} from "https://www.gstatic.com/firebasejs/10.8.0/firebase-storage.js";

// ============================================================================
// Firebase Configuration
// ============================================================================

// Firebase config for PhysiqAI
const defaultConfig = {
  apiKey: "AIzaSyDQnKtxk_uCiW7owBCSf6ABKE2b5QKdqiU",
  authDomain: "physiqai.firebaseapp.com",
  projectId: "physiqai",
  storageBucket: "physiqai.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123def456"
};

// Try to load config from window.firebaseConfig (set in HTML) or use default
const firebaseConfig = (typeof window !== 'undefined' && window.firebaseConfig) || defaultConfig;

// Initialize Firebase
function initializeFirebase() {
  if (getApps().length === 0) {
    const app = initializeApp(firebaseConfig);
    const db = getFirestore(app);
    
    // Enable offline persistence
    enableIndexedDbPersistence(db).catch((err) => {
      if (err.code === 'failed-precondition') {
        console.warn('Persistence: Multiple tabs open');
      } else if (err.code === 'unimplemented') {
        console.warn('Persistence: Browser not supported');
      }
    });
    
    return app;
  }
  return getApp();
}

const app = initializeFirebase();
const auth = getAuth(app);
const db = getFirestore(app);
const storage = getStorage(app);

const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: 'select_account' });

// ============================================================================
// Collection Names
// ============================================================================
const COLLECTIONS = {
  USERS: 'users',
  WEIGHT_LOGS: 'weight_logs',
  WORKOUTS: 'workouts',
  PHOTOS: 'photos',
  AVATAR_STATE: 'avatar_state'
};

// ============================================================================
// AUTHENTICATION API
// ============================================================================

/**
 * Sign up with email and password
 * @param {string} email 
 * @param {string} password 
 * @param {object} profile - { displayName, photoURL }
 * @returns {Promise<{user: object|null, error: object|null}>}
 */
export async function signUpWithEmail(email, password, profile = {}) {
  try {
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const user = userCredential.user;
    
    // Update profile if displayName provided
    if (profile.displayName) {
      await updateProfile(user, {
        displayName: profile.displayName,
        photoURL: profile.photoURL || null
      });
    }
    
    // Create user document in Firestore
    await setDoc(doc(db, COLLECTIONS.USERS, user.uid), {
      email: user.email,
      displayName: profile.displayName || email.split('@')[0],
      photoURL: profile.photoURL || null,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp()
    });
    
    return { user, error: null };
  } catch (error) {
    console.error('Sign up error:', error);
    return { user: null, error: formatAuthError(error) };
  }
}

/**
 * Sign in with email and password
 * @param {string} email 
 * @param {string} password 
 * @param {boolean} rememberMe - Whether to persist session across browser restarts
 * @returns {Promise<{user: object|null, error: object|null}>}
 */
export async function signInWithEmail(email, password, rememberMe = true) {
  try {
    // Set persistence based on rememberMe option
    const persistence = rememberMe ? browserLocalPersistence : browserSessionPersistence;
    await setPersistence(auth, persistence);
    
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    
    // Store preference for reference
    localStorage.setItem('rememberMe', rememberMe.toString());
    
    return { user: userCredential.user, error: null };
  } catch (error) {
    console.error('Sign in error:', error);
    return { user: null, error: formatAuthError(error) };
  }
}

/**
 * Sign in with Google
 * @param {boolean} rememberMe - Whether to persist session across browser restarts
 * @returns {Promise<{user: object|null, isNewUser: boolean, error: object|null}>}
 */
export async function signInWithGoogle(rememberMe = true) {
  try {
    // Set persistence based on rememberMe option
    const persistence = rememberMe ? browserLocalPersistence : browserSessionPersistence;
    await setPersistence(auth, persistence);
    
    const result = await signInWithPopup(auth, googleProvider);
    const user = result.user;
    const isNewUser = result._tokenResponse?.isNewUser || false;
    
    // Create user document if new user
    if (isNewUser) {
      await setDoc(doc(db, COLLECTIONS.USERS, user.uid), {
        email: user.email,
        displayName: user.displayName,
        photoURL: user.photoURL,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
    }
    
    // Store preference for reference
    localStorage.setItem('rememberMe', rememberMe.toString());
    
    return { user, isNewUser, error: null };
  } catch (error) {
    console.error('Google sign in error:', error);
    return { user: null, isNewUser: false, error: formatAuthError(error) };
  }
}

/**
 * Sign out current user
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function signOutUser() {
  try {
    await signOut(auth);
    return { success: true, error: null };
  } catch (error) {
    console.error('Sign out error:', error);
    return { success: false, error: formatAuthError(error) };
  }
}

/**
 * Send password reset email
 * @param {string} email 
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function resetPassword(email) {
  try {
    await sendPasswordResetEmail(auth, email);
    return { success: true, error: null };
  } catch (error) {
    console.error('Password reset error:', error);
    return { success: false, error: formatAuthError(error) };
  }
}

/**
 * Subscribe to auth state changes
 * @param {function} callback - Called with user object or null
 * @returns {function} Unsubscribe function
 */
export function onAuthChange(callback) {
  return onAuthStateChanged(auth, callback);
}

/**
 * Get current user
 * @returns {object|null} Current user or null
 */
export function getCurrentUser() {
  return auth.currentUser;
}

/**
 * Get current user ID
 * @returns {string|null} Current user ID or null
 */
export function getCurrentUserId() {
  return auth.currentUser?.uid || null;
}

// ============================================================================
// WEIGHT API
// ============================================================================

/**
 * Save a weight log entry
 * @param {string} userId 
 * @param {number} weight - Weight in lbs/kg
 * @param {Date} date - Date of weigh-in
 * @param {string} notes - Optional notes
 * @returns {Promise<{id: string|null, error: object|null}>}
 */
export async function saveWeight(userId, weight, date = new Date(), notes = '') {
  try {
    const weightLogRef = doc(collection(db, COLLECTIONS.WEIGHT_LOGS));
    const data = {
      user_id: userId,
      weight: Number(weight),
      date: Timestamp.fromDate(date),
      notes: notes || '',
      created_at: serverTimestamp()
    };
    
    await setDoc(weightLogRef, data);
    return { id: weightLogRef.id, error: null };
  } catch (error) {
    console.error('Save weight error:', error);
    return { id: null, error: { message: error.message } };
  }
}

/**
 * Get weight history for a user
 * @param {string} userId 
 * @param {object} options - { limit: number, startDate: Date, endDate: Date }
 * @returns {Promise<{logs: array, error: object|null}>}
 */
export async function getWeightHistory(userId, options = {}) {
  try {
    let q = query(
      collection(db, COLLECTIONS.WEIGHT_LOGS),
      where('user_id', '==', userId),
      orderBy('date', 'desc')
    );
    
    if (options.startDate) {
      q = query(q, where('date', '>=', Timestamp.fromDate(options.startDate)));
    }
    if (options.endDate) {
      q = query(q, where('date', '<=', Timestamp.fromDate(options.endDate)));
    }
    q = query(q, limit(options.limit || 100));
    
    const snapshot = await getDocs(q);
    const logs = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      date: doc.data().date?.toDate(),
      created_at: doc.data().created_at?.toDate()
    }));
    
    return { logs, error: null };
  } catch (error) {
    console.error('Get weight history error:', error);
    return { logs: [], error: { message: error.message } };
  }
}

/**
 * Get the most recent weight entry
 * @param {string} userId 
 * @returns {Promise<{log: object|null, error: object|null}>}
 */
export async function getLatestWeight(userId) {
  try {
    const q = query(
      collection(db, COLLECTIONS.WEIGHT_LOGS),
      where('user_id', '==', userId),
      orderBy('date', 'desc'),
      limit(1)
    );
    
    const snapshot = await getDocs(q);
    if (snapshot.empty) return { log: null, error: null };
    
    const doc = snapshot.docs[0];
    return {
      log: {
        id: doc.id,
        ...doc.data(),
        date: doc.data().date?.toDate(),
        created_at: doc.data().created_at?.toDate()
      },
      error: null
    };
  } catch (error) {
    console.error('Get latest weight error:', error);
    return { log: null, error: { message: error.message } };
  }
}

/**
 * Update a weight log entry
 * @param {string} logId 
 * @param {object} data - Fields to update
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function updateWeight(logId, data) {
  try {
    const logRef = doc(db, COLLECTIONS.WEIGHT_LOGS, logId);
    const updateData = { ...data };
    if (data.date) updateData.date = Timestamp.fromDate(data.date);
    
    await updateDoc(logRef, updateData);
    return { success: true, error: null };
  } catch (error) {
    console.error('Update weight error:', error);
    return { success: false, error: { message: error.message } };
  }
}

/**
 * Delete a weight log entry
 * @param {string} logId 
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function deleteWeight(logId) {
  try {
    await deleteDoc(doc(db, COLLECTIONS.WEIGHT_LOGS, logId));
    return { success: true, error: null };
  } catch (error) {
    console.error('Delete weight error:', error);
    return { success: false, error: { message: error.message } };
  }
}

// ============================================================================
// WORKOUT API
// ============================================================================

/**
 * Save a workout
 * @param {string} userId 
 * @param {object} workout - { exercises: [], volume: number, duration: number, notes: string, date: Date }
 * @returns {Promise<{id: string|null, error: object|null}>}
 */
export async function saveWorkout(userId, workout) {
  try {
    const workoutRef = doc(collection(db, COLLECTIONS.WORKOUTS));
    const data = {
      user_id: userId,
      date: Timestamp.fromDate(workout.date || new Date()),
      exercises: workout.exercises || [],
      volume: Number(workout.volume) || 0,
      duration: Number(workout.duration) || 0,
      notes: workout.notes || '',
      created_at: serverTimestamp()
    };
    
    await setDoc(workoutRef, data);
    return { id: workoutRef.id, error: null };
  } catch (error) {
    console.error('Save workout error:', error);
    return { id: null, error: { message: error.message } };
  }
}

/**
 * Get workouts for a user
 * @param {string} userId 
 * @param {object} options - { limit: number }
 * @returns {Promise<{workouts: array, error: object|null}>}
 */
export async function getWorkouts(userId, options = {}) {
  try {
    const q = query(
      collection(db, COLLECTIONS.WORKOUTS),
      where('user_id', '==', userId),
      orderBy('date', 'desc'),
      limit(options.limit || 100)
    );
    
    const snapshot = await getDocs(q);
    const workouts = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      date: doc.data().date?.toDate(),
      created_at: doc.data().created_at?.toDate()
    }));
    
    return { workouts, error: null };
  } catch (error) {
    console.error('Get workouts error:', error);
    return { workouts: [], error: { message: error.message } };
  }
}

/**
 * Delete a workout
 * @param {string} workoutId 
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function deleteWorkout(workoutId) {
  try {
    await deleteDoc(doc(db, COLLECTIONS.WORKOUTS, workoutId));
    return { success: true, error: null };
  } catch (error) {
    console.error('Delete workout error:', error);
    return { success: false, error: { message: error.message } };
  }
}

// ============================================================================
// PHOTOS API
// ============================================================================

/**
 * Upload a photo and save metadata to Firestore
 * @param {string} userId 
 * @param {File} file 
 * @param {string} type - 'front', 'side', 'back', 'progress'
 * @param {Date} date 
 * @returns {Promise<{id: string|null, url: string|null, error: object|null}>}
 */
export async function savePhoto(userId, file, type = 'progress', date = new Date()) {
  try {
    // Upload to Storage
    const fileName = `${Date.now()}_${file.name}`;
    const storageRef = ref(storage, `photos/${userId}/${type}/${fileName}`);
    
    const uploadResult = await uploadBytes(storageRef, file);
    const url = await getDownloadURL(uploadResult.ref);
    
    // Save metadata to Firestore
    const photoRef = doc(collection(db, COLLECTIONS.PHOTOS));
    const data = {
      user_id: userId,
      type: type,
      url: url,
      storage_path: uploadResult.ref.fullPath,
      file_name: file.name,
      file_size: file.size,
      content_type: file.type,
      date: Timestamp.fromDate(date),
      created_at: serverTimestamp()
    };
    
    await setDoc(photoRef, data);
    return { id: photoRef.id, url, error: null };
  } catch (error) {
    console.error('Save photo error:', error);
    return { id: null, url: null, error: { message: error.message } };
  }
}

/**
 * Upload photo with progress callback
 * @param {string} userId 
 * @param {File} file 
 * @param {string} type 
 * @param {function} onProgress - Called with progress percentage
 * @param {Date} date 
 * @returns {Promise<{id: string|null, url: string|null, error: object|null}>}
 */
export async function uploadPhotoWithProgress(userId, file, type, onProgress, date = new Date()) {
  try {
    const fileName = `${Date.now()}_${file.name}`;
    const storageRef = ref(storage, `photos/${userId}/${type}/${fileName}`);
    const uploadTask = uploadBytesResumable(storageRef, file);
    
    return new Promise((resolve, reject) => {
      uploadTask.on(
        'state_changed',
        (snapshot) => {
          const progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
          if (onProgress) onProgress(progress);
        },
        (error) => reject({ id: null, url: null, error: { message: error.message } }),
        async () => {
          const url = await getDownloadURL(uploadTask.snapshot.ref);
          const photoRef = doc(collection(db, COLLECTIONS.PHOTOS));
          const data = {
            user_id: userId,
            type: type,
            url: url,
            storage_path: uploadTask.snapshot.ref.fullPath,
            file_name: file.name,
            file_size: file.size,
            content_type: file.type,
            date: Timestamp.fromDate(date),
            created_at: serverTimestamp()
          };
          await setDoc(photoRef, data);
          resolve({ id: photoRef.id, url, error: null });
        }
      );
    });
  } catch (error) {
    return { id: null, url: null, error: { message: error.message } };
  }
}

/**
 * Get photos for a user
 * @param {string} userId 
 * @param {object} options - { type: string, limit: number }
 * @returns {Promise<{photos: array, error: object|null}>}
 */
export async function getPhotos(userId, options = {}) {
  try {
    let q = query(
      collection(db, COLLECTIONS.PHOTOS),
      where('user_id', '==', userId),
      orderBy('date', 'desc')
    );
    
    if (options.type) {
      q = query(q, where('type', '==', options.type));
    }
    q = query(q, limit(options.limit || 100));
    
    const snapshot = await getDocs(q);
    const photos = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      date: doc.data().date?.toDate(),
      created_at: doc.data().created_at?.toDate()
    }));
    
    return { photos, error: null };
  } catch (error) {
    console.error('Get photos error:', error);
    return { photos: [], error: { message: error.message } };
  }
}

/**
 * Delete a photo (from Storage and Firestore)
 * @param {string} photoId 
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function deletePhoto(photoId) {
  try {
    // Get photo data
    const photoRef = doc(db, COLLECTIONS.PHOTOS, photoId);
    const snapshot = await getDoc(photoRef);
    
    if (!snapshot.exists()) {
      return { success: false, error: { message: 'Photo not found' } };
    }
    
    const photoData = snapshot.data();
    
    // Delete from Storage
    if (photoData.storage_path) {
      await deleteObject(ref(storage, photoData.storage_path));
    }
    
    // Delete from Firestore
    await deleteDoc(photoRef);
    return { success: true, error: null };
  } catch (error) {
    console.error('Delete photo error:', error);
    return { success: false, error: { message: error.message } };
  }
}

// ============================================================================
// AVATAR STATE API
// ============================================================================

/**
 * Get avatar state for current user
 * @param {string} userId 
 * @returns {Promise<{state: object, error: object|null}>}
 */
export async function getAvatarState(userId) {
  try {
    const avatarRef = doc(db, COLLECTIONS.AVATAR_STATE, userId);
    const snapshot = await getDoc(avatarRef);
    
    if (!snapshot.exists()) {
      return {
        state: {
          current_params: {
            muscle_mass: 0,
            body_fat: 20,
            fitness_level: 'beginner'
          },
          target_params: {
            muscle_mass: 0,
            body_fat: 15,
            fitness_level: 'intermediate'
          }
        },
        error: null
      };
    }
    
    return { state: { id: snapshot.id, ...snapshot.data() }, error: null };
  } catch (error) {
    console.error('Get avatar state error:', error);
    return { state: null, error: { message: error.message } };
  }
}

/**
 * Update avatar current parameters
 * @param {string} userId 
 * @param {object} params - { muscle_mass, body_fat, fitness_level }
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function updateAvatarParams(userId, params) {
  try {
    const avatarRef = doc(db, COLLECTIONS.AVATAR_STATE, userId);
    await setDoc(avatarRef, {
      user_id: userId,
      current_params: params,
      updated_at: serverTimestamp()
    }, { merge: true });
    
    return { success: true, error: null };
  } catch (error) {
    console.error('Update avatar params error:', error);
    return { success: false, error: { message: error.message } };
  }
}

// ============================================================================
// USER PROFILE API
// ============================================================================

/**
 * Get user profile
 * @param {string} userId 
 * @returns {Promise<{profile: object|null, error: object|null}>}
 */
export async function getUserProfile(userId) {
  try {
    const userRef = doc(db, COLLECTIONS.USERS, userId);
    const snapshot = await getDoc(userRef);
    
    if (!snapshot.exists()) {
      return { profile: null, error: null };
    }
    
    return { profile: { id: snapshot.id, ...snapshot.data() }, error: null };
  } catch (error) {
    console.error('Get profile error:', error);
    return { profile: null, error: { message: error.message } };
  }
}

/**
 * Update user profile
 * @param {string} userId 
 * @param {object} data 
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function updateUserProfile(userId, data) {
  try {
    const userRef = doc(db, COLLECTIONS.USERS, userId);
    await updateDoc(userRef, { ...data, updatedAt: serverTimestamp() });
    return { success: true, error: null };
  } catch (error) {
    console.error('Update profile error:', error);
    return { success: false, error: { message: error.message } };
  }
}

// ============================================================================
// AVATAR PERSISTENCE API - Mesh & Stats Storage
// ============================================================================

/**
 * Save complete avatar data to Firestore
 * @param {string} userId 
 * @param {object} avatarData - { mesh_data, stats, measurements, created_from }
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function saveAvatar(userId, avatarData) {
  try {
    const avatarRef = doc(db, COLLECTIONS.USERS, userId, 'avatar', 'current');
    const data = {
      user_id: userId,
      mesh_data: avatarData.mesh_data || null,
      stats: avatarData.stats || {},
      measurements: avatarData.measurements || {},
      created_from: avatarData.created_from || null,
      updated_at: serverTimestamp(),
      created_at: serverTimestamp()
    };
    
    await setDoc(avatarRef, data, { merge: true });
    
    // Also cache to localStorage for fast loading
    try {
      localStorage.setItem(`avatar_cache_${userId}`, JSON.stringify({
        ...data,
        cached_at: Date.now()
      }));
    } catch (e) {
      console.warn('Failed to cache avatar locally:', e);
    }
    
    return { success: true, error: null };
  } catch (error) {
    console.error('Save avatar error:', error);
    return { success: false, error: { message: error.message } };
  }
}

/**
 * Get saved avatar data for user
 * @param {string} userId 
 * @param {object} options - { useCache: boolean }
 * @returns {Promise<{avatar: object|null, fromCache: boolean, error: object|null}>}
 */
export async function getAvatar(userId, options = {}) {
  const { useCache = true } = options;
  
  // Try cache first for fast loading
  if (useCache) {
    try {
      const cached = localStorage.getItem(`avatar_cache_${userId}`);
      if (cached) {
        const parsed = JSON.parse(cached);
        const cacheAge = Date.now() - (parsed.cached_at || 0);
        // Use cache if less than 24 hours old
        if (cacheAge < 24 * 60 * 60 * 1000) {
          console.log('[Avatar] Loaded from cache');
          return { avatar: parsed, fromCache: true, error: null };
        }
      }
    } catch (e) {
      console.warn('Failed to load avatar from cache:', e);
    }
  }
  
  // Fetch from Firestore
  try {
    const avatarRef = doc(db, COLLECTIONS.USERS, userId, 'avatar', 'current');
    const snapshot = await getDoc(avatarRef);
    
    if (!snapshot.exists()) {
      return { avatar: null, fromCache: false, error: null };
    }
    
    const avatarData = { id: snapshot.id, ...snapshot.data() };
    
    // Update cache
    try {
      localStorage.setItem(`avatar_cache_${userId}`, JSON.stringify({
        ...avatarData,
        cached_at: Date.now()
      }));
    } catch (e) {
      console.warn('Failed to cache avatar:', e);
    }
    
    return { avatar: avatarData, fromCache: false, error: null };
  } catch (error) {
    console.error('Get avatar error:', error);
    
    // Try to return stale cache on error
    if (useCache) {
      try {
        const cached = localStorage.getItem(`avatar_cache_${userId}`);
        if (cached) {
          console.log('[Avatar] Using stale cache due to error');
          return { avatar: JSON.parse(cached), fromCache: true, error: null };
        }
      } catch (e) {
        // Ignore
      }
    }
    
    return { avatar: null, fromCache: false, error: { message: error.message } };
  }
}

/**
 * Check if user has a saved avatar
 * @param {string} userId 
 * @returns {Promise<{hasAvatar: boolean, error: object|null}>}
 */
export async function hasAvatar(userId) {
  try {
    // Check local cache first
    const cached = localStorage.getItem(`avatar_cache_${userId}`);
    if (cached) {
      const parsed = JSON.parse(cached);
      if (parsed.mesh_data || parsed.stats) {
        return { hasAvatar: true, error: null };
      }
    }
    
    // Check Firestore
    const avatarRef = doc(db, COLLECTIONS.USERS, userId, 'avatar', 'current');
    const snapshot = await getDoc(avatarRef);
    
    return { hasAvatar: snapshot.exists(), error: null };
  } catch (error) {
    console.error('Has avatar check error:', error);
    return { hasAvatar: false, error: { message: error.message } };
  }
}

/**
 * Save avatar generation input (photo reference)
 * @param {string} userId 
 * @param {string} photoUrl - URL of the source photo
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function saveAvatarSource(userId, photoUrl) {
  try {
    const avatarRef = doc(db, COLLECTIONS.USERS, userId, 'avatar', 'source');
    await setDoc(avatarRef, {
      user_id: userId,
      photo_url: photoUrl,
      created_at: serverTimestamp()
    });
    
    return { success: true, error: null };
  } catch (error) {
    console.error('Save avatar source error:', error);
    return { success: false, error: { message: error.message } };
  }
}

/**
 * Clear avatar data (for logout or reset)
 * @param {string} userId 
 * @returns {Promise<{success: boolean, error: object|null}>}
 */
export async function clearAvatarCache(userId) {
  try {
    localStorage.removeItem(`avatar_cache_${userId}`);
    return { success: true, error: null };
  } catch (error) {
    return { success: false, error: { message: error.message } };
  }
}

/**
 * Get user's body stats history
 * @param {string} userId 
 * @returns {Promise<{stats: array, error: object|null}>}
 */
export async function getBodyStatsHistory(userId) {
  try {
    const statsRef = collection(db, COLLECTIONS.USERS, userId, 'body_stats');
    const q = query(statsRef, orderBy('date', 'desc'), limit(100));
    const snapshot = await getDocs(q);
    
    const stats = snapshot.docs.map(doc => ({
      id: doc.id,
      ...doc.data(),
      date: doc.data().date?.toDate()
    }));
    
    return { stats, error: null };
  } catch (error) {
    console.error('Get body stats error:', error);
    return { stats: [], error: { message: error.message } };
  }
}

/**
 * Save body stats entry
 * @param {string} userId 
 * @param {object} stats - { weight, height, body_fat, muscle_mass, measurements: {} }
 * @returns {Promise<{id: string, success: boolean, error: object|null}>}
 */
export async function saveBodyStats(userId, stats) {
  try {
    const statsRef = collection(db, COLLECTIONS.USERS, userId, 'body_stats');
    const data = {
      user_id: userId,
      weight: stats.weight || null,
      height: stats.height || null,
      body_fat: stats.body_fat || null,
      muscle_mass: stats.muscle_mass || null,
      measurements: stats.measurements || {},
      date: Timestamp.fromDate(stats.date || new Date()),
      created_at: serverTimestamp()
    };
    
    const docRef = doc(statsRef);
    await setDoc(docRef, data);
    
    // Also update current avatar stats
    await saveAvatar(userId, { stats: data });
    
    return { id: docRef.id, success: true, error: null };
  } catch (error) {
    console.error('Save body stats error:', error);
    return { id: null, success: false, error: { message: error.message } };
  }
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

function formatAuthError(error) {
  const errorMessages = {
    'auth/invalid-email': 'Invalid email address format.',
    'auth/user-disabled': 'This account has been disabled.',
    'auth/user-not-found': 'No account found with this email.',
    'auth/wrong-password': 'Incorrect password.',
    'auth/email-already-in-use': 'An account with this email already exists.',
    'auth/weak-password': 'Password should be at least 6 characters.',
    'auth/invalid-credential': 'Invalid email or password.',
    'auth/popup-closed-by-user': 'Sign-in popup was closed before completing.',
    'auth/cancelled-popup-request': 'Sign-in popup was cancelled.',
    'auth/popup-blocked': 'Sign-in popup was blocked by the browser.',
    'auth/requires-recent-login': 'Please sign in again to complete this action.'
  };
  
  return {
    code: error.code,
    message: errorMessages[error.code] || error.message || 'An unknown error occurred.'
  };
}

// ============================================================================
// EXPORTS
// ============================================================================

export {
  app,
  auth,
  db,
  storage,
  COLLECTIONS,
  Timestamp,
  serverTimestamp,
  sendEmailVerification
};

// Default export with all APIs
export default {
  // Auth
  signUpWithEmail,
  signInWithEmail,
  signInWithGoogle,
  signOutUser,
  resetPassword,
  sendEmailVerification,
  onAuthChange,
  getCurrentUser,
  getCurrentUserId,
  
  // Weight
  saveWeight,
  getWeightHistory,
  getLatestWeight,
  updateWeight,
  deleteWeight,
  
  // Workouts
  saveWorkout,
  getWorkouts,
  deleteWorkout,
  
  // Photos
  savePhoto,
  uploadPhotoWithProgress,
  getPhotos,
  deletePhoto,
  
  // Avatar State
  getAvatarState,
  updateAvatarParams,
  
  // Avatar Persistence (NEW)
  saveAvatar,
  getAvatar,
  hasAvatar,
  saveAvatarSource,
  clearAvatarCache,
  getBodyStatsHistory,
  saveBodyStats,
  
  // User
  getUserProfile,
  updateUserProfile,
  
  // Firebase instances
  app,
  auth,
  db,
  storage
};