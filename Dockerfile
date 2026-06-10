# PhysiqAI backend (FastAPI) for Railway / any container host.
# Only the Python backend ships — the Expo app and the 763MB SMPL assets are
# excluded via .dockerignore.
FROM python:3.12-slim

WORKDIR /app

# imageio-ffmpeg bundles its own ffmpeg binary (no apt ffmpeg needed) and
# opencv-python-headless avoids the libGL system dep, so the slim base is enough.
COPY server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# Pre-cache the rembg u2net matte model into the image so cold starts don't
# re-download ~176MB on every container boot.
RUN python -c "from rembg import new_session; new_session('u2net')"

# App code only (mobile/, outputs, venvs, SMPL assets excluded by .dockerignore).
COPY server/ server/
COPY pipeline/ pipeline/
COPY models/__init__.py models/__init__.py
COPY models/governor/ models/governor/

ENV PYTHONUNBUFFERED=1
EXPOSE 8000
# Railway injects $PORT; bind to it (fall back to 8000 for local `docker run`).
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
