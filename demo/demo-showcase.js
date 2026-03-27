{user.name}</h3>
                            <p>${user.journey.title}</p>
                        </div>
                    </div>
                    <p style="color: rgba(255,255,255,0.6); font-size: 14px; margin-bottom: 15px;">
                        ${user.journey.description}
                    </p>
                    <div class="journey-stats">
                        <div class="stat-item">
                            <div class="stat-value ${user.journey.totalLost > 0 ? '' : 'negative'}">
                                ${user.journey.totalLost > 0 ? user.journey.totalLost : user.journey.totalGained || user.stats.currentMuscle - user.stats.startMuscle}
                            </div>
                            <div class="stat-label">${user.journey.totalLost > 0 ? 'lbs lost' : 'lbs gained'}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${user.stats.workoutsCompleted}</div>
                            <div class="stat-label">workouts</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${user.stats.consistency}%</div>
                            <div class="stat-label">consistent</div>
                        </div>
                    </div>
                </div>
            `).join('');
        }
        
        function selectUser(userId) {
            demoData.currentUser = demoData.users.find(u => u.id === userId);
            renderUserSelector();
            renderScenario();
        }
        
        function switchScenario(scenario) {
            demoData.currentScenario = scenario;
            
            // Update tabs
            document.querySelectorAll('.scenario-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            event.target.classList.add('active');
            
            // Show/hide celebration for day90
            const banner = document.getElementById('celebrationBanner');
            if (scenario === 'day90') {
                banner.classList.add('active');
                triggerConfetti();
            } else {
                banner.classList.remove('active');
            }
            
            renderScenario();
        }
        
        function renderScenario() {
            const container = document.getElementById('mainContent');
            const user = demoData.currentUser;
            
            switch(demoData.currentScenario) {
                case 'day1':
                    container.innerHTML = renderDay1(user);
                    break;
                case 'day30':
                    container.innerHTML = renderDay30(user);
                    setTimeout(() => renderWeightChart(user), 100);
                    break;
                case 'day90':
                    container.innerHTML = renderDay90(user);
                    setTimeout(() => renderWeightChart(user), 100);
                    break;
                case 'workouts':
                    container.innerHTML = renderWorkouts();
                    break;
                case 'avatars':
                    container.innerHTML = renderAvatars(user);
                    break;
            }
        }
        
        function renderDay1(user) {
            return `
                <div class="day1-content">
                    <div class="welcome-message">
                        <h2>Welcome to Your Transformation Journey!</h2>
                        <p>Let's set up your profile and create your first 3D avatar. This takes just 2 minutes.</p>
                    </div>
                    
                    <div class="onboarding-steps">
                        <div class="step-card" onclick="alert('Demo: Photo upload would open camera/gallery')">
                            <div class="step-number">1</div>
                            <h3>📸 Take Photos</h3>
                            <p>Front, side, and back photos in good lighting</p>
                        </div>
                        <div class="step-card" onclick="alert('Demo: Body analysis with AI')">
                            <div class="step-number">2</div>
                            <h3>🔍 AI Analysis</h3>
                            <p>Our AI analyzes your body composition</p>
                        </div>
                        <div class="step-card" onclick="alert('Demo: Avatar generation')">
                            <div class="step-number">3</div>
                            <h3>👤 Get Your Avatar</h3>
                            <p>See your 3D model come to life</p>
                        </div>
                    </div>
                    
                    <div class="dashboard-card" style="margin-top: 40px;">
                        <h2>🎯 Your Starting Point</h2>
                        <div class="journey-stats" style="margin-top: 20px;">
                            <div class="stat-item">
                                <div class="stat-value">${user.journey.startWeight}</div>
                                <div class="stat-label">Starting Weight</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${user.stats.startBodyFat}%</div>
                                <div class="stat-label">Body Fat</div>
                            </div>
                            <div class="stat-item">
                                <div class="stat-value">${user.stats.startMuscle}</div>
                                <div class="stat-label">Muscle Mass</div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 30px; text-align: center;">
                            <button class="btn btn-primary" style="font-size: 18px; padding: 15px 40px;"
                                    onclick="alert('Demo: Starting onboarding flow...')">
                                Start Your Journey →
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function renderDay30(user) {
            const photoBefore = user.photos[0];
            const photoAfter = user.photos[1];
            
            return `
                <div class="dashboard-grid">
                    <div class="dashboard-card">
                        <h2>📊 Weight Progress (30 Days)</h2>
                        <div class="chart-container">
                            <canvas id="weightChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="dashboard-card">
                        <h2>👤 Your 3D Avatar</h2>
                        <div class="avatar-section">
                            <div class="avatar-container">
                                <div class="avatar-3d" id="avatar3d">
                                    <div class="avatar-muscles"></div>
                                </div>
                            </div>
                            <div class="avatar-slider">
                                <input type="range" min="0" max="100" value="33" 
                                       oninput="updateAvatarMorph(this.value)">
                                <div class="slider-labels">
                                    <span>Start</span>
                                    <span>Current</span>
                                    <span>Goal</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <h2>📸 30-Day Progress Comparison</h2>
                    <div class="photo-compare" style="position: relative;">
                        <div class="photo-box">
                            <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1e1b4b, #312e81);">
                                <div style="text-align: center;">
                                    <div style="font-size: 60px; margin-bottom: 10px;">👤</div>
                                    <div>Day 1 Photo</div>
                                </div>
                            </div>
                            <div class="photo-label">${photoBefore.label}</div>
                        </div>
                        <div class="vs-badge">VS</div>
                        <div class="photo-box">
                            <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #312e81, #6366f1);">
                                <div style="text-align: center;">
                                    <div style="font-size: 60px; margin-bottom: 10px;">💪</div>
                                    <div>Day 30 Photo</div>
                                </div>
                            </div>
                            <div class="photo-label">${photoAfter.label}</div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-card" style="margin-top: 30px;">
                    <h2>🏆 Milestones Reached</h2>
                    <div class="milestones-list" style="margin-top: 20px;">
                        ${user.milestones.slice(0, 2).map(m => `
                            <div class="milestone-item">
                                <div class="milestone-icon achieved">🎯</div>
                                <div class="milestone-info">
                                    <h4>${m.reward}</h4>
                                    <p>Achieved on ${m.achieved}</p>
                                </div>
                                <div class="milestone-date">✓</div>
                            </div>
                        `).join('')}
                        ${user.milestones.slice(2, 3).map(m => `
                            <div class="milestone-item">
                                <div class="milestone-icon pending">🔒</div>
                                <div class="milestone-info">
                                    <h4>${m.reward}</h4>
                                    <p>Keep going!</p>
                                </div>
                                <div class="milestone-date">...</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        function renderDay90(user) {
            const photoBefore = user.photos[0];
            const photoAfter = user.photos[user.photos.length - 1];
            
            return `
                <div class="dashboard-grid">
                    <div class="dashboard-card">
                        <h2>📊 Complete Weight Journey (90 Days)</h2>
                        <div class="chart-container">
                            <canvas id="weightChart"></canvas>
                        </div>
                    </div>
                    
                    <div class="dashboard-card">
                        <h2>🎉 Transformation Complete!</h2>
                        <div style="text-align: center; padding: 30px;">
                            <div style="font-size: 80px; margin-bottom: 20px;">🏆</div>
                            <h3 style="font-size: 28px; margin-bottom: 15px; color: #fbbf24;">
                                ${user.journey.totalLost > 0 ? user.journey.totalLost + ' lbs Lost!' : user.journey.totalGained + ' lbs Gained!'}
                            </h3>
                            <p style="color: rgba(255,255,255,0.7); margin-bottom: 25px;">
                                You crushed your goal in ${user.journey.duration}!
                            </p>
                            <div class="journey-stats" style="margin-top: 20px;">
                                <div class="stat-item">
                                    <div class="stat-value">${user.stats.workoutsCompleted}</div>
                                    <div class="stat-label">Workouts</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${user.stats.consistency}%</div>
                                    <div class="stat-label">Consistency</div>
                                </div>
                                <div class="stat-item">
                                    <div class="stat-value">${user.milestones.length}</div>
                                    <div class="stat-label">Milestones</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-card">
                    <h2>📸 Before & After</h2>
                    <div class="photo-compare" style="position: relative;">
                        <div class="photo-box">
                            <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #1e1b4b, #312e81);">
                                <div style="text-align: center;">
                                    <div style="font-size: 60px; margin-bottom: 10px;">👤</div>
                                    <div>Before</div>
                                </div>
                            </div>
                            <div class="photo-label">${photoBefore.label}</div>
                        </div>
                        <div class="vs-badge">VS</div>
                        <div class="photo-box">
                            <div style="width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #22c55e, #16a34a);">
                                <div style="text-align: center;">
                                    <div style="font-size: 60px; margin-bottom: 10px;">🎉</div>
                                    <div>After</div>
                                </div>
                            </div>
                            <div class="photo-label">${photoAfter.label}</div>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-card" style="margin-top: 30px;">
                    <h2>🏅 All Milestones Achieved</h2>
                    <div class="milestones-list" style="margin-top: 20px;">
                        ${user.milestones.map(m => `
                            <div class="milestone-item">
                                <div class="milestone-icon achieved">${m.reward.charAt(0)}</div>
                                <div class="milestone-info">
                                    <h4>${m.reward.substring(2)}</h4>
                                    <p>Achieved on ${m.achieved}</p>
                                </div>
                                <div class="milestone-date">✓</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="quick-actions">
                    <button class="action-btn" onclick="triggerCelebration()">
                        <h4>🎉 Share Progress</h4>
                        <p>Post your transformation to social media</p>
                    </button>
                    <button class="action-btn" onclick="alert('Demo: Setting new goals')">
                        <h4>🎯 Set New Goal</h4>
                        <p>Continue your fitness journey</p>
                    </button>
                    <button class="action-btn" onclick="alert('Demo: Exporting transformation report')">
                        <h4>📄 Export Report</h4>
                        <p>Download your complete journey data</p>
                    </button>
                </div>
            `;
        }
        
        function renderWorkouts() {
            return `
                <div class="dashboard-card">
                    <h2>💪 Preset Workout Programs</h2>
                    <p style="color: rgba(255,255,255,0.6); margin-bottom: 30px;">
                        Choose a program that fits your schedule and experience level
                    </p>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                        ${demoData.workouts.map(w => `
                            <div style="background: rgba(255,255,255,0.05); border-radius: 16px; padding: 25px; border: 2px solid rgba(255,255,255,0.1); transition: all 0.3s ease; cursor: pointer;"
                                 onmouseover="this.style.borderColor='#6366f1'" 
                                 onmouseout="this.style.borderColor='rgba(255,255,255,0.1)'"
                                 onclick="selectWorkoutProgram('${w.id}')">
                                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                                    <h3 style="font-size: 20px;">${w.name}</h3>
                                    <span style="background: ${w.difficulty === 'beginner' ? '#22c55e' : w.difficulty === 'intermediate' ? '#f59e0b' : '#ec4899'}; 
                                                 padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase;">
                                        ${w.difficulty}
                                    </span>
                                </div>
                                <p style="color: rgba(255,255,255,0.6); font-size: 14px; margin-bottom: 20px; line-height: 1.5;">
                                    ${w.description}
                                </p>
                                <div style="display: flex; gap: 15px; font-size: 13px; color: rgba(255,255,255,0.5);">
                                    <span>📅 ${w.daysPerWeek} days/week</span>
                                    <span>🏷️ ${w.category || 'strength'}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="dashboard-card" style="margin-top: 30px;">
                    <h2>📅 This Week's Schedule</h2>
                    <div class="workout-preview">
                        <div class="workout-day">
                            <div class="workout-day-info">
                                <h4>Monday</h4>
                                <p>Chest & Triceps - 60 min</p>
                            </div>
                            <span class="workout-status completed">✓ Completed</span>
                        </div>
                        <div class="workout-day">
                            <div class="workout-day-info">
                                <h4>Tuesday</h4>
                                <p>Back & Biceps - 55 min</p>
                            </div>
                            <span class="workout-status completed">✓ Completed</span>
                        </div>
                        <div class="workout-day">
                            <div class="workout-day-info">
                                <h4>Wednesday</h4>
                                <p>Rest Day</p>
                            </div>
                            <span class="workout-status completed">✓ Recovered</span>
                        </div>
                        <div class="workout-day">
                            <div class="workout-day-info">
                                <h4>Thursday</h4>
                                <p>Legs & Core - 65 min</p>
                            </div>
                            <span class="workout-status scheduled">⏰ Scheduled</span>
                        </div>
                        <div class="workout-day">
                            <div class="workout-day-info">
                                <h4>Friday</h4>
                                <p>Shoulders & Arms - 50 min</p>
                            </div>
                            <span class="workout-status scheduled">⏰ Scheduled</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function renderAvatars(user) {
            return `
                <div class="dashboard-grid">
                    <div class="dashboard-card">
                        <h2>👤 Avatar Evolution</h2>
                        <div class="avatar-section">
                            <div class="avatar-container" style="height: 400px;">
                                <div class="avatar-3d" id="avatar3d" style="width: 250px; height: 350px;">
                                    <div class="avatar-muscles" style="width: 200px; height: 120px;"></div>
                                </div>
                            </div>
                            <div class="avatar-slider">
                                <input type="range" min="0" max="100" value="50" 
                                       oninput="updateAvatarMorph(this.value, '${user.id}')">
                                <div class="slider-labels">
                                    <span>Day 1</span>
                                    <span style="color: #6366f1; font-weight: 600;">Drag to Morph →</span>
                                    <span>Goal</span>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="dashboard-card">
                        <h2>📊 Body Composition Changes</h2>
                        <div style="margin-top: 20px;">
                            <div style="margin-bottom: 25px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="color: rgba(255,255,255,0.7);">Body Fat</span>
                                    <span style="color: #22c55e; font-weight: 600;">
                                        ${user.stats.startBodyFat}% → ${user.stats.currentBodyFat}%
                                    </span>
                                </div>
                                <div style="background: rgba(255,255,255,0.1); height: 10px; border-radius: 5px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #ef4444, #22c55e); 
                                                width: ${(user.stats.startBodyFat - user.stats.currentBodyFat) / user.stats.startBodyFat * 100}%; 
                                                height: 100%; border-radius: 5px;"></div>
                                </div>
                            </div>
                            
                            <div style="margin-bottom: 25px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="color: rgba(255,255,255,0.7);">Muscle Mass</span>
                                    <span style="color: #22c55e; font-weight: 600;">
                                        ${user.stats.startMuscle} lbs → ${user.stats.currentMuscle} lbs
                                    </span>
                                </div>
                                <div style="background: rgba(255,255,255,0.1); height: 10px; border-radius: 5px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #6366f1, #22c55e); 
                                                width: ${user.stats.currentMuscle / user.stats.startMuscle * 100 - 100}%; 
                                                height: 100%; border-radius: 5px;"></div>
                                </div>
                            </div>
                            
                            <div>
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="color: rgba(255,255,255,0.7);">Overall Progress</span>
                                    <span style="color: #fbbf24; font-weight: 600;">100%</span>
                                </div>
                                <div style="background: rgba(255,255,255,0.1); height: 10px; border-radius: 5px; overflow: hidden;">
                                    <div style="background: linear-gradient(90deg, #6366f1, #ec4899); 
                                                width: 100%; height: 100%; border-radius: 5px;"></div>
                                </div>
                            </div>
                        </div>
                        
                        <div style="margin-top: 30px; padding: 20px; background: rgba(255,255,255,0.05); border-radius: 12px;">
                            <h4 style="margin-bottom: 10px;">🎯 SMPL Parameters</h4>
                            <p style="font-size: 13px; color: rgba(255,255,255,0.6); line-height: 1.6;">
                                Shape parameters automatically adjusted based on your progress photos. 
                                The avatar morphs in real-time as you log weight and body measurements.
                            </p>
                        </div>
                    </div>
                </div>
                
                <div class="dashboard-card" style="margin-top: 30px;">
                    <h2>🎬 Avatar Comparison Grid</h2>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">
                        ${user.photos.map((photo, i) => `
                            <div style="text-align: center;">
                                <div style="background: rgba(255,255,255,0.05); border-radius: 16px; padding: 20px; aspect-ratio: 3/4; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                                    <div style="font-size: 60px;">
                                        ${i === 0 ? '👤' : i === user.photos.length - 1 ? '💪' : '📊'}
                                    </div>
                                </div>
                                <p style="font-size: 14px; font-weight: 600;">${photo.label}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `;
        }
        
        function renderWeightChart(user) {
            const ctx = document.getElementById('weightChart');
            if (!ctx) return;
            
            const labels = user.weightHistory.map(h => {
                const date = new Date(h.date);
                return `${date.getMonth() + 1}/${date.getDate()}`;
            });
            
            const data = user.weightHistory.map(h => h.weight);
            
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Weight (lbs)',
                        data: data,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#6366f1',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            grid: {
                                color: 'rgba(255,255,255,0.1)'
                            },
                            ticks: {
                                color: 'rgba(255,255,255,0.6)'
                            }
                        },
                        x: {
                            grid: {
                                display: false
                            },
                            ticks: {
                                color: 'rgba(255,255,255,0.6)'
                            }
                        }
                    }
                }
            });
        }
        
        function updateAvatarMorph(value, userId) {
            const avatar = document.getElementById('avatar3d');
            if (avatar) {
                const scale = 1 + (value / 1000);
                const opacity = 0.8 + (value / 500);
                avatar.style.transform = `scale(${scale})`;
                avatar.style.opacity = opacity;
            }
        }
        
        function selectWorkoutProgram(programId) {
            alert(`Demo: Selected ${programId} program. In production, this would load the full workout plan.`);
        }
        
        // Confetti Effect
        function triggerCelebration() {
            triggerConfetti();
            const banner = document.getElementById('celebrationBanner');
            banner.classList.add('active');
            setTimeout(() => banner.classList.remove('active'), 5000);
        }
        
        function triggerConfetti() {
            const canvas = document.getElementById('confetti-canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            
            const confetti = [];
            const colors = ['#6366f1', '#ec4899', '#22c55e', '#f59e0b', '#8b5cf6'];
            
            for (let i = 0; i < 150; i++) {
                confetti.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height - canvas.height,
                    size: Math.random() * 10 + 5,
                    color: colors[Math.floor(Math.random() * colors.length)],
                    speed: Math.random() * 3 + 2,
                    rotation: Math.random() * 360,
                    rotationSpeed: Math.random() * 10 - 5
                });
            }
            
            let animationId;
            function animate() {
                ctx.clearRect(0, 0, canvas.width, canvas.height);
                
                confetti.forEach((c, i) => {
                    c.y += c.speed;
                    c.rotation += c.rotationSpeed;
                    
                    ctx.save();
                    ctx.translate(c.x, c.y);
                    ctx.rotate(c.rotation * Math.PI / 180);
                    ctx.fillStyle = c.color;
                    ctx.fillRect(-c.size/2, -c.size/2, c.size, c.size);
                    ctx.restore();
                    
                    if (c.y > canvas.height) {
                        c.y = -20;
                        c.x = Math.random() * canvas.width;
                    }
                });
                
                animationId = requestAnimationFrame(animate);
            }
            
            animate();
            
            // Stop after 5 seconds
            setTimeout(() => {
                cancelAnimationFrame(animationId);
                ctx.clearRect(0, 0, canvas.width, canvas.height);
            }, 5000);
        }
        
        function resetDemo() {
            demoData.currentUser = demoData.users[0];
            demoData.currentScenario = 'day1';
            document.getElementById('celebrationBanner').classList.remove('active');
            
            document.querySelectorAll('.scenario-tab').forEach((tab, i) => {
                tab.classList.toggle('active', i === 0);
            });
            
            renderUserSelector();
            renderScenario();
        }
        
        function exportDemoData() {
            const dataStr = JSON.stringify(demoData.users, null, 2);
            const dataBlob = new Blob([dataStr], {type: 'application/json'});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'physiqai-demo-data.json';
            link.click();
        }
        
        // Initialize on load
        window.onload = loadDemoData;
        
        // Handle resize for canvas
        window.addEventListener('resize', () => {
            const canvas = document.getElementById('confetti-canvas');
            if (canvas) {
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }
        });
    </script>
</body>
</html>
