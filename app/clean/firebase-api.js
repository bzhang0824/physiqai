/**
 * Firebase API Integration for PhysiqAI
 * Handles mesh storage and retrieval from Firebase
 */

// Firebase configuration - will be loaded from config
let firebaseConfig = null;
let firebaseApp = null;
let firestore = null;
let storage = null;

/**
 * Initialize Firebase
 */
async function initFirebase(config) {
  if (firebaseApp) return firebaseApp;
  
  firebaseConfig = config || window.FIREBASE_CONFIG || FIREBASE_CONFIG;
  
  // Check if Firebase is available
  if (typeof firebase === 'undefined') {
    console.warn('[Firebase] Firebase SDK not loaded');
    return null;
  }
  
  // Check if Firebase is already initialized (from inline script)
  if (firebase.apps.length > 0) {
    firebaseApp = firebase.apps[0];
    firestore = firebase.firestore();
    storage = firebase.storage();
    console.log('[Firebase] Using existing initialized app');
    return firebaseApp;
  }
  
  try {
    firebaseApp = firebase.initializeApp(firebaseConfig);
    firestore = firebase.firestore();
    storage = firebase.storage();
    console.log('[Firebase] Initialized successfully');
    return firebaseApp;
  } catch (error) {
    console.error('[Firebase] Initialization failed:', error);
    return null;
  }
}

/**
 * Firebase configuration for PhysiqAI
 */
const FIREBASE_CONFIG = {
  apiKey: "AIzaSyDQnKtxk_uCiW7owBCSf6ABKE2b5QKdqiU",
  authDomain: "physique-ai-217b0.firebaseapp.com",
  projectId: "physique-ai-217b0",
  storageBucket: "physique-ai-217b0.appspot.com",
  messagingSenderId: "217012345678",
  appId: "1:217012345678:web:abc123def456"
};

/**
 * Load Firebase config from server
 */
async function loadFirebaseConfig() {
  // Return hardcoded config immediately
  return FIREBASE_CONFIG;
}

/**
 * Save mesh to Firebase Storage and metadata to Firestore
 */
async function saveMeshToFirebase(userId, photoId, meshData, metadata = {}) {
  if (!firebaseApp) {
    await initFirebase();
  }
  
  if (!firebaseApp) {
    console.warn('[Firebase] Not initialized, saving locally only');
    saveMeshLocally(userId, photoId, meshData, metadata);
    return { success: false, error: 'Firebase not available', local: true };
  }
  
  try {
    // Save mesh JSON to Storage
    const meshBlob = new Blob([JSON.stringify(meshData)], { type: 'application/json' });
    const meshRef = storage.ref(`users/${userId}/meshes/${photoId}_mesh.json`);
    await meshRef.put(meshBlob);
    const meshUrl = await meshRef.getDownloadURL();
    
    // Save metadata to Firestore
    const meshDoc = {
      userId,
      photoId,
      meshUrl,
      createdAt: firebase.firestore.FieldValue.serverTimestamp(),
      ...metadata
    };
    
    await firestore.collection('users').doc(userId).collection('meshes').doc(photoId).set(meshDoc);
    
    // Update user's latest mesh reference
    await firestore.collection('users').doc(userId).set({
      latestMesh: {
        photoId,
        meshUrl,
        updatedAt: firebase.firestore.FieldValue.serverTimestamp()
      }
    }, { merge: true });
    
    console.log('[Firebase] Mesh saved successfully');
    return { success: true, meshUrl, photoId };
  } catch (error) {
    console.error('[Firebase] Save failed:', error);
    // Fallback to local storage
    saveMeshLocally(userId, photoId, meshData, metadata);
    return { success: false, error: error.message, local: true };
  }
}

/**
 * Save mesh to localStorage as fallback
 */
function saveMeshLocally(userId, photoId, meshData, metadata) {
  const key = `physiq_mesh_${userId}_${photoId}`;
  const data = {
    meshData,
    metadata,
    savedAt: Date.now()
  };
  localStorage.setItem(key, JSON.stringify(data));
  localStorage.setItem('physiq_latest_mesh', JSON.stringify({
    userId,
    photoId,
    timestamp: Date.now(),
    ...metadata
  }));
  console.log('[Firebase] Mesh saved locally');
}

/**
 * Load mesh from Firebase or local storage
 */
