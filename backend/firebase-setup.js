/**
 * PhysiqAI - Firebase Backend Setup
 * 
 * Complete backend infrastructure using Firebase v9 modular SDK.
 * Includes: Auth, Firestore, Storage, and API wrapper functions.
 */

// ============================================================================
// Firebase Imports (v9 Modular SDK)
// ============================================================================
import { initializeApp, getApps, getApp } from "firebase/app";
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
  updatePassword,
  deleteUser
} from "firebase/auth";
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
  writeBatch,
  enableIndexedDbPersistence
} from "firebase/firestore";
import { 
  getStorage,
  ref,
  uploadBytes,
  uploadBytesResumable,
  getDownloadURL,
  deleteObject,
  listAll
} from "firebase/storage";

// Import configuration
import firebaseConfig from "./firebase-config.js";

// ============================================================================
// Firebase Initialization
// ============================================================================

function initializeFirebase() {
  if (getApps().length === 0) {
    const app = initializeApp(firebaseConfig);
    const db = getFirestore(app);
    enableIndexedDbPersistence(db).catch((err) => {
      if (err.code === 'failed-precondition') {
        console.warn('Multiple tabs open, persistence can only be enabled in one tab at a time.');
      } else if (err.code === 'unimplemented') {
        console.warn('Browser does not support offline persistence.');
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

export { app, auth, db, storage, googleProvider };

// Collection names
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

export const AuthAPI = {
  async signUp(email, password, profile = {}) {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      
      if (profile.displayName) {
        await updateProfile(user, {
          displayName: profile.displayName,
          photoURL: profile.photoURL || null
        });
      }
      
      await UserAPI.createUserDocument(user.uid, {
        email: user.email,
        displayName: profile.displayName || email.split('@')[0],
        photoURL: profile.photoURL || null,
        createdAt: serverTimestamp(),
        updatedAt: serverTimestamp()
      });
      
      return { user, error: null };
    } catch (error) {
      console.error('Sign up error:', error);
      return { user: null, error: this._formatError(error) };
    }
  },

  async signIn(email, password) {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return { user: userCredential.user, error: null };
    } catch (error) {
      console.error('Sign in error:', error);
      return { user: null, error: this._formatError(error) };
    }
  },

  async signInWithGoogle() {
    try {
      const result = await signInWithPopup(auth, googleProvider);
      const user = result.user;
      const isNewUser = result._tokenResponse?.isNewUser || false;
      
      if (isNewUser) {
        await UserAPI.createUserDocument(user.uid, {
          email: user.email,
          displayName: user.displayName,
          photoURL: user.photoURL,
          createdAt: serverTimestamp(),
          updatedAt: serverTimestamp()
        });
      }
      
      return { user, isNewUser, error: null };
    } catch (error) {
      console.error('Google sign in error:', error);
      return { user: null, isNewUser: false, error: this._formatError(error) };
    }
  },

  async signOut() {
    try {
      await signOut(auth);
      return { success: true, error: null };
    } catch (error) {
      console.error('Sign out error:', error);
      return { success: false, error: this._formatError(error) };
    }
  },

  async resetPassword(email) {
    try {
      await sendPasswordResetEmail(auth, email);
      return { success: true, error: null };
    } catch (error) {
      console.error('Password reset error:', error);
      return { success: false, error: this._formatError(error) };
    }
  },

  async updatePassword(newPassword) {
    try {
      const user = auth.currentUser;
      if (!user) throw new Error('No user is currently signed in');
      await updatePassword(user, newPassword);
      return { success: true, error: null };
    } catch (error) {
      console.error('Update password error:', error);
      return { success: false, error: this._formatError(error) };
    }
  },

  async deleteAccount() {
    try {
      const user = auth.currentUser;
      if (!user) throw new Error('No user is currently signed in');
      await UserAPI.deleteUserData(user.uid);
      await deleteUser(user);
      return { success: true, error: null };
    } catch (error) {
      console.error('Delete account error:', error);
      return { success: false, error: this._formatError(error) };
    }
  },

  onAuthStateChanged(callback) {
    return onAuthStateChanged(auth, callback);
  },

  getCurrentUser() {
    return auth.currentUser;
  },

  _formatError(error) {
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
};

// ============================================================================
// USERS API
// ============================================================================

export const UserAPI = {
  async createUserDocument(uid, data) {
    const userRef = doc(db, COLLECTIONS.USERS, uid);
    await setDoc(userRef, data);
  },

  async getProfile(uid = null) {
    try {
      const userId = uid || auth.currentUser?.uid;
      if (!userId) throw new Error('No user ID provided');
      
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
  },

  async updateProfile(data) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const userRef = doc(db, COLLECTIONS.USERS, uid);
      await updateDoc(userRef, { ...data, updatedAt: serverTimestamp() });
      
      if (data.displayName || data.photoURL) {
        await updateProfile(auth.currentUser, {
          displayName: data.displayName || auth.currentUser.displayName,
          photoURL: data.photoURL || auth.currentUser.photoURL
        });
      }
      
      return { success: true, error: null };
    } catch (error) {
      console.error('Update profile error:', error);
      return { success: false, error: { message: error.message } };
    }
  },

  async deleteUserData(uid) {
    const batch = writeBatch(db);
    
    const weightLogsQuery = query(collection(db, COLLECTIONS.WEIGHT_LOGS), where('user_id', '==', uid));
    const weightLogsSnapshot = await getDocs(weightLogsQuery);
    weightLogsSnapshot.forEach(doc => batch.delete(doc.ref));
    
    const workoutsQuery = query(collection(db, COLLECTIONS.WORKOUTS), where('user_id', '==', uid));
    const workoutsSnapshot = await getDocs(workoutsQuery);
    workoutsSnapshot.forEach(doc => batch.delete(doc.ref));
    
    const photosQuery = query(collection(db, COLLECTIONS.PHOTOS), where('user_id', '==', uid));
    const photosSnapshot = await getDocs(photosQuery);
    photosSnapshot.forEach(doc => batch.delete(doc.ref));
    
    batch.delete(doc(db, COLLECTIONS.AVATAR_STATE, uid));
    batch.delete(doc(db, COLLECTIONS.USERS, uid));
    
    await batch.commit();
  }
};

// ============================================================================
// WEIGHT LOGS API
// ============================================================================

export const WeightAPI = {
  async logWeight(weight, date = new Date(), notes = '') {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const weightLogRef = doc(collection(db, COLLECTIONS.WEIGHT_LOGS));
      const data = {
        user_id: uid,
        weight: Number(weight),
        date: Timestamp.fromDate(date),
        notes: notes || '',
        created_at: serverTimestamp()
      };
      
      await setDoc(weightLogRef, data);
      return { id: weightLogRef.id, error: null };
    } catch (error) {
      console.error('Log weight error:', error);
      return { id: null, error: { message: error.message } };
    }
  },

  async getLogs(options = {}) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      let q = query(
        collection(db, COLLECTIONS.WEIGHT_LOGS),
        where('user_id', '==', uid),
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
      console.error('Get weight logs error:', error);
      return { logs: [], error: { message: error.message } };
    }
  },

  async getLatest() {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const q = query(
        collection(db, COLLECTIONS.WEIGHT_LOGS),
        where('user_id', '==', uid),
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
  },

  async updateLog(logId, data) {
    try {
      const logRef = doc(db, COLLECTIONS.WEIGHT_LOGS, logId);
      const updateData = { ...data };
      if (data.date) updateData.date = Timestamp.fromDate(data.date);
      
      await updateDoc(logRef, updateData);
      return { success: true, error: null };
    } catch (error) {
      console.error('Update weight log error:', error);
      return { success: false, error: { message: error.message } };
    }
  },

  async deleteLog(logId) {
    try {
      await deleteDoc(doc(db, COLLECTIONS.WEIGHT_LOGS, logId));
      return { success: true, error: null };
    } catch (error) {
      console.error('Delete weight log error:', error);
      return { success: false, error: { message: error.message } };
    }
  }
};

// ============================================================================
// WORKOUTS API
// ============================================================================

export const WorkoutAPI = {
  async logWorkout(workout) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const workoutRef = doc(collection(db, COLLECTIONS.WORKOUTS));
      const data = {
        user_id: uid,
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
      console.error('Log workout error:', error);
      return { id: null, error: { message: error.message } };
    }
  },

  async getWorkouts(options = {}) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      let q = query(
        collection(db, COLLECTIONS.WORKOUTS),
        where('user_id', '==', uid),
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
  },

  async getWorkout(workoutId) {
    try {
      const snapshot = await getDoc(doc(db, COLLECTIONS.WORKOUTS, workoutId));
      if (!snapshot.exists()) return { workout: null, error: null };
      
      return {
        workout: {
          id: snapshot.id,
          ...snapshot.data(),
          date: snapshot.data().date?.toDate(),
          created_at: snapshot.data().created_at?.toDate()
        },
        error: null
      };
    } catch (error) {
      console.error('Get workout error:', error);
      return { workout: null, error: { message: error.message } };
    }
  },

  async updateWorkout(workoutId, data) {
    try {
      const updateData = { ...data };
      if (data.date) updateData.date = Timestamp.fromDate(data.date);
      
      await updateDoc(doc(db, COLLECTIONS.WORKOUTS, workoutId), updateData);
      return { success: true, error: null };
    } catch (error) {
      console.error('Update workout error:', error);
      return { success: false, error: { message: error.message } };
    }
  },

  async deleteWorkout(workoutId) {
    try {
      await deleteDoc(doc(db, COLLECTIONS.WORKOUTS, workoutId));
      return { success: true, error: null };
    } catch (error) {
      console.error('Delete workout error:', error);
      return { success: false, error: { message: error.message } };
    }
  },

  async getStats(startDate, endDate) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const q = query(
        collection(db, COLLECTIONS.WORKOUTS),
        where('user_id', '==', uid),
        where('date', '>=', Timestamp.fromDate(startDate)),
        where('date', '<=', Timestamp.fromDate(endDate))
      );
      
      const snapshot = await getDocs(q);
      const workouts = snapshot.docs.map(doc => doc.data());
      
      const stats = {
        totalWorkouts: workouts.length,
        totalVolume: workouts.reduce((sum, w) => sum + (w.volume || 0), 0),
        totalDuration: workouts.reduce((sum, w) => sum + (w.duration || 0), 0),
        averageVolume: workouts.length > 0 ? workouts.reduce((sum, w) => sum + (w.volume || 0), 0) / workouts.length : 0
      };
      
      return { stats, error: null };
    } catch (error) {
      console.error('Get workout stats error:', error);
      return { stats: null, error: { message: error.message } };
    }
  }
};

