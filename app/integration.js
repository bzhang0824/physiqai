/**
 * ========================================
 * PhysiqAI - Integration Layer
 * Event-Driven Architecture
 * ========================================
 * 
 * Connects all features:
 * 1. Weight logged → updates avatar weight display
 * 2. Workout saved → triggers body prediction
 * 3. Photo uploaded → shows in timeline
 * 4. Dashboard shows real data (not mock)
 * 5. Avatar morphs based on weight change
 * 6. Progress calculated from actual history
 * 7. Insights generated from real patterns
 */

// ========================================
// EVENT BUS - Core Communication System
// ========================================

class PhysiqEventBus {
    constructor() {
        this.events = {};
        this.history = [];
        this.maxHistory = 100;
    }

    subscribe(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
        
        return () => {
            this.events[event] = this.events[event].filter(cb => cb !== callback);
        };
    }

    emit(event, data) {
        this.history.push({ event, data, timestamp: new Date().toISOString() });
        if (this.history.length > this.maxHistory) this.history.shift();

        if (this.events[event]) {
            this.events[event].forEach(callback => {
                try { callback(data); } catch (e) { console.error(e); }
            });
        }

        if (this.events['*']) {
            this.events['*'].forEach(callback => {
                try { callback({ event, data }); } catch (e) { console.error(e); }
            });
        }
    }
}

const physiqBus = new PhysiqEventBus();

// ========================================
// DATA STORE - Centralized State
// ========================================

class PhysiqDataStore {
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
        this.hydrate();
    }

    get(key, defaultValue = null) {
        if (this.cache[key] !== undefined) return this.cache[key];
        try {
            const stored = localStorage.getItem(key);
            const data = stored ? JSON.parse(stored) : defaultValue;
            this.cache[key] = data;
            return data;
        } catch (e) { return defaultValue; }
    }

    set(key, value, emitEvent = true) {
        console.log('[PhysiqDataStore] set() called:', key);
        try {
            this.cache[key] = value;
            localStorage.setItem(key, JSON.stringify(value));
            console.log('[PhysiqDataStore] Saved to localStorage:', key);
            if (this.subscribers[key]) {
                this.subscribers[key].forEach(cb => cb(value));
            }
            if (emitEvent) {
                const eventName = key.replace('_v1', '').replace('physiq_', '').replace('weight_tracker_', '');
                physiqBus.emit(`data:${eventName}`, { key, value });
            }
            return true;
        } catch (e) { 
            console.error('[PhysiqDataStore] set() failed:', e);
            return false; 
        }
    }

    subscribe(key, callback) {
        if (!this.subscribers[key]) this.subscribers[key] = [];
        this.subscribers[key].push(callback);
        callback(this.get(key));
        return () => { this.subscribers[key] = this.subscribers[key].filter(cb => cb !== callback); };
    }

    hydrate() {
        Object.values(this.STORAGE_KEYS).forEach(key => this.get(key));
    }

    getWeightData() {
        return this.get(this.STORAGE_KEYS.WEIGHT, { entries: [], goal: { targetWeight: null, targetDate: null }, milestones: [] });
    }

    getSettings() { return this.get(this.STORAGE_KEYS.SETTINGS, { unit: 'lbs', goalWeight: null }); }
    getWorkouts() { return this.get(this.STORAGE_KEYS.WORKOUTS, []); }
    getPhotos() { return this.get(this.STORAGE_KEYS.PHOTOS, []); }
    getPredictions() { return this.get(this.STORAGE_KEYS.PREDICTIONS, []); }
    getInsights() { return this.get(this.STORAGE_KEYS.INSIGHTS, []); }
    getAvatarState() {
        return this.get(this.STORAGE_KEYS.AVATAR_STATE, { currentWeight: 180, targetWeight: 170, morphLevel: 0, lastUpdated: null });
    }
}

const physiqStore = new PhysiqDataStore();

// ========================================
// WEIGHT INTEGRATION
// ========================================

