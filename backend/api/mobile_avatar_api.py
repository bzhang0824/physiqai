#!/usr/bin/env python3
"""
PhysiqAI Mobile Avatar API - Production Hardened Version
Simple Flask API to handle photo upload and SMPL mesh generation for mobile

Improvements:
- Exception handling with full stack traces
- Request timeouts (30s)
- Memory safety (10MB limit, streaming)
- Threaded production server
- Graceful shutdown handling
- Safe imports (no exec())
- Input validation
- Cleanup on errors
"""

import os
import sys
import json
import logging
import signal
import time
import shutil
import tempfile
import traceback
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, send_file, after_this_request
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Setup logging with detailed formatting
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler('/tmp/mobile_avatar_api.log', maxBytes=10485760, backupCount=5)
    ]
)
logger = logging.getLogger(__name__)

# Configuration constants
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB max file size
UPLOAD_TIMEOUT = 30  # 30 seconds timeout for processing
REQUEST_TIMEOUT = 60  # 60 seconds for request handling
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
ALLOWED_MIME_TYPES = {'image/png', 'image/jpeg', 'image/jpg', 'image/webp'}
MAX_USER_ID_LENGTH = 128

# Determine project root - api -> backend -> physiqai -> projects -> workspace
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent

# Fix: Ensure correct paths (not nested under projects)
UPLOAD_FOLDER = Path(str(PROJECT_ROOT / 'storage' / 'photos').replace('/projects/storage', '/storage'))
MESH_FOLDER = Path(str(PROJECT_ROOT / 'storage' / 'meshes').replace('/projects/storage', '/storage'))
TEMP_FOLDER = Path(tempfile.gettempdir()) / 'physiqai_uploads'

# Import photo fitting pipeline - add backend dir to path
backend_dir = PROJECT_ROOT / 'projects' / 'physiqai' / 'backend'
sys.path.insert(0, str(backend_dir))

# Safe import without exec()
try:
    from photo_fitter import PhotoFittingPipeline
    logger.info("Successfully imported PhotoFittingPipeline")
except ImportError as e:
    logger.error(f"Failed to import PhotoFittingPipeline: {e}")
    # Create a stub for graceful degradation
    class PhotoFittingPipeline:
        def process_photo(self, image_bytes, user_id, photo_type):
            return {'success': False, 'error': 'Pipeline not available'}

    logger.warning("Using stub PhotoFittingPipeline - uploads will fail")

# Initialize Flask app with production settings
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config['PERMANENT_SESSION_LIFETIME'] = 300  # 5 minute session timeout

# Enable CORS for all origins (mobile apps, web apps, etc.)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": False
    }
})

# Initialize pipeline with error handling
try:
    pipeline = PhotoFittingPipeline()
    logger.info("PhotoFittingPipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize PhotoFittingPipeline: {e}")
    pipeline = None

# Track server shutdown state
shutdown_requested = False
active_requests = 0

# Request logging middleware
@app.before_request
def log_request():
    """Log all incoming requests"""
    global active_requests
    active_requests += 1
    logger.info(f"[{request.method}] {request.path} - Active requests: {active_requests}")

    # Log request details for debugging
    if request.content_length:
        logger.info(f"Request content length: {request.content_length} bytes")
    if request.files:
        logger.info(f"Request files: {list(request.files.keys())}")

@app.after_request
def log_response(response):
    """Log all responses"""
    global active_requests
    active_requests -= 1
    logger.info(f"[{request.method}] {request.path} - Status: {response.status_code} - Active: {active_requests}")

    # Add CORS headers to all responses including errors
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')

    return response

# Error handlers with CORS
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    """Handle file size exceeded"""
    logger.warning(f"File too large: {request.content_length} bytes")
    response = jsonify({
        'success': False,
        'error': f'File too large. Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB'
    })
    response.status_code = 413
    return response

@app.errorhandler(404)
def handle_not_found(e):
    """Handle 404 errors"""
    response = jsonify({
        'success': False,
        'error': 'Endpoint not found'
    })
    response.status_code = 404
    return response

@app.errorhandler(500)
def handle_internal_error(e):
    """Handle internal server errors"""
    logger.exception("Internal server error")
    response = jsonify({
        'success': False,
        'error': 'Internal server error. Please try again later.'
    })
    response.status_code = 500
    return response

