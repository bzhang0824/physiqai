/" ========================================
   WEIGHT DASHBOARD JAVASCRIPT
   Alive, motivating, connected to avatar
   ======================================== */

// Weight Tracker Data
let weightData = null;
let chartInstance = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Initialize error handler
    if (typeof ErrorHandler !== 'undefined') {
        ErrorHandler.init();
    }
    
    // Wrap initialization in error boundary if available
    if (typeof ErrorBoundary !== 'undefined') {
        const dashboardBoundary = new ErrorBoundary('weight-section', {
            componentName: 'Weight Dashboard',
            fallbackHTML: `
                <div class="error-boundary-fallback">
                    <div class="error-icon">⚠️</div>
                    <h3>Dashboard Temporarily Unavailable</h3>
                    <p>We're having trouble loading your weight data.</p>
                    <button class="btn btn-primary" onclick="location.reload()">Try Again</button>
                </div>
            `
        });
        
        try {
            loadWeightData();
            initSparkline();
            checkMilestones();
            startLiveSync();
        } catch (error) {
            dashboardBoundary.handleError(error);
        }
    } else {
        loadWeightData();
        initSparkline();
        checkMilestones();
        startLiveSync();
    }
});

// Load weight data from localStorage or use default
async function loadWeightData() {
    // Always try localStorage first (primary data source)
    const localStorageKey = 'physiq_weight_data';
    const stored = localStorage.getItem(localStorageKey);
    
    if (stored) {
        try {
            weightData = JSON.parse(stored);
            updateDashboard();
            return;
        } catch (e) {
            console.warn('Failed to parse stored weight data:', e);
        }
    }
    
    // Use default/demo data
    weightData = getDefaultWeightData();
    
    // Optionally try to fetch from server if available, but don't fail
    try {
        const response = await fetch('../data/weight-tracker.json');
        if (response.ok) {
            const fetched = await response.json();
            weightData = fetched;
            // Save to localStorage for next time
            localStorage.setItem(localStorageKey, JSON.stringify(weightData));
        }
    } catch (error) {
        console.log('Using default weight data (fetch unavailable):', error);
    }
    
    if (typeof ErrorHandler !== 'undefined') {
            ErrorHandler.showUserMessage('Could not load data. Using defaults.', 'warning');
        }
        weightData = getDefaultWeightData();
    }
    
    updateDashboard();
}

// Default weight data (fallback)
function getDefaultWeightData() {
    return {
        userId: "user_001",
        goal: {
            targetWeight: 170,
            targetDate: "2026-05-01",
            startWeight: 180,
            startDate: "2026-01-15"
        },
        current: {
            weight: 172.5,
            date: "2026-02-23",
            bodyFat: 13.8,
            muscle: 43.2
        },
        history: [
            {date: "2026-01-15", weight: 180.0, bodyFat: 16.3, muscle: 39.8},
            {date: "2026-01-22", weight: 179.2, bodyFat: 16.0, muscle: 40.1},
            {date: "2026-01-29", weight: 178.5, bodyFat: 15.7, muscle: 40.4},
            {date: "2026-02-05", weight: 177.1, bodyFat: 15.3, muscle: 41.0},
            {date: "2026-02-12", weight: 175.8, bodyFat: 14.9, muscle: 41.8},
            {date: "2026-02-19", weight: 174.2, bodyFat: 14.5, muscle: 42.4},
            {date: "2026-02-23", weight: 172.5, bodyFat: 13.8, muscle: 43.2}
        ],
        milestones: [
            {weight: 175, achieved: "2026-02-12", celebrated: true},
            {weight: 170, achieved: null, celebrated: false}
        ],
        streaks: {
            currentCheckIn: 7,
            longestCheckIn: 12,
            weighInsThisMonth: 7
        }
    };
}