class WeightIntegration {
    constructor() { this.initListeners(); }

    initListeners() {
        physiqBus.subscribe('weight:logged', this.onWeightLogged.bind(this));
    }

    onWeightLogged(data) {
        this.updateAvatarMorph(data.weight);
        this.recalculateProgress();
        this.generateWeightInsights(data.entry);
        this.checkMilestones(data.weight);
        physiqBus.emit('prediction:update', { type: 'weight', data: data.entry });
    }

    updateAvatarMorph(currentWeight) {
        const settings = physiqStore.getSettings();
        const goalWeight = settings.goalWeight || currentWeight - 10;
        const startWeight = this.getStartWeight() || currentWeight;
        const totalToLose = startWeight - goalWeight;
        const lostSoFar = startWeight - currentWeight;
        const morphLevel = Math.max(0, Math.min(1, lostSoFar / totalToLose));

        const avatarState = physiqStore.getAvatarState();
        avatarState.currentWeight = currentWeight;
        avatarState.targetWeight = goalWeight;
        avatarState.morphLevel = morphLevel;
        avatarState.lastUpdated = new Date().toISOString();
        physiqStore.set(physiqStore.STORAGE_KEYS.AVATAR_STATE, avatarState);

        physiqBus.emit('avatar:morph', { level: morphLevel, currentWeight, targetWeight: goalWeight, progress: Math.round(morphLevel * 100) });
    }

    recalculateProgress() {
        const weightData = physiqStore.getWeightData();
        if (!weightData) return;
        const entries = weightData.entries || [];
        if (entries.length < 2) return;

        const current = entries[entries.length - 1];
        const first = entries[0];
        const settings = physiqStore.getSettings();

        const progress = {
            currentWeight: current.weight,
            startWeight: first.weight,
            change: current.weight - first.weight,
            changePercent: ((current.weight - first.weight) / first.weight) * 100,
            daysTracked: entries.length,
            goalWeight: settings.goalWeight,
            goalProgress: settings.goalWeight ? ((first.weight - current.weight) / (first.weight - settings.goalWeight)) * 100 : null,
            lastUpdated: new Date().toISOString()
        };
        physiqBus.emit('progress:updated', progress);
    }

    generateWeightInsights(entry) {
        const weightData = physiqStore.getWeightData();
        if (!weightData) return;
        const entries = weightData.entries || [];
        if (entries.length < 2) return;

        const insights = [];
        const streak = this.calculateStreak(entries);
        if (streak >= 7) {
            insights.push({ type: 'consistency', message: `🔥 ${streak} day logging streak! Keep it up!`, severity: 'positive', timestamp: new Date().toISOString() });
        }

        const existingInsights = physiqStore.getInsights();
        physiqStore.set(physiqStore.STORAGE_KEYS.INSIGHTS, [...insights, ...existingInsights].slice(0, 50));
        physiqBus.emit('insights:generated', { insights });
    }

    checkMilestones(currentWeight) {
        const weightData = physiqStore.getWeightData();
        if (!weightData) return;
        const milestones = weightData.milestones || [];
        let updated = false;

        milestones.forEach(m => {
            if (!m.achieved && currentWeight <= m.weight) {
                m.achieved = new Date().toISOString().split('T')[0];
                m.celebrated = false;
                updated = true;
                physiqBus.emit('milestone:achieved', { weight: m.weight });
            }
        });

        if (updated) {
            weightData.milestones = milestones;
            physiqStore.set(physiqStore.STORAGE_KEYS.WEIGHT, weightData);
        }
    }

    calculateStreak(entries) {
        if (!entries || entries.length === 0) return 0;
        let streak = 1;
        const sorted = [...entries].sort((a, b) => new Date(b.date) - new Date(a.date));
        for (let i = 1; i < sorted.length; i++) {
            const diffDays = (new Date(sorted[i - 1].date) - new Date(sorted[i].date)) / (1000 * 60 * 60 * 24);
            if (diffDays <= 1.5) streak++; else break;
        }
        return streak;
    }

