#!/usr/bin/env python3
"""
PhysiqAI Demo Data Validator & Report Generator
Run this to verify all demo data is properly formatted
"""

import json
import os
from datetime import datetime

def load_json(filepath):
    """Load and parse JSON file"""
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        return {'error': str(e)}

def validate_demo_data():
    """Validate all demo data files"""
    demo_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print("PHYSIQAI DEMO DATA VALIDATION")
    print("=" * 60)

    # Load files
    users_file = os.path.join(demo_dir, 'demo-users.json')
    workouts_file = os.path.join(demo_dir, 'workout-presets.json')
    history_file = os.path.join(demo_dir, 'workout-history.json')

    users_data = load_json(users_file)
    workouts_data = load_json(workouts_file)
    history_data = load_json(history_file)

    # Validate users
    print("\n📊 DEMO USERS")
    print("-" * 60)
    if 'demoUsers' in users_data:
        for user in users_data['demoUsers']:
            journey = user.get('journey', {})
            stats = user.get('stats', {})
            history = user.get('weightHistory', [])

            print(f"\n👤 {user.get('name', 'Unknown')}")
            print(f"   Journey: {journey.get('title', 'N/A')}")
            print(f"   Progress: {journey.get('startWeight', 0)} → {journey.get('currentWeight', 0)} lbs")
            print(f"   Body Fat: {stats.get('startBodyFat', 0)}% → {stats.get('currentBodyFat', 0)}%")
            print(f"   Muscle: {stats.get('startMuscle', 0)} → {stats.get('currentMuscle', 0)} lbs")
            print(f"   Workouts: {stats.get('workoutsCompleted', 0)} ({stats.get('consistency', 0)}% consistent)")
            print(f"   Data Points: {len(history)} weight entries")
            print(f"   Milestones: {len(user.get('milestones', []))} achieved")
    else:
        print("   ❌ Error loading users:", users_data.get('error', 'Unknown'))

    # Validate workouts
    print("\n\n💪 WORKOUT PROGRAMS")
    print("-" * 60)
    if 'workoutPresets' in workouts_data:
        for workout in workouts_data['workoutPresets']:
            schedule = workout.get('schedule', [])
            print(f"\n📋 {workout.get('name', 'Unknown')}")
            print(f"   Difficulty: {workout.get('difficulty', 'N/A').upper()}")
            print(f"   Days/Week: {workout.get('daysPerWeek', 0)}")
            print(f"   Category: {workout.get('category', 'N/A')}")
            print(f"   Workout Days: {len([d for d in schedule if d.get('exercises')])}")
            total_exercises = sum(len(day.get('exercises', [])) for day in schedule)
            print(f"   Total Exercises: {total_exercises}")
    else:
        print("   ❌ Error loading workouts:", workouts_data.get('error', 'Unknown'))

    # Validate workout history
    print("\n\n📈 WORKOUT HISTORY")
    print("-" * 60)
    if 'userWorkouts' in history_data:
        for user_id, data in history_data['userWorkouts'].items():
            print(f"\n🎯 {user_id}")
            print(f"   Program: {data.get('currentProgram', 'N/A')}")
            print(f"   Total Workouts: {data.get('totalWorkouts', 0)}")
            print(f"   Current Streak: {data.get('streak', 0)} days")
            print(f"   Personal Records: {len(data.get('personalRecords', []))}")
    else:
        print("   ❌ Error loading history:", history_data.get('error', 'Unknown'))

    # Summary
    print("\n\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_users = len(users_data.get('demoUsers', []))
    total_workouts = len(workouts_data.get('workoutPresets', []))

    print(f"\n✅ Demo Users: {total_users}")
    print(f"✅ Workout Programs: {total_workouts}")
    print(f"✅ Demo HTML: {'demo-showcase.html exists' if os.path.exists(os.path.join(demo_dir, 'demo-showcase.html')) else 'MISSING'}")
    print(f"✅ Demo Ready: {'YES' if total_users >= 3 and total_workouts >= 5 else 'INCOMPLETE'}")

    print("\n🚀 To run the demo:")
    print(f"   Open: {os.path.join(demo_dir, 'demo-showcase.html')}")
    print("\n")

if __name__ == '__main__':
    validate_demo_data()
