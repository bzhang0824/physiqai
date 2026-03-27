/**
 * PhysiqAI - Demo Data Loader
 * Loads demo user profiles for presentation
 */

const DemoLoader = {
    data: null,
    currentUser: null,
    
    async init() {
        try {
            const response = await fetch('../data/demo-data.json');
            this.data = await response.json();
            console.log('[DemoLoader] Demo data loaded successfully');
            return true;
        } catch (error) {
            console.error('[DemoLoader] Failed to load demo data:', error);
            return false;
        }
    },
    
    getUser(userId) {
        if (!this.data) return null;
        return this.data.demoUsers.find(u => u.id === userId);
    },
    
    getAllUsers() {
        return this.data?.demoUsers || [];
    },
    
    getComparisonData() {
        return this.data?.comparisonData?.beforeAfter || [];
    },
    
    getShowcaseData() {
        return this.data?.landingPageShowcase || {};
    },
    
    loadUserIntoDashboard(userId) {
        const user = this.getUser(userId);
        if (!user) {
            console.error('[DemoLoader] User not found:', userId);
            return false;
        }
        
        this.currentUser = user;
        
        // Store in session for dashboard access
        sessionStorage.setItem('demoUser', JSON.stringify(user));
        sessionStorage.setItem('isDemoMode', 'true');
        
        // Update dashboard elements
        this.populateDashboard(user);
        
        return true;
    },
    
    populateDashboard(user) {
        // Update header
        const userNameEl = document.getElementById('userName');
        if (userNameEl) userNameEl.textContent = user.name;
        
        // Update stats
        const journey = user.journey;
        const current = journey;
        
        // Update weight display
        const currentWeightEl = document.getElementById('currentWeight');
        if (currentWeightEl) {
            currentWeightEl.textContent = current.currentWeight.toFixed(1);
        }
        
        const startWeightEl = document.getElementById('startWeight');
        if (startWeightEl) {
            startWeightEl.textContent = journey.startWeight.toFixed(1);
        }
        
        const goalTargetEl = document.getElementById('goalTarget');
        if (goalTargetEl) {
            goalTargetEl.textContent = journey.goalWeight.toFixed(1);
        }
        
        // Calculate progress
        const totalChange = journey.startWeight - journey.goalWeight;
        const currentChange = journey.startWeight - current.currentWeight;
        const progressPercent = Math.min(100, Math.max(0, (currentChange / totalChange) * 100));
        
        const goalProgressBar = document.getElementById('goalProgressBar');
        if (goalProgressBar) {
            goalProgressBar.style.width = progressPercent + '%';
        }
        
        // Update timeline
        this.populateTimeline(user.timeline);
        
        // Update achievements
        this.populateAchievements(user.achievements);
        
        // Show demo mode indicator
        this.showDemoBanner(user.name);
    },
    
    populateTimeline(timeline) {
        const container = document.getElementById('timelineContainer');
        if (!container) return;
        
        container.innerHTML = timeline.map((entry, index) => `
            <div class="timeline-item" data-week="${entry.week}">
                <div class="timeline-date">
                    <span class="date-day">${new Date(entry.date).getDate()}</span>
                    <span class="date-month">${new Date(entry.date).toLocaleString('default', { month: 'short' })}</span>
                </div>
                <div class="timeline-content">
                    <div class="timeline-card ${entry.milestones.length > 0 ? 'milestone-achieved' : ''}">
                        ${entry.milestones.length > 0 ? `<div class="milestone-badge">🎉 ${entry.milestones[0]}</div>` : ''}
                        <div class="card-preview">
                            <div class="preview-avatar">
                                <div class="mini-figure" style="background: linear-gradient(180deg, var(--bg-elevated), var(--primary));"></div>
                            </div>
                        </div>
                        <div class="card-details">
                            <div class="card-header">
                                <h3>Week ${entry.week}: ${entry.weight} lbs</h3>
                                <span class="badge ${index === timeline.length - 1 ? 'badge-current' : entry.week === 0 ? 'badge-baseline' : 'badge-past'}">
                                    ${index === timeline.length - 1 ? 'Current' : entry.week === 0 ? 'Baseline' : `${entry.week} weeks`}
                                </span>
                            </div>
                            <div class="metrics-row">
                                <div class="mini-metric">
                                    <span class="label">Weight</span>
                                    <span class="value">${entry.weight} lbs</span>
                                </div>
                                <div class="mini-metric">
                                    <span class="label">Body Fat</span>
                                    <span class="value">${entry.bodyFat}%</span>
                                </div>
                                <div class="mini-metric">
                                    <span class="label">Muscle</span>
                                    <span class="value">${entry.muscle}%</span>
                                </div>
                            </div>
                            ${entry.notes ? `<p class="entry-notes">"${entry.notes}"</p>` : ''}
                            <div class="card-actions">
                                <button class="btn btn-sm btn-primary" onclick="DemoLoader.compareEntry(${entry.week})">View 3D</button>
                                <button class="btn btn-sm btn-secondary" onclick="DemoLoader.compareWithBaseline(${entry.week})">Compare</button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');
    },
    
    populateAchievements(achievements) {
        const container = document.getElementById('achievementsContainer');
        if (!container) return;
        
        container.innerHTML = achievements.map(achievement => `
            <div class="achievement-card">
                <div class="achievement-icon">${achievement.icon}</div>
                <div class="achievement-info">
                    <h4>${achievement.name}</h4>
                    <p>${achievement.description}</p>
                    <span class="achievement-date">${new Date(achievement.date).toLocaleDateString()}</span>
                </div>
            </div>
        `).join('');
    },
    
    showDemoBanner(userName) {
        if (document.getElementById('demoBanner')) return;
        
        const banner = document.createElement('div');
        banner.id = 'demoBanner';
        banner.className = 'demo-banner';
        banner.innerHTML = `
            <div class="demo-banner-content">
                <span class="demo-badge">DEMO MODE</span>
                <span>Viewing ${userName}'s transformation journey</span>
                <button class="demo-switch-btn" onclick="DemoLoader.showUserSelector()">Switch User</button>
                <button class="demo-close" onclick="DemoLoader.hideDemoBanner()">×</button>
            </div>
        `;
        
        document.body.insertBefore(banner, document.body.firstChild);
        
        // Add banner styles if not present
        if (!document.getElementById('demo-banner-styles')) {
            const styles = document.createElement('style');
            styles.id = 'demo-banner-styles';
            styles.textContent = `
                .demo-banner {
                    background: linear-gradient(90deg, #6366f1, #8b5cf6);
                    color: white;
                    padding: 12px 20px;
                    text-align: center;
                    position: fixed;
                    top: 72px;
                    left: 0;
                    right: 0;
                    z-index: 1000;
                    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
                }
                .demo-banner-content {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 16px;
                    flex-wrap: wrap;
                }
                .demo-badge {
                    background: rgba(255,255,255,0.2);
                    padding: 4px 12px;
                    border-radius: 100px;
                    font-size: 12px;
                    font-weight: 700;
                }
                .demo-switch-btn {
                    background: white;
                    color: #6366f1;
                    border: none;
                    padding: 6px 16px;
                    border-radius: 6px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: transform 0.2s;
                }
                .demo-switch-btn:hover {
                    transform: scale(1.05);
                }
                .demo-close {
                    background: none;
                    border: none;
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    padding: 0 4px;
                }
                body.has-demo-banner {
                    padding-top: 120px;
                }
                body.has-demo-banner .navbar {
                    top: 48px;
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.classList.add('has-demo-banner');
    },
    
    hideDemoBanner() {
        const banner = document.getElementById('demoBanner');
        if (banner) banner.remove();
        document.body.classList.remove('has-demo-banner');
        sessionStorage.removeItem('isDemoMode');
    },
    
    showUserSelector() {
        const users = this.getAllUsers();
        
        const modal = document.createElement('div');
        modal.className = 'demo-selector-modal';
        modal.innerHTML = `
            <div class="demo-selector-overlay" onclick="this.parentElement.remove()"></div>
            <div class="demo-selector-content">
                <h2>Select a Demo Profile</h2>
                <div class="demo-users-grid">
                    ${users.map(user => `
                        <div class="demo-user-card" onclick="DemoLoader.selectUser('${user.id}')">
                            <div class="demo-user-avatar">${user.name.charAt(0)}</div>
                            <h3>${user.name}</h3>
                            <p>${user.profile.fitnessGoal.replace('_', ' ')}</p>
                            <div class="demo-user-stats">
                                <span>${user.journey.startWeight} → ${user.journey.currentWeight} lbs</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <button class="demo-selector-close" onclick="this.parentElement.parentElement.remove()">Close</button>
            </div>
        `;
        
        // Add modal styles
        const styles = document.createElement('style');
        styles.textContent = `
            .demo-selector-modal {
                position: fixed;
                inset: 0;
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .demo-selector-overlay {
                position: absolute;
                inset: 0;
                background: rgba(0,0,0,0.8);
            }
            .demo-selector-content {
                position: relative;
                background: var(--bg-secondary);
                padding: 40px;
                border-radius: 20px;
                max-width: 600px;
                width: 90%;
                text-align: center;
            }
            .demo-selector-content h2 {
                margin-bottom: 24px;
            }
            .demo-users-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            .demo-user-card {
                background: var(--bg-tertiary);
                padding: 20px;
                border-radius: 12px;
                cursor: pointer;
                transition: all 0.3s;
                border: 2px solid transparent;
            }
            .demo-user-card:hover {
                border-color: var(--primary);
                transform: translateY(-4px);
            }
            .demo-user-avatar {
                width: 60px;
                height: 60px;
                background: linear-gradient(135deg, var(--primary), var(--primary-light));
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                font-weight: 700;
                margin: 0 auto 12px;
            }
            .demo-user-card h3 {
                font-size: 16px;
                margin-bottom: 4px;
            }
            .demo-user-card p {
                font-size: 12px;
                color: var(--text-secondary);
                text-transform: capitalize;
                margin-bottom: 8px;
            }
            .demo-user-stats {
                font-size: 14px;
                color: var(--primary-light);
                font-weight: 600;
            }
            .demo-selector-close {
                background: var(--bg-tertiary);
                color: var(--text-primary);
                border: 1px solid var(--border-color);
                padding: 12px 24px;
                border-radius: 8px;
                cursor: pointer;
            }
        `;
        modal.appendChild(styles);
        document.body.appendChild(modal);
    },
    
    selectUser(userId) {
        this.loadUserIntoDashboard(userId);
        document.querySelector('.demo-selector-modal')?.remove();
        
        // Reload page to refresh all data
        window.location.reload();
    },
    
    compareEntry(week) {
        ToastSystem.info(`Viewing Week ${week} avatar in 3D`);
        window.location.href = 'avatar.html';
    },
    
    compareWithBaseline(week) {
        ToastSystem.info(`Comparing Week ${week} with baseline`);
        // Trigger comparison mode
        sessionStorage.setItem('comparisonWeek', week);
    },
    
    isDemoMode() {
        return sessionStorage.getItem('isDemoMode') === 'true';
    },
    
    getCurrentDemoUser() {
        if (!this.isDemoMode()) return null;
        const userData = sessionStorage.getItem('demoUser');
        return userData ? JSON.parse(userData) : null;
    }
};

// Auto-initialize
document.addEventListener('DOMContentLoaded', () => {
    DemoLoader.init().then(() => {
        // Check if we should load demo mode
        if (DemoLoader.isDemoMode()) {
            const user = DemoLoader.getCurrentDemoUser();
            if (user) {
                DemoLoader.populateDashboard(user);
            }
        }
    });
});

window.DemoLoader = DemoLoader;
