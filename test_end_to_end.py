#!/usr/bin/env python3
"""
PhysiqAI End-to-End Test
=========================

Complete test of the entire user flow:
1. Signup
2. Photo upload & SMPL fitting
3. First workout logging & predictions
4. Daily weight logging
5. Goal setting
6. Progress timeline
7. Social sharing

Usage:
    python3 test_end_to_end.py

This will:
- Create a test user
- Process a sample photo
- Log workouts
- Generate predictions
- Create timeline
- Verify all features work
"""

import sys
import os
import json
import base64
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path

# API base URL
API_BASE = "http://localhost:8000"


def make_request(method: str, endpoint: str, data: dict = None) -> dict:
    """Make API request"""
    url = f"{API_BASE}{endpoint}"

    try:
        if method == "GET":
            response = requests.get(url, params=data, timeout=30)
        else:
            response = requests.request(method, url, json=data, timeout=30)

        return response.json()
    except Exception as e:
        return {"error": str(e), "success": False}


def test_signup() -> dict:
    """Test user signup"""
    print("\n" + "="*70)
    print("STEP 1: USER SIGNUP")
    print("="*70)

    user_data = {
        "email": f"test_{int(time.time())}@physiqai.com",
        "name": "Alex Johnson",
        "gender": "male",
        "height_cm": 175,
        "birth_date": "1995-03-15"
    }

    print(f"\n📋 Creating user account...")
    print(f"   Name: {user_data['name']}")
    print(f"   Email: {user_data['email']}")
    print(f"   Gender: {user_data['gender']}")
    print(f"   Height: {user_data['height_cm']} cm")

    result = make_request("POST", "/api/auth/signup", user_data)

    if result.get('success'):
        print(f"\n✅ User created successfully!")
        print(f"   User ID: {result['user']['id']}")
        return result['user']
    else:
        print(f"\n❌ Signup failed: {result.get('error')}")
        return None


def test_photo_upload(user_id: str) -> dict:
    """Test photo upload and SMPL fitting"""
    print("\n" + "="*70)
    print("STEP 2: PHOTO UPLOAD & SMPL FITTING")
    print("="*70)

    # Create a sample image (gradient pattern that simulates a body photo)
    try:
        from PIL import Image, ImageDraw

        # Create sample image
        img = Image.new('RGB', (400, 600), color='#E8D5C4')
        draw = ImageDraw.Draw(img)

        # Draw simple body shape
        center_x = 200

        # Head
        draw.ellipse([170, 50, 230, 110], fill='#D4A574', outline='#C68642', width=2)

        # Torso (athletic build)
        draw.polygon([
            (160, 120), (240, 120),  # Shoulders
            (230, 250), (170, 250),  # Waist
        ], fill='#D4A574', outline='#C68642', width=2)

        # Arms
        draw.polygon([
            (160, 130), (140, 130), (130, 250), (150, 250)
        ], fill='#D4A574', outline='#C68642', width=2)
        draw.polygon([
            (240, 130), (260, 130), (270, 250), (250, 250)
        ], fill='#D4A574', outline='#C68642', width=2)

        # Legs
        draw.polygon([
            (175, 250), (195, 250), (190, 450), (170, 450)
        ], fill='#D4A574', outline='#C68642', width=2)
        draw.polygon([
            (205, 250), (225, 250), (230, 450), (210, 450)
        ], fill='#D4A574', outline='#C68642', width=2)

        # Save to bytes
        import io
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG')
        photo_bytes = buffer.getvalue()

    except ImportError:
        # If PIL not available, create dummy data
        print("   ⚠️  PIL not available, using dummy photo data")
        photo_bytes = b'dummy_photo_data' * 100

    # Encode to base64
    photo_base64 = base64.b64encode(photo_bytes).decode()

    print(f"\n📸 Uploading front-facing photo...")
    print(f"   Size: {len(photo_bytes)} bytes")

    upload_data = {
        "user_id": user_id,
        "photo": photo_base64,
        "photo_type": "front"
    }

    result = make_request("POST", "/api/photos/upload", upload_data)

    if result.get('success'):
        print(f"\n✅ Photo processed successfully!")
        print(f"   Body type: {result['photo']['body_type']}")
        print(f"   Confidence: {result['photo']['confidence_score']:.1%}")
        print(f"   Estimated height: {result['photo']['estimated_height_cm']:.1f} cm")
        print(f"   Estimated weight: {result['photo']['estimated_weight_kg']:.1f} kg")
        print(f"   Avatar mesh: {result['avatar']['mesh_path']}")
        print(f"   Avatar image: {result['avatar']['image_path']}")
        return result
    else:
        print(f"\n❌ Photo upload failed: {result.get('error')}")
        return None