    getStartWeight() {
        const weightData = physiqStore.getWeightData();
        if (!weightData) return null;
        const entries = weightData.entries || [];
        return entries.length > 0 ? entries[0].weight : null;
    }

    logWeight(weight, date = null, notes = '') {
        console.log('[WeightIntegration] logWeight() called:', { weight, date, notes });
        const weightData = physiqStore.getWeightData() || { entries: [], goal: { targetWeight: null, targetDate: null }, milestones: [] };
        console.log('[WeightIntegration] Current weight data:', weightData);
        const entries = weightData.entries || [];
        const entry = { id: Date.now().toString(), weight: parseFloat(weight), date: date || new Date().toISOString().split('T')[0], notes, timestamp: new Date().toISOString() };
        console.log('[WeightIntegration] New entry:', entry);

        const existingIndex = entries.findIndex(e => e.date === entry.date);
        if (existingIndex >= 0) entries[existingIndex] = entry; else entries.push(entry);
        entries.sort((a, b) => new Date(a.date) - new Date(b.date));

        weightData.entries = entries;
        console.log('[WeightIntegration] Saving weight data with', entries.length, 'entries');
        physiqStore.set(physiqStore.STORAGE_KEYS.WEIGHT, weightData);
        physiqBus.emit('weight:logged', { weight: entry.weight, date: entry.date, entry });
        console.log('[WeightIntegration] logWeight() complete');
        return entry;
    }
}

// ========================================
// WORKOUT INTEGRATION
// ========================================

class WorkoutIntegration {
    constructor() { this.initListeners(); }
    initListeners() { physiqBus.subscribe('workout:saved', this.onWorkoutSaved.bind(this)); }

    onWorkoutSaved(data) {
        this.generateBodyPrediction(data);
        this.generateWorkoutInsights(data);
    }

    generateBodyPrediction(workout) {
        const currentWeight = physiqStore.getWeightData().entries?.slice(-1)[0]?.weight || 180;
        const predictions = physiqStore.getPredictions();
        const intensity = this.calculateIntensity(workout);
        const estimatedCalories = intensity * 50;
        const estimatedFatLoss = estimatedCalories / 3500;

        const prediction = {
            id: Date.now().toString(), type: 'body_change', workoutId: workout.id, currentWeight,
            predictedWeight: currentWeight - estimatedFatLoss, estimatedCalories, estimatedFatLoss,
            timeframe: '7_days', confidence: 0.7, timestamp: new Date().toISOString()
        };

        predictions.push(prediction);
        physiqStore.set(physiqStore.STORAGE_KEYS.PREDICTIONS, predictions.slice(-20));
        physiqBus.emit('prediction:generated', prediction);
    }

    generateWorkoutInsights(workout) {
        const workouts = physiqStore.getWorkouts();
        const insights = [];
        const weekAgo = new Date(); weekAgo.setDate(weekAgo.getDate() - 7);
        const thisWeek = workouts.filter(w => new Date(w.date || w.timestamp) >= weekAgo);

        if (thisWeek.length >= 3) {
            insights.push({ type: 'workout_frequency', message: `💪 ${thisWeek.length} workouts this week! Great consistency!`, severity: 'positive', timestamp: new Date().toISOString() });
        }

        const existingInsights = physiqStore.getInsights();
        physiqStore.set(physiqStore.STORAGE_KEYS.INSIGHTS, [...insights, ...existingInsights].slice(0, 50));
        physiqBus.emit('insights:generated', { insights });
    }

    calculateIntensity(workout) {
        if (!workout.exercises) return 5;
        return workout.exercises.reduce((sum, ex) => sum + (ex.sets || 3) * (ex.reps || 10), 0) / 10;
    }

    saveWorkout(workout) {
        const workouts = physiqStore.getWorkouts();
        const newWorkout = { id: Date.now().toString(), ...workout, timestamp: new Date().toISOString() };
        workouts.push(newWorkout);
        physiqStore.set(physiqStore.STORAGE_KEYS.WORKOUTS, workouts);
        physiqBus.emit('workout:saved', newWorkout);
        return newWorkout;
    }
}

