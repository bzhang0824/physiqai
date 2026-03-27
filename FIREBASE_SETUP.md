# PhysiqAI - Firebase Backend Integration

Complete Firebase backend setup for PhysiqAI fitness tracking app.

## 📁 Files Delivered

### 1. `firestore.rules`
Security rules for Firestore database ensuring users only access their own data.

### 2. `app/firebase-api.js`
Complete API wrapper with all Firebase functions:
- **Authentication**: Email/password + Google Sign-In
- **Weight API**: `saveWeight()`, `getWeightHistory()`, `getLatestWeight()`
- **Workout API**: `saveWorkout()`, `getWorkouts()`
- **Photos API**: `savePhoto()`, `getPhotos()`, `uploadPhotoWithProgress()`
- **Avatar API**: `getAvatarState()`, `updateAvatarParams()`

### 3. `app/firebase-integration.js`
Drop-in replacement for localStorage-based integration:
- Seamlessly syncs with Firebase when online
- Falls back to localStorage when offline
- Maintains existing event bus architecture

### 4. `app/auth-firebase.html`
Updated authentication page with:
- Email/password sign up and sign in
- Google Sign-In
- Form validation
- Loading states
- Error handling

### 5. `app/dashboard-weight-firebase.js`
Updated weight dashboard that loads from Firebase:
- Calculates streaks from cloud data
- Syncs weight entries to Firebase
- Maintains local fallback

---

## 🔥 Firebase Setup Instructions

### Step 1: Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Create a project"
3. Enter project name (e.g., "physiqai-app")
4. Enable Google Analytics (optional)
5. Create the project

### Step 2: Register Your App
1. Click the web icon (</>) to add a web app
2. Register app with nickname "PhysiqAI"
3. Copy the Firebase configuration object

### Step 3: Update Configuration
Replace the placeholder config in `auth-firebase.html`:

```javascript
window.firebaseConfig = {
    apiKey: "YOUR_ACTUAL_API_KEY",
    authDomain: "your-project-id.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project-id.appspot.com",
    messagingSenderId: "123456789",
    appId: "1:123456789:web:abc123..."
};
```

### Step 4: Enable Authentication
1. In Firebase Console, go to **Authentication** > **Get Started**
2. Enable **Email/Password** provider
3. Enable **Google** provider (add support email)

### Step 5: Create Firestore Database
1. Go to **Firestore Database** > **Create Database**
2. Choose **Start in production mode**
3. Select region closest to your users
4. Deploy the security rules from `firestore.rules`

### Step 6: Enable Storage
1. Go to **Storage** > **Get Started**
2. Choose **Start in production mode**
3. Update Storage rules to match security requirements

---

## 📊 Firestore Database Schema

```
users/{uid}
├── email: string
├── displayName: string
├── photoURL: string
├── createdAt: timestamp
└── updatedAt: timestamp

weight_logs/{logId}
├── user_id: string (reference to users/{uid})
├── weight: number
├── date: timestamp
├── notes: string
└── created_at: timestamp

workouts/{workoutId}
├── user_id: string
├── date: timestamp
├── exercises: array
├── volume: number
├── duration: number
├── notes: string
└── created_at: timestamp

photos/{photoId}
├── user_id: string
├── type: string ('front', 'side', 'back', 'progress')
├── url: string (download URL)
├── storage_path: string
├── file_name: string
├── file_size: number
├── content_type: string
├── date: timestamp
└── created_at: timestamp

avatar_state/{uid}
├── user_id: string
├── current_params: map
│   ├── muscle_mass: number
│   ├── body_fat: number
│   └── fitness_level: string
├── target_params: map
└── updated_at: timestamp
```

---

## 🔒 Security Rules Summary

The `firestore.rules` file enforces:

1. **Authentication Required**: All reads/writes require signed-in user
2. **User Isolation**: Users can only access documents where `user_id == auth.uid`
3. **Data Validation**: Validates required fields for each collection
4. **Document Ownership**: Users can only modify their own documents

---

## 📱 Usage Examples

