# PhysiqAI Demo Showcase

## 🎯 Quick Start (2-Minute Demo)

Open `demo-showcase.html` in a browser to experience the full interactive demo.

```bash
cd /home/clawd/.openclaw/workspace/projects/physiqai/demo
open demo-showcase.html  # macOS
# OR
xdg-open demo-showcase.html  # Linux
# OR simply double-click the file
```

## 📁 Demo Files

| File | Description |
|------|-------------|
| `demo-showcase.html` | **Main interactive demo** - Click through scenarios |
| `demo-users.json` | 3 demo users with complete data |
| `workout-presets.json` | 5 workout programs (PPL, Upper/Lower, Bro Split, etc.) |
| `workout-history.json` | Sample workout logs for each user |

## 👥 Demo Users

### User A: Alex Johnson - Weight Loss Journey
- **Goal**: 200 lbs → 170 lbs (3 months)
- **Result**: ✅ -30 lbs, -8.3% body fat
- **Workouts**: 52 completed, 89% consistency
- **Best for**: Showing weight loss transformation

### User B: Sarah Chen - Muscle Building Journey
- **Goal**: 150 lbs → 165 lbs (6 months lean bulk)
- **Result**: ✅ +15 lbs, +7.3 lbs muscle
- **Workouts**: 112 completed, 93% consistency
- **Best for**: Showing muscle gain progress

### User C: Marcus Williams - Body Recomposition
- **Goal**: Maintain 180 lbs, lose fat & gain muscle
- **Result**: ✅ -8% body fat, +6.2 lbs muscle
- **Workouts**: 128 completed, 95% consistency
- **Best for**: Showing recomposition (highest consistency)

## 🎬 Demo Scenarios

### 1. Day 1: Getting Started
- User onboarding flow
- Starting measurements display
- Step-by-step avatar creation preview

### 2. Day 30: Progress Check
- Weight trend charts (Chart.js)
- Side-by-side photo comparison
- Milestone tracking
- Interactive avatar morph slider

### 3. Day 90: Goal Reached
- 🎉 Celebration animation with confetti
- Complete transformation summary
- All milestones achieved
- Export/share options

### 4. Workout Programs
- 5 preset programs:
  - **PPL** (6 days) - Intermediate
  - **Upper/Lower** (4 days) - Beginner
  - **Bro Split** (5 days) - Intermediate
  - **Full Body** (3 days) - Beginner
  - **PHAT** (5 days) - Advanced

### 5. Avatar Evolution
- Real-time avatar morphing
- Body composition progress bars
- SMPL parameter visualization

## ✨ Interactive Features

### User Switching
Click any user card to switch between the 3 demo profiles and see their unique journeys.

### Avatar Morphing
Drag the slider to morph between start and goal body states in real-time.

### Celebration Animation
Click "🎉 Celebrate" button or view Day 90 scenario to trigger confetti animation.

### Data Export
Click "⬇ Export" to download demo user data as JSON.

## 📊 Data Included

### Weight History
- 45-90 days of daily weigh-ins
- Realistic fluctuations (±1-2 lbs)
- Body fat % and muscle mass tracking

### Milestones
- Automatic milestone detection
- Celebration triggers at goal weights
- Visual progress indicators

### Workouts
- 3-6 workouts per week per user
- Volume and duration tracking
- Consistency percentages

## 🎨 Visual Features

- **Dark theme** with gradient backgrounds
- **Smooth animations** (breathe effect on avatars)
- **Professional charts** via Chart.js
- **Responsive design** for mobile/tablet
- **Glassmorphism** UI elements
- **Confetti celebration** effects

## 🔧 Technical Details

- Pure HTML/CSS/JavaScript - no build step required
- Chart.js for data visualization
- Canvas API for confetti animation
- Local JSON data storage
- Fully self-contained (works offline)

## 🚀 For BZ's Demo

1. **Open** `demo-showcase.html`
2. **Click** through the 5 scenario tabs at top
3. **Switch** between 3 user cards to see different journeys
4. **Try** the avatar slider in Day 30/90 scenarios
5. **Click** "🎉 Celebrate" to see confetti
6. **Export** data to show JSON structure

**Total time**: ~2 minutes to experience everything