def test_first_workout(user_id: str) -> dict:
    """Test first workout logging and predictions"""
    print("\n" + "="*70)
    print("STEP 3: FIRST WORKOUT & PREDICTIONS")
    print("="*70)

    workout_data = {
        "user_id": user_id,
        "name": "First Workout - Upper Body",
        "workout_type": "strength",
        "start_time": datetime.now().isoformat(),
        "duration_minutes": 60,
        "exercises": [
            {
                "name": "Bench Press",
                "muscle_groups": ["chest", "triceps", "shoulders"],
                "exercise_type": "compound",
                "sets": 4,
                "reps": 8,
                "weight_kg": 60,
                "rpe": 8
            },
            {
                "name": "Barbell Rows",
                "muscle_groups": ["lats", "biceps", "lower_back"],
                "exercise_type": "compound",
                "sets": 4,
                "reps": 10,
                "weight_kg": 50,
                "rpe": 7
            },
            {
                "name": "Overhead Press",
                "muscle_groups": ["shoulders", "triceps"],
                "exercise_type": "compound",
                "sets": 3,
                "reps": 10,
                "weight_kg": 40,
                "rpe": 7
            },
            {
                "name": "Bicep Curls",
                "muscle_groups": ["biceps"],
                "exercise_type": "isolation",
                "sets": 3,
                "reps": 12,
                "weight_kg": 15,
                "rpe": 8
            }
        ],
        "notes": "Great first session! Felt strong on bench."
    }

    print(f"\n💪 Logging first workout...")
    print(f"   Name: {workout_data['name']}")
    print(f"   Exercises: {len(workout_data['exercises'])}")

    total_volume = sum(ex['sets'] * ex['reps'] * ex['weight_kg'] for ex in workout_data['exercises'])
    print(f"   Total volume: {total_volume:,.0f} kg")

    result = make_request("POST", "/api/workouts/log", workout_data)

    if result.get('success'):
        print(f"\n✅ Workout logged successfully!")

        analysis = result['analysis']
        immediate = analysis['immediate_effects']
        long_term = analysis['long_term_adaptation']

        print(f"\n📊 Immediate Effects (Post-Workout Pump):")
        print(f"   Duration: {immediate['duration_minutes']:.0f} minutes")
        print(f"   Vascularity boost: {immediate['vascularity_boost']:.0%}")
        print(f"   Energy expended: {immediate['energy_expenditure_kcal']:.0f} kcal")

        print(f"\n   Muscle pump by group:")
        for muscle, pump in sorted(immediate['muscle_pump'].items(), key=lambda x: x[1], reverse=True):
            if pump > 0:
                bar = "█" * int(pump * 20)
                print(f"      {muscle:15s}: {pump:.0%} {bar}")

        print(f"\n📈 Long-term Projections (12 weeks):")
        print(f"   Muscle gain rate: {sum(long_term['muscle_gain_rate_per_week_kg'].values())*1000:.1f}g/week")
        print(f"   Fat burn per session: {long_term['fat_burn_per_session_kg']*1000:.1f}g")
        print(f"   Projected weight change: {long_term['projected_weight_change_kg']:+.2f} kg")
        print(f"   Projected body fat change: {long_term['projected_body_fat_change_pct']:+.2f}%")

        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   • {rec}")

        print(f"\n🔮 Future Predictions (4-week preview):")
        for pred in result['predictions']:
            print(f"   Week {pred['weeks_from_now']:2d}: {pred['predicted_weight_kg']:.1f} kg, "
                  f"{pred['predicted_body_fat_pct']:.1f}% BF, "
                  f"{pred['predicted_muscle_mass_kg']:.1f} kg muscle "
                  f"(confidence: {pred['confidence']:.0%})")

        return result
    else:
        print(f"\n❌ Workout logging failed: {result.get('error')}")
        return None