// ============================================================================
// PHOTOS API
// ============================================================================

export const PhotosAPI = {
  async uploadPhoto(file, type = 'other', date = new Date()) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const fileName = `${Date.now()}_${file.name}`;
      const storageRef = ref(storage, `photos/${uid}/${type}/${fileName}`);
      
      const uploadResult = await uploadBytes(storageRef, file);
      const url = await getDownloadURL(uploadResult.ref);
      
      const photoRef = doc(collection(db, COLLECTIONS.PHOTOS));
      const data = {
        user_id: uid,
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
      console.error('Upload photo error:', error);
      return { id: null, url: null, error: { message: error.message } };
    }
  },

  async uploadPhotoWithProgress(file, type = 'other', onProgress, date = new Date()) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const fileName = `${Date.now()}_${file.name}`;
      const storageRef = ref(storage, `photos/${uid}/${type}/${fileName}`);
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
              user_id: uid,
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
  },

  async getPhotos(options = {}) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      let q = query(
        collection(db, COLLECTIONS.PHOTOS),
        where('user_id', '==', uid),
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
  },

  async deletePhoto(photoId) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const photoRef = doc(db, COLLECTIONS.PHOTOS, photoId);
      const snapshot = await getDoc(photoRef);
      
      if (!snapshot.exists()) {
        return { success: false, error: { message: 'Photo not found' } };
      }
      
      const photoData = snapshot.data();
      if (photoData.user_id !== uid) {
        return { success: false, error: { message: 'Unauthorized' } };
      }
      
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
};