// ========================================
// PHOTO INTEGRATION
// ========================================

class PhotoIntegration {
    constructor() { this.initListeners(); }
    initListeners() { physiqBus.subscribe('photo:uploaded', this.onPhotoUploaded.bind(this)); }

    onPhotoUploaded(data) {
        this.addToTimeline(data);
        const insights = [{ type: 'photo', message: '📸 New progress photo added to your timeline', severity: 'positive', timestamp: new Date().toISOString() }];
        const existingInsights = physiqStore.getInsights();
        physiqStore.set(physiqStore.STORAGE_KEYS.INSIGHTS, [...insights, ...existingInsights].slice(0, 50));
        physiqBus.emit('insights:generated', { insights });
    }

    addToTimeline(photoData) {
        const photos = physiqStore.getPhotos();
        const photo = { id: photoData.id || Date.now().toString(), src: photoData.src, date: photoData.date || new Date().toISOString().split('T')[0], type: photoData.type || 'progress', timestamp: new Date().toISOString() };
        photos.push(photo);
        physiqStore.set(physiqStore.STORAGE_KEYS.PHOTOS, photos);
        physiqBus.emit('timeline:updated', { photo, photos });
    }

    getTimeline() {
        const photos = physiqStore.getPhotos();
        const weightData = physiqStore.getWeightData();
        const workouts = physiqStore.getWorkouts();
        const timeline = [];

        photos.forEach(p => timeline.push({ type: 'photo', date: p.date, data: p, timestamp: new Date(p.timestamp || p.date).getTime() }));
        weightData.entries?.forEach(e => timeline.push({ type: 'weight', date: e.date, data: e, timestamp: new Date(e.timestamp || e.date).getTime() }));
        workouts.forEach(w => timeline.push({ type: 'workout', date: w.date || w.timestamp?.split('T')[0], data: w, timestamp: new Date(w.timestamp || w.date).getTime() }));

        return timeline.sort((a, b) => b.timestamp - a.timestamp);
    }

    uploadPhoto(photoData) {
        const newPhoto = { id: Date.now().toString(), ...photoData, timestamp: new Date().toISOString() };
        physiqBus.emit('photo:uploaded', newPhoto);
        return newPhoto;
    }
}

// ========================================
// AVATAR INTEGRATION
// ========================================

class AvatarIntegration {
    constructor() {
        this.morphState = { level: 0, targetLevel: 0, animating: false };
        this.initListeners();
    }

    initListeners() {
        physiqBus.subscribe('avatar:morph', this.onMorph.bind(this));
    }

    onMorph(data) {
        this.morphState.targetLevel = data.level;
        this.morphState.targetWeight = data.targetWeight;
        this.morphState.currentWeight = data.currentWeight;
        if (!this.morphState.animating) this.animateMorph();
        this.updateAvatarDisplay(data);
    }

    animateMorph() {
        this.morphState.animating = true;
        const step = () => {
            const diff = this.morphState.targetLevel - this.morphState.level;
            if (Math.abs(diff) < 0.001) { this.morphState.level = this.morphState.targetLevel; this.morphState.animating = false; return; }
            this.morphState.level += diff * 0.1;
            this.applyMorph(this.morphState.level);
            requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
    }

    applyMorph(level) {
        const scale = 1 - (level * 0.15);
        document.documentElement.style.setProperty('--avatar-scale-x', scale);
        document.documentElement.style.setProperty('--avatar-scale-y', 1 - (level * 0.05));
        physiqBus.emit('avatar:scale', { x: scale, y: 1 - (level * 0.05), level });
    }

    updateAvatarDisplay(data) {
        const weightDisplay = document.getElementById('avatarWeightDisplay');
        if (weightDisplay) weightDisplay.textContent = data.currentWeight.toFixed(1);
        const progressDisplay = document.getElementById('avatarProgress');
        if (progressDisplay) progressDisplay.textContent = `${data.progress}%`;
        const miniAvatar = document.getElementById('avatarBody');
        if (miniAvatar) miniAvatar.style.transform = `scaleX(${1 - (data.level * 0.15)})`;
    }
}

// ========================================
// DASHBOARD INTEGRATION
// ========================================

class DashboardIntegration {
    constructor() { this.initListeners(); }