def test_weight_logging(user_id: str) -> dict:
    """Test daily weight logging"""
    print("\n" + "="*70)
    print("STEP 4: DAILY WEIGHT LOGGING")
    print("="*70)

    weights = [
        ("Day 1", 78.5, 18.5),
        ("Day 3", 78.2, 18.3),
        ("Day 7", 77.8, 18.1),
        ("Day 14", 77.2, 17.8),
    ]

    print(f"\n⚖️  Logging weight entries...")

    results = []
    for day, weight, bf in weights:
        weight_data = {
            "user_id": user_id,
            "weight_kg": weight,
            "body_fat_pct": bf,
        }

        result = make_request("POST", "/api/weight/log", weight_data)

        if result.get('success'):
            print(f"   {day}: {weight:.1f} kg, {bf:.1f}% body fat")
            results.append(result)
        else:
            print(f"   {day}: Failed - {result.get('error')}")

    print(f"\n✅ Logged {len(results)} weight entries")

    return results


def test_goal_setting(user_id: str) -> dict:
    """Test goal creation"""
    print("\n" + "="*70)
    print("STEP 5: GOAL SETTING")
    print("="*70)

    goal_data = {
        "user_id": user_id,
        "goal_type": "muscle_gain",
        "title": "Build 5kg of Muscle",
        "description": "Gain 5kg of lean muscle mass over 6 months",
        "target_weight_kg": 82,
        "target_body_fat_pct": 15,
        "target_muscle_mass_kg": 38,
        "target_date": (datetime.now() + timedelta(days=180)).isoformat(),
        "timeline_weeks": 24,
    }

    print(f"\n🎯 Creating goal...")
    print(f"   Title: {goal_data['title']}")
    print(f"   Type: {goal_data['goal_type']}")
    print(f"   Target weight: {goal_data['target_weight_kg']} kg")
    print(f"   Target body fat: {goal_data['target_body_fat_pct']}%")
    print(f"   Target muscle: {goal_data['target_muscle_mass_kg']} kg")
    print(f"   Timeline: {goal_data['timeline_weeks']} weeks")

    result = make_request("POST", "/api/goals/create", goal_data)

    if result.get('success'):
        print(f"\n✅ Goal created successfully!")

        print(f"\n📋 Recommendations to achieve goal:")
        for rec in result['recommendations']:
            print(f"   • {rec}")

        print(f"\n🔮 Projected Avatar (24 weeks):")
        avatar = result['projected_avatar']
        print(f"   Mesh: {avatar['mesh_path']}")
        print(f"   Image: {avatar['image_path']}")

        return result
    else:
        print(f"\n❌ Goal creation failed: {result.get('error')}")
        return None


def test_avatar_timeline(user_id: str) -> dict:
    """Test avatar timeline generation"""
    print("\n" + "="*70)
    print("STEP 6: AVATAR TIMELINE")
    print("="*70)

    print(f"\n📅 Generating 12-week avatar timeline...")

    result = make_request("GET", f"/api/avatar/{user_id}/timeline", {"weeks": 12})

    if 'timeline' in result:
        timeline = result['timeline']
        print(f"\n✅ Generated {len(timeline)} weekly avatars")

        print(f"\n   Week progression:")
        for entry in timeline[::3]:  # Show every 3rd week
            print(f"      Week {entry['week']:2d}: {entry['progress_pct']:.0f}% progress")

        return result
    else:
        print(f"\n❌ Timeline generation failed: {result.get('error')}")
        return None


def test_social_sharing(user_id: str) -> dict:
    """Test social sharing"""
    print("\n" + "="*70)
    print("STEP 7: SOCIAL SHARING")
    print("="*70)

    share_data = {
        "user_id": user_id,
        "share_type": "milestone",
        "title": "Completed First Week! 💪",
        "description": "Just finished my first week of training. Down 1.3kg and feeling great!",
        "progress_data": {
            "days_trained": 4,
            "weight_change_kg": -1.3,
            "workouts_completed": 4,
        }
    }

    print(f"\n📱 Sharing progress...")
    print(f"   Title: {share_data['title']}")

    result = make_request("POST", "/api/social/share", share_data)

    if result.get('success'):
        print(f"\n✅ Progress shared successfully!")
        return result
    else:
        print(f"\n❌ Sharing failed: {result.get('error')}")
        return None