// Update all dashboard elements
function updateDashboard() {
    if (!weightData) return;
    
    const current = weightData.current;
    const history = weightData.history;
    const goal = weightData.goal;
    
    // Update current weight display
    animateNumber('currentWeight', current.weight);
    document.getElementById('currentWeightSmall').textContent = current.weight.toFixed(1);
    
    // Update avatar weight display
    document.getElementById('avatarWeightDisplay').textContent = current.weight.toFixed(1);
    
    // Calculate changes
    const lastWeek = history[history.length - 2];
    const lastMonth = history[0];
    
    const weekChange = current.weight - lastWeek.weight;
    const monthChange = current.weight - lastMonth.weight;
    
    updateChangeDisplay('changeWeek', weekChange);
    updateChangeDisplay('changeMonth', monthChange);
    
    // Update sparkline stats
    document.getElementById('startWeight').textContent = goal.startWeight.toFixed(1);
    document.getElementById('totalLost').textContent = (current.weight - goal.startWeight).toFixed(1);
    
    // Update goal section
    document.getElementById('goalStart').textContent = goal.startWeight.toFixed(1);
    document.getElementById('goalTarget').textContent = goal.targetWeight.toFixed(1);
    
    // Calculate and update progress
    const totalToLose = goal.startWeight - goal.targetWeight;
    const lostSoFar = goal.startWeight - current.weight;
    const progressPercent = Math.min(100, Math.max(0, (lostSoFar / totalToLose) * 100));
    
    document.getElementById('goalProgressBar').style.width = progressPercent + '%';
    document.getElementById('currentMarker').style.left = progressPercent + '%';
    
    // Update streak
    document.getElementById('streakValue').textContent = `🔥 ${weightData.streaks.currentCheckIn} days`;
    
    // Update avatar visual based on progress
    updateAvatarVisual(progressPercent);
    
    // Redraw sparkline with current data
    drawSparkline();
}

