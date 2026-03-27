# PhysiqAI Integration System

## Overview

The PhysiqAI Integration System connects all app features using an **event-driven architecture**. When you perform any action, it triggers a chain of updates across the entire application.

## Architecture

```
User Action → Event Bus → Data Store → Recalculation → UI Update
```

## Core Components

### 1. Event Bus (`physiqBus`)
Central message broker for all communication:
- `subscribe(event, callback)` - Listen for events
- `emit(event, data)` - Broadcast events

### 2. Data Store (`physiqStore`)
Centralized state management using localStorage:
- Automatic persistence
- Change subscriptions
- Cross-page data sharing

### 3. Integration Classes

#### WeightIntegration
- Logs weight entries
- Calculates streaks
- Triggers avatar morphing
- Checks milestones

#### WorkoutIntegration
- Saves workout plans
- Generates body predictions
- Creates workout insights

#### PhotoIntegration
- Manages photo uploads
- Updates timeline
- Triggers body analysis

#### AvatarIntegration
- Morphs 3D avatar based on weight
- Animates transitions
- Syncs with weight changes

#### DashboardIntegration
- Real-time widget updates
- Progress calculations
- Milestone celebrations

## Data Flow

### Weight Logged
```javascript
// 1. User logs weight
PhysiqIntegration.logWeight(170, '2026-02-23', 'Feeling great!');

// 2. Events triggered:
//    - weight:logged
//    - data:weight (auto)
//    - progress:updated
//    - avatar:morph
//    - insights:generated
//    - prediction:update
```

### Workout Saved
```javascript
// 1. User saves workout
PhysiqIntegration.saveWorkout({
    name: 'Push Day',
    exercises: [...]
});

// 2. Events triggered:
//    - workout:saved
//    - prediction:generated
//    - insights:generated
```

### Photo Uploaded
```javascript
// 1. User uploads photo
PhysiqIntegration.uploadPhoto({
    src: 'data:image/...',
    date: '2026-02-23',
    type: 'front'
});

// 2. Events triggered:
//    - photo:uploaded
//    - timeline:updated
//    - insights:generated
```

## Files

| File | Purpose |
|------|---------|
| `integration.js` | Core integration layer |
| `index-integrated.html` | Home page with live stats |
| `weight-tracker-integrated.html` | Weight logging with event emission |
| `avatar-integrated.html` | 3D avatar with live morphing |
| `dashboard-integrated.html` | Dashboard with real data |

## Usage

### In HTML
```html
<script src="integration.js"></script>
<script>
    // Access global instances
    physiqBus.subscribe('weight:logged', (data) => {
        console.log('Weight logged:', data.weight);
    });
    
    // Log weight (triggers all connected updates)
    PhysiqIntegration.logWeight(170);
</script>
```

### Available Events

| Event | Data | Description |
|-------|------|-------------|
| `weight:logged` | `{weight, date, entry}` | New weight entry |
| `weight:updated` | `entry` | Weight entry updated |
| `workout:saved` | `workout` | New workout saved |
| `photo:uploaded` | `photo` | Photo uploaded |
| `avatar:morph` | `{level, progress}` | Avatar morph level |
| `progress:updated` | `progress` | Progress recalculated |
| `milestone:achieved` | `{weight}` | Milestone hit |
| `insights:generated` | `{insights}` | New insights |
| `timeline:updated` | `{photos}` | Timeline changed |

## Storage Keys

All data stored in localStorage:
- `weight_tracker_data_v1` - Weight entries, goals, milestones
- `weight_tracker_settings_v1` - User settings
- `physiq_workouts_v1` - Saved workouts
- `physiq_photos_v1` - Uploaded photos
- `physiq_predictions_v1` - Body predictions
- `physiq_insights_v1` - Generated insights
- `physiq_avatar_state_v1` - Avatar morph state

## Getting Started

1. Open `index-integrated.html`
2. Navigate to Weight Tracker
3. Log your first weight entry
4. Watch the dashboard and avatar update automatically
5. Upload photos and save workouts to see the full integration

## Connected Features

✅ Weight logged → Avatar weight display updates  
✅ Workout saved → Body prediction generated  
✅ Photo uploaded → Shows in timeline  
✅ Dashboard shows real data (not mock)  
✅ Avatar morphs based on weight change  
✅ Progress calculated from actual history  
✅ Insights generated from real patterns