async function loadMeshFromFirebase(userId, photoId = null) {
  if (!firebaseApp) {
    await initFirebase();
  }
  
  // Try localStorage first for speed
  const latestLocal = localStorage.getItem('physiq_latest_mesh');
  if (latestLocal) {
    const parsed = JSON.parse(latestLocal);
    if (parsed.userId === userId) {
      console.log('[Firebase] Using cached mesh from localStorage');
      return { success: true, ...parsed, fromCache: true };
    }
  }
  
  if (!firebaseApp) {
    return { success: false, error: 'Firebase not available' };
  }
  
  try {
    let meshDoc;
    
    if (photoId) {
      // Get specific mesh
      const doc = await firestore.collection('users').doc(userId).collection('meshes').doc(photoId).get();
      if (!doc.exists) {
        return { success: false, error: 'Mesh not found' };
      }
      meshDoc = doc.data();
    } else {
      // Get latest mesh
      const userDoc = await firestore.collection('users').doc(userId).get();
      if (!userDoc.exists || !userDoc.data().latestMesh) {
        return { success: false, error: 'No mesh found for user' };
      }
      meshDoc = userDoc.data().latestMesh;
    }
    
    // Cache in localStorage
    localStorage.setItem('physiq_latest_mesh', JSON.stringify({
      userId,
      photoId: meshDoc.photoId,
      meshUrl: meshDoc.meshUrl,
      timestamp: Date.now(),
      detection: meshDoc.detection,
      smplParams: meshDoc.smplParams
    }));
    
    return { success: true, ...meshDoc };
  } catch (error) {
    console.error('[Firebase] Load failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Check if user has a personalized mesh
 */
async function hasPersonalizedMesh(userId) {
  // Check localStorage first
  const latest = localStorage.getItem('physiq_latest_mesh');
  if (latest) {
    const parsed = JSON.parse(latest);
    if (parsed.userId === userId && Date.now() - parsed.timestamp < 24 * 60 * 60 * 1000) {
      return true;
    }
  }
  
  if (!firebaseApp) return false;
  
  try {
    const userDoc = await firestore.collection('users').doc(userId).get();
    return userDoc.exists && userDoc.data().latestMesh;
  } catch (error) {
    return false;
  }
}

/**
 * Delete mesh from Firebase
 */
async function deleteMeshFromFirebase(userId, photoId) {
  if (!firebaseApp) {
    return { success: false, error: 'Firebase not initialized' };
  }
  
  try {
    // Delete from Storage
    const meshRef = storage.ref(`users/${userId}/meshes/${photoId}_mesh.json`);
    await meshRef.delete();
    
    // Delete from Firestore
    await firestore.collection('users').doc(userId).collection('meshes').doc(photoId).delete();
    
    // Clear localStorage if this was the latest
    const latest = localStorage.getItem('physiq_latest_mesh');
    if (latest) {
      const parsed = JSON.parse(latest);
      if (parsed.photoId === photoId) {
        localStorage.removeItem('physiq_latest_mesh');
      }
    }
    
    return { success: true };
  } catch (error) {
    console.error('[Firebase] Delete failed:', error);
    return { success: false, error: error.message };
  }
}

/**
 * ==================== AUTHENTICATION FUNCTIONS ====================
 */

let auth = null;
let currentUser = null;
let authStateListeners = [];

/**
 * Initialize Firebase Auth
 */
async function initAuth() {
  if (auth) return auth;
  
  if (!firebaseApp) {
    await initFirebase();
  }
  
  if (firebaseApp) {
    auth = firebase.auth();
    // Set up auth state listener
    auth.onAuthStateChanged((user) => {
      currentUser = user;
      authStateListeners.forEach(callback => callback(user));
    });
    console.log('[Auth] Initialized with domain:', auth.config?.authDomain || 'default');
  }
  return auth;
}

/**
 * Sign in with email and password
 */
async function signInWithEmail(email, password, rememberMe = false) {
  await initAuth();
  if (!auth) {
    return { error: { message: 'Firebase Auth not available' } };
  }
  
  try {
    // Set persistence based on rememberMe
    const persistence = rememberMe 
      ? firebase.auth.Auth.Persistence.LOCAL 
      : firebase.auth.Auth.Persistence.SESSION;
    await auth.setPersistence(persistence);
    
    const result = await auth.signInWithEmailAndPassword(email, password);
    return { user: result.user };
  } catch (error) {
    console.error('[Auth] Sign in failed:', error);
    return { error: { message: getAuthErrorMessage(error.code) } };
  }
}

/**
 * Sign up with email and password
 */
async function signUpWithEmail(email, password, profile = {}) {
  await initAuth();
  if (!auth) {
    return { error: { message: 'Firebase Auth not available' } };
  }
  
  try {
    const result = await auth.createUserWithEmailAndPassword(email, password);
    
    // Update profile
    if (profile.displayName) {
      await result.user.updateProfile({ displayName: profile.displayName });
    }
    
    // Send email verification
    await result.user.sendEmailVerification();
    
    return { user: result.user };
  } catch (error) {
    console.error('[Auth] Sign up failed:', error);
    return { error: { message: getAuthErrorMessage(error.code) } };
  }
}

/**
 * Sign in with Google
 */
async function signInWithGoogle(rememberMe = false) {
  await initAuth();
  if (!auth) {
    return { error: { message: 'Firebase Auth not available' } };
  }
  
  try {
    const provider = new firebase.auth.GoogleAuthProvider();
    provider.addScope('email');
    provider.addScope('profile');
    
    // Set persistence
    const persistence = rememberMe 
      ? firebase.auth.Auth.Persistence.LOCAL 
      : firebase.auth.Auth.Persistence.SESSION;
    await auth.setPersistence(persistence);
    
    const result = await auth.signInWithPopup(provider);
    return { user: result.user, isNewUser: result.additionalUserInfo?.isNewUser || false };
  } catch (error) {
    console.error('[Auth] Google sign in failed:', error);
    return { error: { message: getAuthErrorMessage(error.code) } };
  }
}

/**
 * Sign out
 */
async function signOutUser() {
  await initAuth();
  if (!auth) return { error: { message: 'Firebase Auth not available' } };
  
  try {
    await auth.signOut();
    // Clear local storage
    localStorage.removeItem('rememberMe');
    localStorage.removeItem('userId');
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userName');
    localStorage.removeItem('userPhoto');
    localStorage.removeItem('physiq_latest_mesh');
    return { success: true };
  } catch (error) {
    console.error('[Auth] Sign out failed:', error);
    return { error: { message: error.message } };
  }
}

/**
 * Reset password
 */
async function resetPassword(email) {
  await initAuth();
  if (!auth) {
    return { error: { message: 'Firebase Auth not available' } };
  }
  
  try {
    await auth.sendPasswordResetEmail(email);
    return { success: true };
  } catch (error) {
    console.error('[Auth] Password reset failed:', error);
    return { error: { message: getAuthErrorMessage(error.code) } };
  }
}

/**
 * Send email verification
 */
async function sendEmailVerification(user) {
  if (!user) {
    return { error: { message: 'No user provided' } };
  }
  
  try {
    await user.sendEmailVerification();
    return { success: true };
  } catch (error) {
    console.error('[Auth] Send verification failed:', error);
    return { error: { message: error.message } };
  }
}

/**
 * Check for admin/demo session in localStorage
 */
function getAdminSession() {
  const userId = localStorage.getItem('userId');
  const isAdmin = localStorage.getItem('isAdmin') === 'true';
  const isDemo = localStorage.getItem('isDemo') === 'true';
  
  console.log('[Auth] Checking admin session:', { userId, isAdmin, isDemo });
  
  if (userId && (isAdmin || isDemo)) {
    console.log('[Auth] Admin/demo session found!');
    return {
      uid: userId,
      email: localStorage.getItem('userEmail') || 'admin@physiqai.com',
      displayName: localStorage.getItem('userName') || (isAdmin ? 'BZ Admin' : 'Demo User'),
      photoURL: localStorage.getItem('userPhoto') || null,
      emailVerified: true,
      isAdmin: isAdmin,
      isDemo: isDemo
    };
  }
  console.log('[Auth] No admin session found');
  return null;
}

/**
 * Listen for auth state changes
 */
function onAuthChange(callback) {
  authStateListeners.push(callback);
  
  // Check for admin/demo session first
  const adminSession = getAdminSession();
  if (adminSession) {
    console.log('[Auth] Using admin/demo session:', adminSession.displayName);
    callback(adminSession);
    return () => {
      const index = authStateListeners.indexOf(callback);
      if (index > -1) {
        authStateListeners.splice(index, 1);
      }
    };
  }
  
  // If auth already initialized and we have a user, call immediately
  if (auth && currentUser !== undefined) {
    callback(currentUser);
  } else if (!auth) {
    // Initialize auth and then call
    initAuth().then(() => {
      callback(currentUser);
    });
  }
  
  // Return unsubscribe function
  return () => {
    const index = authStateListeners.indexOf(callback);
    if (index > -1) {
      authStateListeners.splice(index, 1);
    }
  };
}

/**
 * Get current user
 */
function getCurrentUser() {
  // Check for admin/demo session first
  const adminSession = getAdminSession();
  if (adminSession) {
    return adminSession;
  }
  return currentUser || auth?.currentUser;
}

/**
 * Convert Firebase auth error codes to user-friendly messages
 */
function getAuthErrorMessage(code) {
  const messages = {
    'auth/invalid-email': 'Invalid email address',
    'auth/user-disabled': 'This account has been disabled',
    'auth/user-not-found': 'No account found with this email',
    'auth/wrong-password': 'Incorrect password',
    'auth/email-already-in-use': 'An account already exists with this email',
    'auth/weak-password': 'Password is too weak',
    'auth/invalid-credential': 'Invalid email or password',
    'auth/popup-closed-by-user': 'Sign in was cancelled',
    'auth/popup-blocked': 'Sign in popup was blocked. Please allow popups for this site',
    'auth/account-exists-with-different-credential': 'An account already exists with the same email but different sign-in method',
    'auth/network-request-failed': 'Network error. Please check your connection',
    'auth/too-many-requests': 'Too many attempts. Please try again later',
    'auth/unauthorized-domain': 'This domain is not authorized for OAuth operations'
  };
  return messages[code] || 'An error occurred. Please try again.';
}

/**
 * ==================== AVATAR DATA FUNCTIONS ====================
 */

/**
 * Save avatar data to Firestore
 */
async function saveAvatar(userId, avatarData) {
  await initFirebase();
  if (!firebaseApp) {
    console.warn('[Firebase] Not initialized, saving locally');
    localStorage.setItem(`physiq_avatar_${userId}`, JSON.stringify(avatarData));
    return { success: false, local: true };
  }
  
  try {
    await firestore.collection('users').doc(userId).collection('avatars').add({
      ...avatarData,
      createdAt: firebase.firestore.FieldValue.serverTimestamp()
    });
    return { success: true };
  } catch (error) {
    console.error('[Firebase] Save avatar failed:', error);
    localStorage.setItem(`physiq_avatar_${userId}`, JSON.stringify(avatarData));
    return { success: false, error: error.message, local: true };
  }
}

/**
 * Get latest avatar for user
 */
async function getAvatar(userId) {
  await initFirebase();
  
  // Check localStorage first
  const localAvatar = localStorage.getItem(`physiq_avatar_${userId}`);
  if (localAvatar) {
    return { avatar: JSON.parse(localAvatar), fromCache: true };
  }
  
  if (!firebaseApp) {
    return { error: 'Firebase not available' };
  }
  
  try {
    const snapshot = await firestore.collection('users').doc(userId)
      .collection('avatars')
      .orderBy('createdAt', 'desc')
      .limit(1)
      .get();
    
    if (snapshot.empty) {
      return { avatar: null };
    }
    
    return { avatar: snapshot.docs[0].data() };
  } catch (error) {
    console.error('[Firebase] Get avatar failed:', error);
    return { error: error.message };
  }
}

/**
 * Save avatar source photo
 */
async function saveAvatarSource(userId, sourceData) {
  await initFirebase();
  if (!firebaseApp) {
    localStorage.setItem(`physiq_avatar_source_${userId}`, JSON.stringify(sourceData));
    return { success: false, local: true };
  }
  
  try {
    await firestore.collection('users').doc(userId).set({
      avatarSource: sourceData
    }, { merge: true });
    return { success: true };
  } catch (error) {
    console.error('[Firebase] Save source failed:', error);
    localStorage.setItem(`physiq_avatar_source_${userId}`, JSON.stringify(sourceData));
    return { success: false, error: error.message, local: true };
  }
}

// Export functions for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initFirebase,
    saveMeshToFirebase,
    loadMeshFromFirebase,
    hasPersonalizedMesh,
    deleteMeshFromFirebase,
    signInWithEmail,
    signUpWithEmail,
    signInWithGoogle,
    signOutUser,
    resetPassword,
    sendEmailVerification,
    onAuthChange,
    getCurrentUser,
    saveAvatar,
    getAvatar,
    saveAvatarSource
  };
}