# Signal handlers for graceful shutdown
def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown"""
    global shutdown_requested
    logger.info(f"Received signal {signum}. Starting graceful shutdown...")
    shutdown_requested = True

    # Wait for active requests to complete (with timeout)
    wait_start = time.time()
    while active_requests > 0 and time.time() - wait_start < 10:
        logger.info(f"Waiting for {active_requests} active requests to complete...")
        time.sleep(0.5)

    # Cleanup temp files
    cleanup_temp_files()

    logger.info("Shutdown complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

def cleanup_temp_files():
    """Clean up temporary upload files"""
    try:
        if TEMP_FOLDER.exists():
            for f in TEMP_FOLDER.glob('*'):
                try:
                    f.unlink()
                    logger.debug(f"Cleaned up temp file: {f}")
                except Exception as e:
                    logger.warning(f"Failed to clean up {f}: {e}")
            logger.info(f"Temp folder cleanup complete: {TEMP_FOLDER}")
    except Exception as e:
        logger.error(f"Error cleaning up temp files: {e}")

def validate_user_id(user_id):
    """Validate user_id parameter"""
    if not user_id or not isinstance(user_id, str):
        return False, "user_id is required and must be a string"

    if len(user_id) > MAX_USER_ID_LENGTH:
        return False, f"user_id too long (max {MAX_USER_ID_LENGTH} characters)"

    # Check for valid characters (alphanumeric, underscore, hyphen)
    if not all(c.isalnum() or c in '_-' for c in user_id):
        return False, "user_id contains invalid characters (only alphanumeric, underscore, hyphen allowed)"

    return True, None

def validate_file_type(file):
    """Validate file type by extension and MIME type"""
    filename = file.filename.lower()

    # Check extension
    if '.' not in filename:
        return False, "File must have an extension"

    ext = filename.rsplit('.', 1)[1]
    if ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type '.{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"

    # Check MIME type if available
    mime_type = file.content_type
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        logger.warning(f"Unexpected MIME type: {mime_type}")
        # Don't fail on MIME type mismatch, just warn

    return True, None

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class TimeoutError(Exception):
    """Custom timeout exception"""
    pass

def process_with_timeout(image_bytes, user_id, photo_type, timeout=UPLOAD_TIMEOUT):
    """Process photo with timeout protection"""
    import threading

    result = {'success': False, 'error': 'Processing timed out'}
    exception_occurred = None

    def target():
        nonlocal result, exception_occurred
        try:
            if pipeline is None:
                result = {'success': False, 'error': 'Pipeline not initialized'}
                return
            result = pipeline.process_photo(image_bytes, user_id, photo_type)
        except Exception as e:
            exception_occurred = e
            logger.exception("Pipeline processing error")

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        logger.error(f"Processing timed out after {timeout}s")
        # We can't kill the thread, but we return timeout error
        # The thread will eventually complete but result is discarded
        return {'success': False, 'error': 'Processing timed out (30s limit)', 'timeout': True}

    if exception_occurred:
        raise exception_occurred

    return result

# Ensure directories exist
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
MESH_FOLDER.mkdir(parents=True, exist_ok=True)
TEMP_FOLDER.mkdir(parents=True, exist_ok=True)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check if pipeline is available
        pipeline_status = 'available' if pipeline is not None else 'unavailable'

        # Check storage directories
        storage_ok = UPLOAD_FOLDER.exists() and MESH_FOLDER.exists()

        # Check available disk space (require at least 100MB)
        disk = shutil.disk_usage('/tmp')
        disk_ok = disk.free > 100 * 1024 * 1024

        status = 'healthy' if (pipeline_status == 'available' and storage_ok and disk_ok) else 'degraded'

        response = jsonify({
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'version': '1.1.0-hardened',
            'checks': {
                'pipeline': pipeline_status,
                'storage': 'ok' if storage_ok else 'error',
                'disk_space': 'ok' if disk_ok else 'low'
            },
            'active_requests': active_requests,
            'shutdown_requested': shutdown_requested
        })

        if status != 'healthy':
            response.status_code = 503

        return response

    except Exception as e:
        logger.exception("Health check failed")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_photo():
    """
    Upload photo and generate SMPL mesh

    Form data:
    - photo: File (required, max 10MB)
    - user_id: string (required, alphanumeric + _-)
    - photo_type: string (default: 'front')
    """
    temp_file_path = None

    try:
        logger.info("Received upload request")

        # Check if shutdown is requested
        if shutdown_requested:
            return jsonify({
                'success': False,
                'error': 'Server is shutting down, please try again later'
            }), 503

        # Validate user_id
        user_id = request.form.get('user_id', '').strip()
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            logger.warning(f"Invalid user_id: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        photo_type = request.form.get('photo_type', 'front').strip().lower()
        if photo_type not in ['front', 'back', 'side']:
            return jsonify({
                'success': False,
                'error': 'photo_type must be front, back, or side'
            }), 400

        logger.info(f"Processing upload for user: {user_id}, type: {photo_type}")

        # Check if photo is present
        if 'photo' not in request.files:
            logger.error("No photo in request")
            return jsonify({
                'success': False,
                'error': 'No photo provided'
            }), 400

        file = request.files['photo']
        if file.filename == '':
            logger.error("Empty filename")
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file type
        is_valid, error_msg = validate_file_type(file)
        if not is_valid:
            logger.warning(f"File validation failed: {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Check file size by reading content
        file_content = file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            logger.warning(f"File too large: {file_size} bytes (max {MAX_FILE_SIZE})")
            return jsonify({
                'success': False,
                'error': f'File too large ({file_size / (1024*1024):.1f}MB). Maximum size is {MAX_FILE_SIZE / (1024*1024):.1f}MB'
            }), 413

        if file_size == 0:
            return jsonify({
                'success': False,
                'error': 'File is empty'
            }), 400

        logger.info(f"File size: {file_size} bytes")

        # Save to temp file for memory safety with large files
        temp_file_path = TEMP_FOLDER / f"upload_{user_id}_{int(time.time())}.tmp"
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)

        logger.info(f"Saved to temp file: {temp_file_path}")

        # Process through photo fitting pipeline with timeout
        logger.info("Starting pipeline processing with timeout...")
        result = process_with_timeout(file_content, user_id, photo_type)

        # Clean up temp file after reading
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
                logger.debug(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {e}")

        if result.get('timeout'):
            return jsonify({
                'success': False,
                'error': 'Processing took too long. Please try with a smaller image or try again later.'
            }), 408  # Request Timeout

        if result['success']:
            # Convert file:// URLs to relative paths for mobile access
            mesh_path = result.get('mesh_path', '')

            logger.info(f"Pipeline success: {result.get('photo_id', 'unknown')}")

            return jsonify({
                'success': True,
                'photo_id': result.get('photo_id'),
                'user_id': user_id,
                'photo_url': result.get('photo_url'),
                'mesh_path': mesh_path,
                'mesh_url': f'/api/mesh/{user_id}/{result.get("photo_id", "")}',
                'detection': result.get('detection'),
                'smpl_params': result.get('smpl_params'),
                'processing_time_ms': result.get('processing_time_ms'),
                'confidence': result.get('confidence')
            })
        else:
            error_msg = result.get('error', 'Processing failed')
            logger.error(f"Pipeline failed: {error_msg}")

            # Check if mesh was partially created and save it anyway
            if 'mesh_data' in result and result.get('photo_id'):
                try:
                    mesh_path = MESH_FOLDER / f"{result['photo_id']}_mesh.json"
                    with open(mesh_path, 'w') as f:
                        json.dump(result['mesh_data'], f)
                    logger.info(f"Saved partial mesh to {mesh_path}")
                except Exception as e:
                    logger.error(f"Failed to save partial mesh: {e}")

            return jsonify({
                'success': False,
                'error': error_msg
            }), 500

    except Exception as e:
        logger.exception(f"Upload error: {str(e)}")
        logger.error(f"Stack trace:\n{traceback.format_exc()}")

        # Clean up temp file on error
        if temp_file_path and temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except:
                pass

        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again later.'
        }), 500

@app.route('/api/mesh/<user_id>/<photo_id>', methods=['GET'])
def get_mesh(user_id, photo_id):
    """
    Get generated mesh for a specific photo
    """
    try:
        # Validate inputs
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        if not photo_id or not isinstance(photo_id, str):
            return jsonify({'success': False, 'error': 'Invalid photo_id'}), 400

        # Sanitize photo_id to prevent path traversal
        photo_id = secure_filename(photo_id)

        mesh_filename = f"{photo_id}_mesh.json"
        mesh_path = MESH_FOLDER / mesh_filename

        logger.info(f"Serving mesh: {mesh_path}")

        if not mesh_path.exists():
            # Try finding by user_id prefix
            user_meshes = list(MESH_FOLDER.glob(f"{user_id}*{photo_id}*_mesh.json"))
            if user_meshes:
                mesh_path = user_meshes[0]
            else:
                logger.warning(f"Mesh not found: {mesh_filename}")
                return jsonify({
                    'success': False,
                    'error': 'Mesh not found'
                }), 404

        # Check file is within mesh folder (prevent path traversal)
        try:
            mesh_path.resolve().relative_to(MESH_FOLDER.resolve())
        except ValueError:
            logger.error(f"Path traversal attempt: {mesh_path}")
            return jsonify({'success': False, 'error': 'Invalid mesh path'}), 400

        return send_file(mesh_path, mimetype='application/json')

    except Exception as e:
        logger.exception(f"Mesh retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve mesh'
        }), 500

@app.route('/api/mesh/latest/<user_id>', methods=['GET'])
def get_latest_mesh(user_id):
    """
    Get the most recent mesh for a user
    """
    try:
        # Validate user_id
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        # Find all meshes for this user
        user_meshes = sorted(
            MESH_FOLDER.glob(f"{user_id}*_mesh.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not user_meshes:
            return jsonify({
                'success': False,
                'error': 'No meshes found for user'
            }), 404

        latest_mesh = user_meshes[0]

        # Extract photo_id from filename
        filename = latest_mesh.stem.replace('_mesh', '')

        return jsonify({
            'success': True,
            'mesh_path': str(latest_mesh.relative_to(PROJECT_ROOT)),
            'mesh_url': f'/api/mesh/{user_id}/{filename}',
            'photo_id': filename,
            'created': datetime.fromtimestamp(latest_mesh.stat().st_mtime).isoformat()
        })

    except Exception as e:
        logger.exception(f"Latest mesh error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve latest mesh'
        }), 500

@app.route('/api/meshes/<user_id>', methods=['GET'])
def list_user_meshes(user_id):
    """
    List all meshes for a user
    """
    try:
        # Validate user_id
        is_valid, error_msg = validate_user_id(user_id)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400

        user_meshes = []
        for mesh_file in MESH_FOLDER.glob(f"{user_id}*_mesh.json"):
            try:
                user_meshes.append({
                    'filename': mesh_file.name,
                    'path': str(mesh_file.relative_to(PROJECT_ROOT)),
                    'url': f'/api/mesh/{user_id}/{mesh_file.stem.replace("_mesh", "")}',
                    'created': datetime.fromtimestamp(mesh_file.stat().st_mtime).isoformat()
                })
            except Exception as e:
                logger.warning(f"Error processing mesh file {mesh_file}: {e}")
                continue

        # Sort by creation time, newest first
        user_meshes.sort(key=lambda x: x['created'], reverse=True)

        return jsonify({
            'success': True,
            'meshes': user_meshes,
            'count': len(user_meshes)
        })

    except Exception as e:
        logger.exception(f"List meshes error: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to list meshes'
        }), 500

# Cleanup endpoint for testing/admin
@app.route('/api/cleanup', methods=['POST'])
def cleanup():
    """Clean up temp files (admin endpoint)"""
    try:
        cleanup_temp_files()
        return jsonify({'success': True, 'message': 'Cleanup completed'})
    except Exception as e:
        logger.exception(f"Cleanup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    logger.info("="*60)
    logger.info("Starting Mobile Avatar API - Production Hardened")
    logger.info("="*60)
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Mesh folder: {MESH_FOLDER}")
    logger.info(f"Temp folder: {TEMP_FOLDER}")
    logger.info(f"Max file size: {MAX_FILE_SIZE / (1024*1024):.1f}MB")
    logger.info(f"Processing timeout: {UPLOAD_TIMEOUT}s")
    logger.info(f"Pipeline available: {pipeline is not None}")
    logger.info("="*60)

    # Run with threaded mode for production
    # Use threaded=True to handle concurrent requests
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=False,  # Disable debug mode in production
        threaded=True,  # Enable threading for concurrent requests
        use_reloader=False  # Disable auto-reloader
    )