    initListeners() {
        physiqBus.subscribe('data:weight', this.onWeightDataChange.bind(this));
        physiqBus.subscribe('progress:updated', this.onProgressUpdate.bind(this));
        physiqBus.subscribe('insights:generated', this.onInsightsGenerated.bind(this));
        physiqBus.subscribe('milestone:achieved', this.onMilestoneAchieved.bind(this));
        physiqBus.subscribe('timeline:updated', this.onTimelineUpdated.bind(this));
    }

    onWeightDataChange(data) {
        const entries = data.value?.entries || [];
        if (entries.length > 0) {
            const current = entries[entries.length - 1];
            const el = document.getElementById('currentWeight');
            if (el) el.textContent = current.weight.toFixed(1);
            const el2 = document.getElementById('currentWeightSmall');
            if (el2) el2.textContent = current.weight.toFixed(1);
            const el3 = document.getElementById('statCurrent');
            if (el3) el3.textContent = current.weight.toFixed(1);
        }
    }

    onProgressUpdate(data) {
        const bar = document.getElementById('goalProgressBar');
        const marker = document.getElementById('currentMarker');
        if (bar && data.goalProgress !== null) {
            const percent = Math.min(100, Math.max(0, data.goalProgress));
            bar.style.width = `${percent}%`;
            if (marker) marker.style.left = `${percent}%`;
        }

        const elements = {
            'statChange': data.change?.toFixed(1),
            'statDays': data.daysTracked,
            'totalLost': Math.abs(data.change || 0).toFixed(1)
        };
        Object.entries(elements).forEach(([id, value]) => {
            const el = document.getElementById(id);
            if (el && value !== undefined) el.textContent = value;
        });
    }

    onInsightsGenerated(data) {
        const container = document.getElementById('insightsList');
        if (!container || !data.insights) return;
        container.innerHTML = data.insights.slice(0, 5).map(i => `
            <div class="insight-item ${i.severity}">
                <span class="insight-message">${i.message}</span>
                <span class="insight-time">${new Date(i.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'})}</span>
            </div>
        `).join('');
    }

    onTimelineUpdated(data) {
        const container = document.getElementById('timelineList');
        if (!container) return;
        const timeline = new PhotoIntegration().getTimeline().slice(0, 10);
        container.innerHTML = timeline.map(item => {
            if (item.type === 'photo') return `<div class="timeline-item photo"><div class="timeline-date">${item.date}</div><div class="timeline-content"><span class="timeline-icon">📸</span><span>Progress photo added</span></div></div>`;
            if (item.type === 'weight') return `<div class="timeline-item weight"><div class="timeline-date">${item.date}</div><div class="timeline-content"><span class="timeline-icon">⚖️</span><span>Weight: ${item.data.weight.toFixed(1)} lbs</span></div></div>`;
            if (item.type === 'workout') return `<div class="timeline-item workout"><div class="timeline-date">${item.date}</div><div class="timeline-content"><span class="timeline-icon">💪</span><span>Workout completed</span></div></div>`;
            return '';
        }).join('');
    }

    onMilestoneAchieved(data) {
        const overlay = document.getElementById('celebrationOverlay');
        if (overlay) {
            const weightSpan = overlay.querySelector('.milestone-weight');
            if (weightSpan) weightSpan.textContent = `${data.weight} lbs`;
            overlay.classList.remove('hidden');
            if (typeof launchConfetti === 'function') launchConfetti();
        }
    }