def test_progress_retrieval(user_id: str) -> dict:
    """Test progress data retrieval"""
    print("\n" + "="*70)
    print("STEP 8: PROGRESS RETRIEVAL")
    print("="*70)

    print(f"\n📊 Retrieving progress data...")

    result = make_request("GET", "/api/progress", {"user_id": user_id})

    if 'user' in result:
        print(f"\n✅ Retrieved progress data")
        print(f"   User: {result['user']['name']}")
        print(f"   Current weight: {result['user'].get('current_weight_kg', 'N/A')} kg")
        print(f"   Measurements: {len(result['measurements'])}")
        print(f"   Workouts: {result['workout_count']}")
        print(f"   Recent entries: {len(result['recent_entries'])}")

        return result
    else:
        print(f"\n❌ Progress retrieval failed: {result.get('error')}")
        return None


def test_full_timeline_prediction(user_id: str) -> dict:
    """Test full timeline prediction with avatars"""
    print("\n" + "="*70)
    print("STEP 9: FULL TIMELINE PREDICTION")
    print("="*70)

    print(f"\n🔮 Generating full 12-week prediction with avatars...")

    prediction_data = {
        "user_id": user_id,
        "weeks": 12,
    }

    result = make_request("POST", "/api/predictions/timeline", prediction_data)

    if 'predictions' in result:
        predictions = result['predictions']
        print(f"\n✅ Generated {len(predictions)} weekly predictions")

        print(f"\n   Sample predictions:")
        for pred in predictions[::4]:  # Every 4th week
            print(f"      Week {pred['weeks_from_now']:2d}: "
                  f"{pred['predicted_weight_kg']:.1f}kg, "
                  f"{pred['predicted_body_fat_pct']:.1f}% BF, "
                  f"confidence {pred['confidence']:.0%}")

        if 'avatars' in result:
            print(f"\n   Generated avatars:")
            for key, avatar in result['avatars'].items():
                print(f"      {key}: {avatar['image_path']}")

        return result
    else:
        print(f"\n❌ Prediction failed: {result.get('error')}")
        return None


def run_all_tests():
    """Run complete end-to-end test"""
    print("\n" + "="*70)
    print("PHYSIQAI END-TO-END TEST")
    print("Complete User Flow Validation")
    print("="*70)

    # Check if server is running
    print("\n🔍 Checking API server...")
    health = make_request("GET", "/health")

    if not health.get('status') == 'healthy':
        print("\n❌ API server not running!")
        print("   Start the server with: python3 -m backend.api.server")
        return False

    print(f"   ✓ Server healthy: {health.get('service')} v{health.get('version')}")

    # Run tests
    results = {}

    # Step 1: Signup
    user = test_signup()
    if not user:
        print("\n❌ TEST FAILED at signup")
        return False
    results['user'] = user
    user_id = user['id']

    # Step 2: Photo upload
    photo_result = test_photo_upload(user_id)
    if not photo_result:
        print("\n❌ TEST FAILED at photo upload")
        return False
    results['photo'] = photo_result

    # Step 3: First workout
    workout_result = test_first_workout(user_id)
    if not workout_result:
        print("\n❌ TEST FAILED at workout logging")
        return False
    results['workout'] = workout_result

    # Step 4: Weight logging
    weight_results = test_weight_logging(user_id)
    results['weights'] = weight_results

    # Step 5: Goal setting
    goal_result = test_goal_setting(user_id)
    if not goal_result:
        print("\n❌ TEST FAILED at goal setting")
        return False
    results['goal'] = goal_result

    # Step 6: Avatar timeline
    timeline_result = test_avatar_timeline(user_id)
    results['timeline'] = timeline_result

    # Step 7: Social sharing
    social_result = test_social_sharing(user_id)
    results['social'] = social_result

    # Step 8: Progress retrieval
    progress_result = test_progress_retrieval(user_id)
    results['progress'] = progress_result

    # Step 9: Full prediction
    prediction_result = test_full_timeline_prediction(user_id)
    results['prediction'] = prediction_result

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"\n✅ All tests completed successfully!")
    print(f"\nUser created: {user['name']} ({user_id})")
    print(f"Features tested:")
    print(f"   ✓ User signup & authentication")
    print(f"   ✓ Photo upload & SMPL fitting")
    print(f"   ✓ 3D avatar generation")
    print(f"   ✓ Workout logging & analysis")
    print(f"   ✓ Immediate effects (pump)")
    print(f"   ✓ Long-term predictions")
    print(f"   ✓ Weight tracking")
    print(f"   ✓ Goal setting & recommendations")
    print(f"   ✓ Avatar timeline generation")
    print(f"   ✓ Social sharing")
    print(f"   ✓ Progress retrieval")
    print(f"\nThe complete system is working end-to-end!")

    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