// Update change display with animation
function updateChangeDisplay(elementId, change) {
    const element = document.getElementById(elementId);
    const isPositive = change < 0; // For weight loss, negative is good
    
    element.className = 'change-value ' + (isPositive ? 'positive' : 'negative');
    element.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="${isPositive ? '23 18 13.5 8.5 8.5 13.5 1 6' : '23 6 13.5 15.5 8.5 10.5 1 18'}"/>
        </svg>
        ${change > 0 ? '+' : ''}${change.toFixed(1)} lbs
    `;
}

// Animate number counting
function animateNumber(elementId, targetValue) {
    const element = document.getElementById(elementId);
    const startValue = parseFloat(element.textContent) || 0;
    const duration = 1000;
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const easeOutQuart = 1 - Math.pow(1 - progress, 4);
        
        const current = startValue + (targetValue - startValue) * easeOutQuart;
        element.textContent = current.toFixed(1);
        
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Update avatar visual based on weight progress
function updateAvatarVisual(progressPercent) {
    const torso = document.getElementById('avatarTorso');
    const syncedTorso = document.getElementById('avatarTorso');
    
    // Scale torso slightly based on progress (thinner as progress increases)
    const scale = 1 - (progressPercent / 1000); // Max 10% reduction
    if (torso) {
        torso.style.transform = `scaleX(${scale})`;
    }
}

// Initialize and draw sparkline chart
function initSparkline() {
    drawSparkline();
}

function drawSparkline() {
    const canvas = document.getElementById('weightSparkline');
    if (!canvas || !weightData) return;
    
    const ctx = canvas.getContext('2d');
    const history = weightData.history;
    
    // Handle high-DPI displays
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    const width = rect.width;
    const height = rect.height;
    const padding = 10;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Find min/max for scaling
    const weights = history.map(h => h.weight);
    const minWeight = Math.min(...weights) - 1;
    const maxWeight = Math.max(...weights) + 1;
    const range = maxWeight - minWeight;
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, 0, height);
    gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
    gradient.addColorStop(1, 'rgba(99, 102, 241, 0)');
    
    // Draw filled area
    ctx.beginPath();
    history.forEach((point, index) => {
        const x = (index / (history.length - 1)) * (width - padding * 2) + padding;
        const y = height - padding - ((point.weight - minWeight) / range) * (height - padding * 2);
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            // Smooth curve
            const prevX = ((index - 1) / (history.length - 1)) * (width - padding * 2) + padding;
            const prevY = height - padding - ((history[index - 1].weight - minWeight) / range) * (height - padding * 2);
            const cpX = (prevX + x) / 2;
            ctx.quadraticCurveTo(cpX, prevY, cpX, (prevY + y) / 2);
            ctx.quadraticCurveTo(cpX, y, x, y);
        }
    });
    
    // Close path for fill
    ctx.lineTo(width - padding, height);
    ctx.lineTo(padding, height);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
    
    // Draw line
    ctx.beginPath();
    history.forEach((point, index) => {
        const x = (index / (history.length - 1)) * (width - padding * 2) + padding;
        const y = height - padding - ((point.weight - minWeight) / range) * (height - padding * 2);
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            const prevX = ((index - 1) / (history.length - 1)) * (width - padding * 2) + padding;
            const prevY = height - padding - ((history[index - 1].weight - minWeight) / range) * (height - padding * 2);
            const cpX = (prevX + x) / 2;
            ctx.quadraticCurveTo(cpX, prevY, cpX, (prevY + y) / 2);
            ctx.quadraticCurveTo(cpX, y, x, y);
        }
    });
    
    ctx.strokeStyle = '#6366f1';
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.stroke();
    
    // Draw points
    history.forEach((point, index) => {
        const x = (index / (history.length - 1)) * (width - padding * 2) + padding;
        const y = height - padding - ((point.weight - minWeight) / range) * (height - padding * 2);
        
        ctx.beginPath();
        ctx.arc(x, y, index === history.length - 1 ? 6 : 4, 0, Math.PI * 2);
        ctx.fillStyle = index === history.length - 1 ? '#10b981' : '#6366f1';
        ctx.fill();
        
        if (index === history.length - 1) {
            ctx.strokeStyle = '#0f0f1a';
            ctx.lineWidth = 2;
            ctx.stroke();
            
            // Add glow effect for current point
            ctx.beginPath();
            ctx.arc(x, y, 12, 0, Math.PI * 2);
            ctx.fillStyle = 'rgba(16, 185, 129, 0.3)';
            ctx.fill();
        }
    });
}

// Check and trigger milestone celebrations
function checkMilestones() {
    if (!weightData) return;
    
    const uncelebrated = weightData.milestones.find(m => m.achieved && !m.celebrated);
    
    if (uncelebrated) {
        showCelebration(uncelebrated.weight);
        uncelebrated.celebrated = true;
    }
}

// Show celebration overlay with confetti
function showCelebration(milestoneWeight) {
    const overlay = document.getElementById('celebrationOverlay');
    const weightSpan = overlay.querySelector('.milestone-weight');
    
    weightSpan.textContent = milestoneWeight + ' lbs';
    overlay.classList.remove('hidden');
    
    // Launch confetti
    launchConfetti();
    
    // Play celebration sound (optional)
    playCelebrationSound();
}

// Dismiss celebration
function dismissCelebration() {
    const overlay = document.getElementById('celebrationOverlay');
    overlay.classList.add('hidden');
    
    // Stop confetti
    const canvas = document.getElementById('confettiCanvas');
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

// Share milestone
function shareMilestone() {
    const text = `🎉 Just hit ${weightData.current.weight} lbs on my fitness journey with PhysiqAI!`;
    
    if (navigator.share) {
        navigator.share({
            title: 'Milestone Achieved!',
            text: text
        });
    } else {
        // Copy to clipboard fallback
        navigator.clipboard.writeText(text).then(() => {
            alert('Milestone copied to clipboard!');
        });
    }
}

// Confetti effect
function launchConfetti() {
    const canvas = document.getElementById('confettiCanvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    
    const particles = [];
    const colors = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];
    
    // Create particles
    for (let i = 0; i < 150; i++) {
        particles.push({
            x: canvas.width / 2,
            y: canvas.height / 2,
            vx: (Math.random() - 0.5) * 20,
            vy: (Math.random() - 0.5) * 20 - 10,
            color: colors[Math.floor(Math.random() * colors.length)],
            size: Math.random() * 8 + 4,
            rotation: Math.random() * 360,
            rotationSpeed: (Math.random() - 0.5) * 10,
            gravity: 0.3,
            drag: 0.98
        });
    }
    
    let animationId;
    
    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        let activeParticles = 0;
        
        particles.forEach(p => {
            if (p.y < canvas.height + 50) {
                activeParticles++;
                
                // Update position
                p.x += p.vx;
                p.y += p.vy;
                p.vy += p.gravity;
                p.vx *= p.drag;
                p.vy *= p.drag;
                p.rotation += p.rotationSpeed;
                
                // Draw particle
                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate((p.rotation * Math.PI) / 180);
                ctx.fillStyle = p.color;
                ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
                ctx.restore();
            }
        });
        
        if (activeParticles > 0) {
            animationId = requestAnimationFrame(animate);
        }
    }
    
    animate();
    
    // Stop after 5 seconds
    setTimeout(() => {
        cancelAnimationFrame(animationId);
    }, 5000);
}

// Play celebration sound
function playCelebrationSound() {
    // Create a simple celebratory sound using Web Audio API
    try {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Create oscillator for a pleasant chime
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.frequency.setValueAtTime(523.25, audioContext.currentTime); // C5
        oscillator.frequency.exponentialRampToValueAtTime(1046.5, audioContext.currentTime + 0.1); // C6
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.5);
        
        // Second note
        setTimeout(() => {
            const osc2 = audioContext.createOscillator();
            const gain2 = audioContext.createGain();
            osc2.connect(gain2);
            gain2.connect(audioContext.destination);
            
            osc2.frequency.setValueAtTime(659.25, audioContext.currentTime); // E5
            gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.4);
            
            osc2.start(audioContext.currentTime);
            osc2.stop(audioContext.currentTime + 0.4);
        }, 150);
        
        // Third note
        setTimeout(() => {
            const osc3 = audioContext.createOscillator();
            const gain3 = audioContext.createGain();
            osc3.connect(gain3);
            gain3.connect(audioContext.destination);
            
            osc3.frequency.setValueAtTime(783.99, audioContext.currentTime); // G5
            gain3.gain.setValueAtTime(0.3, audioContext.currentTime);
            gain3.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.6);
            
            osc3.start(audioContext.currentTime);
            osc3.stop(audioContext.currentTime + 0.6);
        }, 300);
        
    } catch (e) {
        console.log('Audio not supported');
    }
}

// Log weight button handler
function logWeight() {
    const weight = prompt('Enter your current weight (lbs):');
    
    if (!weight || isNaN(weight)) {
        if (typeof ErrorHandler !== 'undefined') {
            ErrorHandler.showUserMessage('Please enter a valid weight.', 'error');
        } else {
            alert('⚠️ Please enter a valid weight.');
        }
        return;
    }
    
    const newWeight = parseFloat(weight);
    
    // Validate weight range
    if (newWeight < 50 || newWeight > 1000) {
        if (typeof ErrorHandler !== 'undefined') {
            ErrorHandler.showUserMessage('Please enter a weight between 50 and 1000 lbs.', 'error');
        } else {
            alert('⚠️ Please enter a weight between 50 and 1000 lbs.');
        }
        return;
    }
    
    // Update current weight
    weightData.current.weight = newWeight;
    weightData.current.date = new Date().toISOString().split('T')[0];
    
    // Add to history
    weightData.history.push({
        date: weightData.current.date,
        weight: newWeight,
        bodyFat: weightData.current.bodyFat,
        muscle: weightData.current.muscle
    });
    
    // Update streak
    weightData.streaks.currentCheckIn++;
    
    // Check for milestones
    weightData.milestones.forEach(m => {
        if (!m.achieved && newWeight <= m.weight) {
            m.achieved = weightData.current.date;
            m.celebrated = false;
        }
    });
    
    // Save to localStorage safely
    if (typeof ErrorHandler !== 'undefined') {
        const saved = ErrorHandler.storage.set('weightData', weightData);
        if (!saved) {
            ErrorHandler.showUserMessage('Could not save data. Storage may be full.', 'warning');
        }
    }
    
    // Update dashboard
    updateDashboard();
    
    // Check for new celebrations
    checkMilestones();
    
    // Show success message
    showNotification('Weight logged successfully! 🎉');
    }
}

// Show notification
function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'weight-notification';
    notification.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="20 6 9 17 4 12"/>
        </svg>
        ${message}
    `;
    
    notification.style.cssText = `
        position: fixed;
        bottom: 2rem;
        right: 2rem;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 1rem 1.5rem;
        background: var(--secondary);
        color: white;
        border-radius: var(--border-radius);
        font-weight: 500;
        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);
        z-index: 9999;
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Start live sync simulation
function startLiveSync() {
    // Simulate occasional sync updates
    setInterval(() => {
        const syncBadge = document.getElementById('syncBadge');
        if (syncBadge) {
            syncBadge.style.opacity = '0.5';
            setTimeout(() => {
                syncBadge.style.opacity = '1';
            }, 300);
        }
    }, 5000);
}

// Handle window resize for sparkline
window.addEventListener('resize', () => {
    drawSparkline();
});

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);