    refresh() {
        this.onWeightDataChange({ value: physiqStore.getWeightData() });
        new WeightIntegration().recalculateProgress();
        this.onInsightsGenerated({ insights: physiqStore.getInsights() });
        this.onTimelineUpdated({});
    }
}

// ========================================
// INSIGHTS ENGINE
// ========================================

class InsightsEngine {
    constructor() { this.initListeners(); }

    initListeners() {
        physiqBus.subscribe('data:weight', this.analyzeWeightPatterns.bind(this));
        physiqBus.subscribe('data:workouts', this.analyzeWorkoutPatterns.bind(this));
    }

    analyzeWeightPatterns(data) {
        const entries = data.value?.entries || [];
        if (entries.length < 3) return;
        const insights = [];

        const recent = entries.slice(-7);
        const avgRecent = recent.reduce((sum, e) => sum + e.weight, 0) / recent.length;
        const previous = entries.slice(-14, -7);

        if (previous.length > 0) {
            const avgPrevious = previous.reduce((sum, e) => sum + e.weight, 0) / previous.length;
            const change = avgRecent - avgPrevious;
            if (Math.abs(change) > 1) {
                insights.push({ type: 'weight_trend', message: `Your weight has ${change < 0 ? 'decreased' : 'increased'} by ${Math.abs(change).toFixed(1)} lbs`, severity: change < 0 ? 'positive' : 'warning', timestamp: new Date().toISOString() });
            }
        }

        const existingInsights = physiqStore.getInsights();
        physiqStore.set(physiqStore.STORAGE_KEYS.INSIGHTS, [...insights, ...existingInsights].slice(0, 50));
        if (insights.length > 0) physiqBus.emit('insights:generated', { insights });
    }

    analyzeWorkoutPatterns(data) {
        const workouts = data.value || [];
        if (workouts.length < 2) return;
        const insights = [];

        const weekAgo = new Date(); weekAgo.setDate(weekAgo.getDate() - 7);
        const thisWeek = workouts.filter(w => new Date(w.timestamp || w.date) >= weekAgo);

        if (thisWeek.length >= 4) {
            insights.push({ type: 'workout_frequency', message: '🏋️ Excellent! 4+ workouts this week!', severity: 'positive', timestamp: new Date().toISOString() });
        } else if (thisWeek.length === 0) {
            insights.push({ type: 'workout_frequency', message: 'No workouts this week. Ready to get back at it?', severity: 'warning', timestamp: new Date().toISOString() });
        }

        const existingInsights = physiqStore.getInsights();
        physiqStore.set(physiqStore.STORAGE_KEYS.INSIGHTS, [...insights, ...existingInsights].slice(0, 50));
        if (insights.length > 0) physiqBus.emit('insights:generated', { insights });
    }
}

// ========================================
// INITIALIZATION
// ========================================

const PhysiqIntegration = {
    bus: physiqBus,
    store: physiqStore,
    weight: new WeightIntegration(),
    workout: new WorkoutIntegration(),
    photo: new PhotoIntegration(),
    avatar: new AvatarIntegration(),
    dashboard: new DashboardIntegration(),
    insights: new InsightsEngine(),

    init() {
        console.log('[PhysiqIntegration] Initializing...');
        console.log('[PhysiqIntegration] weight.logWeight exists:', typeof this.weight.logWeight);
        this.dashboard.refresh();
        console.log('[PhysiqIntegration] Ready!');
        return this;
    },

    logWeight(weight, date, notes) { return this.weight.logWeight(weight, date, notes); },
    saveWorkout(workout) { return this.workout.saveWorkout(workout); },
    uploadPhoto(photoData) { return this.photo.uploadPhoto(photoData); },
    getTimeline() { return this.photo.getTimeline(); },
    refresh() { this.dashboard.refresh(); }
};

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => PhysiqIntegration.init());
} else {
    PhysiqIntegration.init();
}

// Export for global access
window.PhysiqIntegration = PhysiqIntegration;
window.physiqBus = physiqBus;
window.physiqStore = physiqStore;