// ============================================================================
// AVATAR STATE API
// ============================================================================

export const AvatarAPI = {
  async getAvatarState() {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const avatarRef = doc(db, COLLECTIONS.AVATAR_STATE, uid);
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
  },

  async updateCurrentParams(params) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const avatarRef = doc(db, COLLECTIONS.AVATAR_STATE, uid);
      await setDoc(avatarRef, {
        user_id: uid,
        current_params: params,
        updated_at: serverTimestamp()
      }, { merge: true });
      
      return { success: true, error: null };
    } catch (error) {
      console.error('Update current params error:', error);
      return { success: false, error: { message: error.message } };
    }
  },

  async updateTargetParams(params) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const avatarRef = doc(db, COLLECTIONS.AVATAR_STATE, uid);
      await setDoc(avatarRef, {
        user_id: uid,
        target_params: params,
        updated_at: serverTimestamp()
      }, { merge: true });
      
      return { success: true, error: null };
    } catch (error) {
      console.error('Update target params error:', error);
      return { success: false, error: { message: error.message } };
    }
  },

  async updateAvatarState(currentParams, targetParams) {
    try {
      const uid = auth.currentUser?.uid;
      if (!uid) throw new Error('No user is currently signed in');
      
      const avatarRef = doc(db, COLLECTIONS.AVATAR_STATE, uid);
      await setDoc(avatarRef, {
        user_id: uid,
        current_params: currentParams,
        target_params: targetParams,
        updated_at: serverTimestamp()
      }, { merge: true });
      
      return { success: true, error: null };
    } catch (error) {
      console.error('Update avatar state error:', error);
      return { success: false, error: { message: error.message } };
    }
  }
};

// ============================================================================
// EXPORT ALL APIs
// ============================================================================

export default {
  AuthAPI,
  UserAPI,
  WeightAPI,
  WorkoutAPI,
  PhotosAPI,
  AvatarAPI,
  app,
  auth,
  db,
  storage,
  COLLECTIONS
};