### Initialize and Use in Your App

```html
<!-- Add to your HTML -->
<script type="module">
    import { 
        signInWithEmail, 
        saveWeight, 
        getWeightHistory 
    } from './firebase-api.js';
    
    // Sign in
    const result = await signInWithEmail('user@example.com', 'password');
    
    // Save weight
    await saveWeight(result.user.uid, 175.5, new Date(), 'Morning weigh-in');
    
    // Get history
    const { logs } = await getWeightHistory(result.user.uid, { limit: 30 });
</script>
```

### Using the Integration Layer (Drop-in Replacement)

```html
<!-- Replace integration.js with firebase-integration.js -->
<script type="module" src="firebase-integration.js"></script>

<script>
    // This now syncs to Firebase automatically!
    firebaseIntegration.logWeight(175.5, '2025-02-24', 'Notes');
    
    // Get data (from Firebase or localStorage fallback)
    const data = await firebaseIntegration.store.getWeightData();
</script>
```

---

## 🔄 Migration Guide

### From localStorage to Firebase

1. **Replace auth page**:
   ```bash
   mv app/auth-firebase.html app/auth.html
   ```

2. **Update dashboard**:
   ```html
   <!-- In dashboard.html -->
   <script type="module" src="dashboard-weight-firebase.js"></script>
   ```

3. **Add Firebase integration**:
   ```html
   <!-- Add to index.html and other pages -->
   <script type="module" src="firebase-integration.js"></script>
   ```

4. **Update your config**:
   Add your Firebase config to all pages that use auth:
   ```javascript
   window.firebaseConfig = { /* your config */ };
   ```

---

## 📦 API Reference

### Authentication

| Function | Description |
|----------|-------------|
| `signUpWithEmail(email, password, profile)` | Create new account |
| `signInWithEmail(email, password)` | Sign in existing user |
| `signInWithGoogle()` | Sign in with Google |
| `signOutUser()` | Sign out current user |
| `onAuthChange(callback)` | Listen for auth state changes |

### Weight Tracking

| Function | Description |
|----------|-------------|
| `saveWeight(userId, weight, date, notes)` | Log a weight entry |
| `getWeightHistory(userId, options)` | Get user's weight history |
| `getLatestWeight(userId)` | Get most recent entry |
| `updateWeight(logId, data)` | Update existing entry |
| `deleteWeight(logId)` | Delete a weight entry |

### Workouts

| Function | Description |
|----------|-------------|
| `saveWorkout(userId, workout)` | Log a workout |
| `getWorkouts(userId, options)` | Get workout history |
| `deleteWorkout(workoutId)` | Delete a workout |

### Photos

| Function | Description |
|----------|-------------|
| `savePhoto(userId, file, type, date)` | Upload and save photo |
| `getPhotos(userId, options)` | Get user's photos |
| `deletePhoto(photoId)` | Delete photo from Storage & DB |
| `uploadPhotoWithProgress(userId, file, type, onProgress)` | Upload with progress callback |

---

## 🛠️ Testing

### Local Testing
1. Set up Firebase emulators:
   ```bash
   npm install -g firebase-tools
   firebase init emulators
   firebase emulators:start
   ```

2. Update `firebase-api.js` to use emulator:
   ```javascript
   connectAuthEmulator(auth, 'http://localhost:9099');
   connectFirestoreEmulator(db, 'localhost', 8080);
   connectStorageEmulator(storage, 'localhost', 9199);
   ```

---

## 🚨 Troubleshooting

### CORS Errors
Configure CORS for Firebase Storage:
```bash
gsutil cors set cors.json gs://your-bucket
```

### Auth Domain Not Authorized
Add your domain to Firebase Console > Authentication > Settings > Authorized domains

### Offline Support Not Working
Ensure IndexedDB is enabled in browser and persistence is initialized.

---

## 📄 License

Part of PhysiqAI project.

## 🙋 Support

For issues or questions, check:
- [Firebase Documentation](https://firebase.google.com/docs)
- Firestore rules validation in Firebase Console
- Browser console for detailed error messages