# PhysiqAI API Reference

## Auto-generated: $(date '+%Y-%m-%d %H:%M UTC')

### Backend API Endpoints

#### test_photo_fitter.py
def download_sample_image():
def test_pipeline():

#### avatar_generator.py
class AvatarState:
class AvatarGenerator:

#### __init__.py

#### photo_processor.py
class SimpleSMPLFitter:
class PhotoProcessor:

#### workout_engine.py
class ImmediateEffects:
class LongTermAdaptation:
class WorkoutAnalysis:
class BodyPrediction:
class WorkoutEngine:

#### demo_api.py
def demo_basic_prediction():
def demo_weight_loss():
def demo_body_recomposition():
def demo_weekly_progression():
def demo_compare_workout_types():
def demo_api_response():

#### workout_predictor_optimized.py
class UserProfile:
class WorkoutPlan:
class NutritionPlan:
class PredictionResult:
class PhysiquePredictorModel:
class SyntheticDataGenerator:
class OptimizedPredictor:
def run_test_suite():

#### __init__.py

#### test_ml_model_v2.py
def load_reddit_transformations(n_samples=50):
def validate_model(n_samples=50):
def run_test_scenarios():
def generate_report(validation_results, scenario_results):

#### photo_fitter.py
class BodyKeypoints:
class BodyMeasurements:
class BodyDetectionResult:
class SMPLParams:
class PhotoUploadHandler:
class BodyDetector:
class SMPLEstimator:
class SMPLModelLoader:
class ThreeJSExporter:
class PhotoFittingPipeline:
def demo():

#### workout_predictor_fast.py
class UserProfile:
class WorkoutPlan:
class NutritionPlan:
class PredictionResult:
class OptimizedPredictor:
def run_test_suite():

#### mobile_avatar_api.py
def log_request():
def log_response(response):
def handle_file_too_large(e):
def handle_not_found(e):
def handle_internal_error(e):
def signal_handler(signum, frame):
def cleanup_temp_files():
def validate_user_id(user_id):
def validate_file_type(file):
def allowed_file(filename):
class TimeoutError(Exception):
def process_with_timeout(image_bytes, user_id, photo_type, timeout=UPLOAD_TIMEOUT):
def health_check():
def upload_photo():
def get_mesh(user_id, photo_id):
def get_latest_mesh(user_id):
def list_user_meshes(user_id):
def cleanup():

#### server.py
class APIHandler(BaseHTTPRequestHandler):
class PhysiqAPIServer:
def main():

#### __init__.py

#### test_harness.py
class TestHarness:
def main():

#### __init__.py

#### database.py
class User:
class UserPhoto:
class WorkoutExercise:
class Workout:
class BodyMeasurement:
class ProgressEntry:
class Goal:
class SocialConnection:
class SharedProgress:
class InMemoryDB:

#### ml_model_final.py
class UserProfile:
class NutritionPlan:
class PhysiqAIModel:
def validate_model():
def run_tests():

#### workout_predictor.py
class UserState:
class WorkoutPlan:
class NutritionPlan:
class WorkoutPredictor:
def test_predictor():

#### ml_model_v2.py
class UserProfile:
class NutritionPlan:
class PredictionResult:
class ImprovedPredictionEngine:

#### test_predictor.py
def validate_against_reddit_data(predictor: WorkoutPredictor, data_path: str) -> dict:
def test_scenarios():
def generate_accuracy_report():

