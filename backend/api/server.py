#!/usr/bin/env python3
"""
PhysiqAI API Server
===================

Complete REST API for the fitness avatar application.

Endpoints:
- User management (signup, login, profile)
- Photo processing (upload, fit SMPL, generate avatar)
- Workout logging (log workout, get analysis, predictions)
- Progress tracking (weight, measurements, timeline)
- Goals (set goals, get recommendations, projections)
- Social (share progress, friends, leaderboards)

Usage:
    python3 -m backend.api.server

Server runs on http://localhost:8000 by default.
"""

import json
import uuid
import base64
from datetime import datetime, timedelta
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import sys
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.models.database import (
    User, UserPhoto, Workout, WorkoutExercise, BodyMeasurement,
    Goal, ProgressEntry, SocialConnection, SharedProgress, db
)
from backend.services.photo_processor import photo_processor
from backend.services.workout_engine import workout_engine, WorkoutAnalysis
from backend.services.avatar_generator import avatar_generator


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for PhysiqAI API"""

    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

    def send_json_response(self, data: dict, status: int = 200):
        """Send JSON response"""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

    def send_error_response(self, message: str, status: int = 400):
        """Send error response"""
        self.send_json_response({'error': message, 'success': False}, status)

    def read_json_body(self) -> dict:
        """Read and parse JSON request body"""
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode()
        return json.loads(body)

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        """Handle GET requests"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Health check
        if path == '/health':
            self.send_json_response({
                'status': 'healthy',
                'service': 'PhysiqAI API',
                'version': '1.0.0'
            })
            return

        # User endpoints
        if path.startswith('/api/users/'):
            self.handle_get_user(path, query)
            return

        if path == '/api/users':
            self.handle_list_users(query)
            return

        # Avatar endpoints
        if path.startswith('/api/avatar/'):
            self.handle_get_avatar(path, query)
            return

        # Workout endpoints
        if path.startswith('/api/workouts/'):
            self.handle_get_workout(path, query)
            return

        if path == '/api/workouts':
            self.handle_list_workouts(query)
            return

        # Progress endpoints
        if path == '/api/progress':
            self.handle_get_progress(query)
            return

        # Goal endpoints
        if path == '/api/goals':
            self.handle_get_goals(query)
            return

        # Social endpoints
        if path == '/api/social/feed':
            self.handle_get_social_feed(query)
            return

        # 404
        self.send_error_response('Not found', 404)

    def do_POST(self):
        """Handle POST requests"""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Auth endpoints
        if path == '/api/auth/signup':
            self.handle_signup()
            return

        if path == '/api/auth/login':
            self.handle_login()
            return

        # Photo upload
        if path == '/api/photos/upload':
            self.handle_photo_upload()
            return

        # Workout logging
        if path == '/api/workouts/log':
            self.handle_log_workout()
            return

        # Weight logging
        if path == '/api/weight/log':
            self.handle_log_weight()
            return

        # Goals
        if path == '/api/goals/create':
            self.handle_create_goal()
            return

        # Social
        if path == '/api/social/share':
            self.handle_share_progress()
            return

        if path == '/api/social/friend/request':
            self.handle_friend_request()
            return

        # Predictions
        if path == '/api/predictions/timeline':
            self.handle_get_timeline_prediction()
            return

        # 404
        self.send_error_response('Not found', 404)

    # === HANDLER METHODS ===

    def handle_signup(self):
        """Handle user signup"""
        try:
            data = self.read_json_body()

            # Validate required fields
            required = ['email', 'name', 'gender']
            for field in required:
                if field not in data:
                    self.send_error_response(f'Missing required field: {field}')
                    return

            # Check if email exists
            for user in db.users.values():
                if user.email == data['email']:
                    self.send_error_response('Email already registered', 409)
                    return

            # Create user
            user = User(
                id=str(uuid.uuid4())[:12],
                email=data['email'],
                name=data['name'],
                gender=data['gender'],
                height_cm=data.get('height_cm'),
                birth_date=datetime.fromisoformat(data['birth_date']) if data.get('birth_date') else None,
            )

            db.save_user(user)

            self.send_json_response({
                'success': True,
                'message': 'User created successfully',
                'user': user.to_dict()
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_login(self):
        """Handle user login"""
        try:
            data = self.read_json_body()
            email = data.get('email')

            # Find user by email (simplified - no password for demo)
            user = None
            for u in db.users.values():
                if u.email == email:
                    user = u
                    break

            if not user:
                self.send_error_response('User not found', 404)
                return

            self.send_json_response({
                'success': True,
                'user': user.to_dict()
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_get_user(self, path: str, query: dict):
        """Get user by ID"""
        try:
            user_id = path.split('/')[-1]
            user = db.get_user(user_id)

            if not user:
                self.send_error_response('User not found', 404)
                return

            # Include related data
            response = {'user': user.to_dict()}

            if query.get('include', [''])[0] == 'full':
                response['photos'] = [p.to_dict() for p in db.get_user_photos(user_id)]
                response['workouts'] = [w.to_dict() for w in db.get_user_workouts(user_id)]
                response['measurements'] = [m.to_dict() for m in db.get_user_measurements(user_id)]
                response['goals'] = [g.to_dict() for g in db.get_user_goals(user_id)]

            self.send_json_response(response)

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_list_users(self, query: dict):
        """List all users"""
        users = [u.to_dict() for u in db.users.values()]
        self.send_json_response({'users': users, 'count': len(users)})

    def handle_photo_upload(self):
        """Handle photo upload and SMPL fitting"""
        try:
            data = self.read_json_body()

            user_id = data.get('user_id')
            photo_base64 = data.get('photo')
            photo_type = data.get('photo_type', 'front')

            if not user_id or not photo_base64:
                self.send_error_response('Missing user_id or photo')
                return

            user = db.get_user(user_id)
            if not user:
                self.send_error_response('User not found', 404)
                return

            # Decode base64 photo
            photo_bytes = base64.b64decode(photo_base64)

            print(f"\n📸 Processing photo upload for user {user_id}...")

            # Process photo
            photo_record = photo_processor.process_upload(
                user_id=user_id,
                photo_data=photo_bytes,
                photo_type=photo_type,
                gender=user.gender
            )

            if photo_record.processed:
                # Update user stats from photo estimation
                if photo_record.estimated_weight_kg:
                    user.current_weight_kg = photo_record.estimated_weight_kg
                db.save_user(user)

                # Generate avatar
                avatar = avatar_generator.generate_current_avatar(user)

                self.send_json_response({
                    'success': True,
                    'message': 'Photo processed successfully',
                    'photo': photo_record.to_dict(),
                    'avatar': avatar,
                })
            else:
                self.send_json_response({
                    'success': False,
                    'message': 'Photo processing failed',
                    'error': photo_record.processing_error,
                    'photo': photo_record.to_dict(),
                })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_get_avatar(self, path: str, query: dict):
        """Get avatar for user"""
        try:
            parts = path.split('/')
            if len(parts) < 4:
                self.send_error_response('Invalid path')
                return

            user_id = parts[3]
            action = parts[4] if len(parts) > 4 else 'current'

            user = db.get_user(user_id)
            if not user:
                self.send_error_response('User not found', 404)
                return

            if action == 'current':
                avatar = avatar_generator.generate_current_avatar(user)
                self.send_json_response({'avatar': avatar})

            elif action == 'future':
                weeks = int(query.get('weeks', ['12'])[0])
                avatar = avatar_generator.generate_future_avatar(user, weeks)
                self.send_json_response({'avatar': avatar})

            elif action == 'comparison':
                comparison = avatar_generator.generate_comparison(user)
                self.send_json_response({'comparison': comparison})

            elif action == 'timeline':
                weeks = int(query.get('weeks', ['12'])[0])
                timeline = avatar_generator.generate_timeline(user, weeks)
                self.send_json_response({'timeline': timeline})

            else:
                self.send_error_response('Invalid action')

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_log_workout(self):
        """Log a workout and get analysis"""
        try:
            data = self.read_json_body()

            user_id = data.get('user_id')
            user = db.get_user(user_id)

            if not user:
                self.send_error_response('User not found', 404)
                return

            # Create workout from data
            exercises = []
            for ex_data in data.get('exercises', []):
                exercise = WorkoutExercise(
                    name=ex_data['name'],
                    muscle_groups=ex_data.get('muscle_groups', []),
                    exercise_type=ex_data.get('exercise_type', 'compound'),
                    sets=ex_data.get('sets', 3),
                    reps=ex_data.get('reps', 10),
                    weight_kg=ex_data.get('weight_kg', 0),
                    rpe=ex_data.get('rpe', 7),
                    notes=ex_data.get('notes', ''),
                )
                exercises.append(exercise)

            workout = Workout(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                name=data.get('name', 'Workout'),
                workout_type=data.get('workout_type', 'strength'),
                start_time=datetime.fromisoformat(data['start_time']) if data.get('start_time') else datetime.now(),
                duration_minutes=data.get('duration_minutes'),
                exercises=exercises,
                notes=data.get('notes', ''),
            )

            print(f"\n💪 Logging workout for user {user_id}...")

            # Log and analyze workout
            analysis = workout_engine.log_workout(user, workout)

            # Generate post-workout avatar with pump
            avatar = avatar_generator.generate_current_avatar(
                user,
                with_pump=True,
                pump_muscles=analysis.immediate_effects.muscle_pump
            )

            # Generate future prediction
            predictions = workout_engine.predict_body_timeline(user, weeks=12)

            self.send_json_response({
                'success': True,
                'workout': workout.to_dict(),
                'analysis': analysis.to_dict(),
                'post_workout_avatar': avatar,
                'predictions': [p.to_dict() for p in predictions[:4]],  # First 4 weeks
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_get_workout(self, path: str, query: dict):
        """Get workout by ID"""
        try:
            workout_id = path.split('/')[-1]
            workout = db.workouts.get(workout_id)

            if not workout:
                self.send_error_response('Workout not found', 404)
                return

            self.send_json_response({'workout': workout.to_dict()})

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_list_workouts(self, query: dict):
        """List workouts for user"""
        try:
            user_id = query.get('user_id', [''])[0]
            if not user_id:
                self.send_error_response('Missing user_id')
                return

            workouts = db.get_user_workouts(user_id)
            self.send_json_response({
                'workouts': [w.to_dict() for w in workouts],
                'count': len(workouts)
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_log_weight(self):
        """Log weight measurement"""
        try:
            data = self.read_json_body()

            user_id = data.get('user_id')
            user = db.get_user(user_id)

            if not user:
                self.send_error_response('User not found', 404)
                return

            weight_kg = data.get('weight_kg')
            body_fat_pct = data.get('body_fat_pct')

            if not weight_kg:
                self.send_error_response('Missing weight_kg')
                return

            print(f"\n⚖️  Logging weight for user {user_id}: {weight_kg} kg")

            # Log weight
            measurement = workout_engine.log_weight(
                user=user,
                weight_kg=weight_kg,
                body_fat_pct=body_fat_pct,
            )

            # Generate updated avatar
            avatar = avatar_generator.generate_current_avatar(user)

            self.send_json_response({
                'success': True,
                'measurement': measurement.to_dict(),
                'avatar': avatar,
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_get_progress(self, query: dict):
        """Get progress data for user"""
        try:
            user_id = query.get('user_id', [''])[0]
            if not user_id:
                self.send_error_response('Missing user_id')
                return

            user = db.get_user(user_id)
            if not user:
                self.send_error_response('User not found', 404)
                return

            # Get all progress data
            measurements = db.get_user_measurements(user_id)
            workouts = db.get_user_workouts(user_id)
            entries = db.get_user_progress(user_id)

            self.send_json_response({
                'user': user.to_dict(),
                'measurements': [m.to_dict() for m in measurements],
                'workout_count': len(workouts),
                'recent_entries': [e.to_dict() for e in entries],
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_create_goal(self):
        """Create a fitness goal"""
        try:
            data = self.read_json_body()

            user_id = data.get('user_id')
            user = db.get_user(user_id)

            if not user:
                self.send_error_response('User not found', 404)
                return

            goal = Goal(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                goal_type=data.get('goal_type', 'weight_loss'),
                title=data.get('title', 'New Goal'),
                description=data.get('description', ''),
                target_date=datetime.fromisoformat(data['target_date']) if data.get('target_date') else None,
                target_weight_kg=data.get('target_weight_kg'),
                target_body_fat_pct=data.get('target_body_fat_pct'),
                target_muscle_mass_kg=data.get('target_muscle_mass_kg'),
                start_weight_kg=user.current_weight_kg,
                start_body_fat_pct=user.current_body_fat_pct,
                timeline_weeks=data.get('timeline_weeks', 12),
            )

            db.save_goal(goal)

            # Generate projected avatar
            if goal.target_weight_kg:
                weight_diff = goal.target_weight_kg - (user.current_weight_kg or 70)
                target_betas = [weight_diff * 0.02] + [0.0] * 9
                projected_avatar = avatar_generator.generate_future_avatar(user, goal.timeline_weeks, target_betas)
            else:
                projected_avatar = avatar_generator.generate_future_avatar(user, goal.timeline_weeks)

            # Generate workout recommendation
            recommendations = self._generate_goal_recommendations(goal, user)

            self.send_json_response({
                'success': True,
                'goal': goal.to_dict(),
                'projected_avatar': projected_avatar,
                'recommendations': recommendations,
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def _generate_goal_recommendations(self, goal: Goal, user: User) -> List[dict]:
        """Generate workout recommendations for goal"""
        recommendations = []

        if goal.goal_type == 'weight_loss':
            recommendations = [
                {'type': 'cardio', 'frequency': '3-4x per week', 'duration': '30-45 min', 'intensity': 'Moderate'},
                {'type': 'strength', 'frequency': '3x per week', 'focus': 'Full body compound movements'},
                {'type': 'nutrition', 'advice': '500 kcal daily deficit', 'protein': '2g per kg bodyweight'},
            ]
        elif goal.goal_type == 'muscle_gain':
            recommendations = [
                {'type': 'strength', 'frequency': '4-5x per week', 'split': 'Upper/Lower or PPL', 'volume': '10-20 sets per muscle'},
                {'type': 'nutrition', 'advice': '300 kcal daily surplus', 'protein': '1.6-2.2g per kg bodyweight'},
                {'type': 'recovery', 'sleep': '7-9 hours', 'rest_days': '2-3 per week'},
            ]
        elif goal.goal_type == 'body_recomposition':
            recommendations = [
                {'type': 'strength', 'frequency': '4x per week', 'focus': 'Progressive overload'},
                {'type': 'cardio', 'frequency': '2-3x per week', 'type': 'LISS or HIIT'},
                {'type': 'nutrition', 'advice': 'Maintenance calories', 'protein': '2.2g per kg bodyweight'},
            ]

        return recommendations

    def handle_get_goals(self, query: dict):
        """Get goals for user"""
        try:
            user_id = query.get('user_id', [''])[0]
            if not user_id:
                self.send_error_response('Missing user_id')
                return

            goals = db.get_user_goals(user_id)
            self.send_json_response({
                'goals': [g.to_dict() for g in goals],
                'count': len(goals)
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_get_timeline_prediction(self):
        """Get body prediction timeline"""
        try:
            data = self.read_json_body()

            user_id = data.get('user_id')
            weeks = data.get('weeks', 12)

            user = db.get_user(user_id)
            if not user:
                self.send_error_response('User not found', 404)
                return

            predictions = workout_engine.predict_body_timeline(user, weeks)

            # Generate avatars for key weeks
            avatar_weeks = [0, weeks // 2, weeks]
            avatars = {}

            for week in avatar_weeks:
                if week < len(predictions):
                    pred = predictions[week]
                    avatars[f'week_{week}'] = avatar_generator.generate_future_avatar(
                        user, week, pred.smpl_betas
                    )

            self.send_json_response({
                'predictions': [p.to_dict() for p in predictions],
                'avatars': avatars,
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_share_progress(self):
        """Share progress to social feed"""
        try:
            data = self.read_json_body()

            user_id = data.get('user_id')
            user = db.get_user(user_id)

            if not user:
                self.send_error_response('User not found', 404)
                return

            shared = SharedProgress(
                id=str(uuid.uuid4())[:8],
                user_id=user_id,
                share_type=data.get('share_type', 'milestone'),
                title=data.get('title', 'Progress Update'),
                description=data.get('description', ''),
                progress_data=data.get('progress_data', {}),
            )

            db.save_shared_progress(shared)

            self.send_json_response({
                'success': True,
                'shared': shared.to_dict(),
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_get_social_feed(self, query: dict):
        """Get social feed"""
        try:
            feed = db.get_shared_progress(limit=20)
            self.send_json_response({
                'feed': [s.to_dict() for s in feed],
                'count': len(feed)
            })

        except Exception as e:
            self.send_error_response(str(e), 500)

    def handle_friend_request(self):
        """Send friend request"""
        try:
            data = self.read_json_body()

            connection = SocialConnection(
                id=str(uuid.uuid4())[:8],
                requester_id=data.get('requester_id'),
                recipient_id=data.get('recipient_id'),
            )

            db.save_connection(connection)

            self.send_json_response({
                'success': True,
                'connection': connection.to_dict(),
            })

        except Exception as e:
            self.send_error_response(str(e), 500)


class PhysiqAPIServer:
    """PhysiqAI API Server"""

    def __init__(self, host='localhost', port=8000):
        self.host = host
        self.port = port
        self.server = HTTPServer((host, port), APIHandler)

    def start(self):
        """Start the server"""
        print(f"\n🚀 PhysiqAI API Server starting...")
        print(f"   URL: http://{self.host}:{self.port}")
        print(f"\n📚 Available endpoints:")
        print(f"   POST /api/auth/signup          - Create account")
        print(f"   POST /api/auth/login           - Login")
        print(f"   POST /api/photos/upload        - Upload photo & generate avatar")
        print(f"   POST /api/workouts/log         - Log workout & get analysis")
        print(f"   POST /api/weight/log           - Log weight")
        print(f"   POST /api/goals/create         - Create goal")
        print(f"   GET  /api/avatar/{'{user_id}'}/current  - Get current avatar")
        print(f"   GET  /api/avatar/{'{user_id}'}/future   - Get future projection")
        print(f"   GET  /api/avatar/{'{user_id}'}/timeline - Get timeline")
        print(f"\nPress Ctrl+C to stop\n")

        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 Server stopped")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='PhysiqAI API Server')
    parser.add_argument('--host', default='localhost', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8000, help='Port to bind to')
    args = parser.parse_args()

    server = PhysiqAPIServer(args.host, args.port)
    server.start()


if __name__ == "__main__":
    main()
