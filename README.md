# PhysiqAI

**AI-Powered 3D Body Transformation Visualization**

PhysiqAI creates photorealistic 3D avatars that visualize your fitness journey. Upload a photo, track your workouts, and watch your avatar transform in real-time based on actual physiological changes.

---

## What It Does

1. **Upload a photo** → AI extracts your body shape
2. **Log your workouts** → System calculates physiological changes
3. **See your future self** → Avatar morphs to show projected results

No other app combines photorealistic visualization with exercise science-backed predictions.

---

## Quick Start

```bash
# Clone and enter
git clone https://github.com/bzhang0824/physiqai.git
cd physiqai

# Install dependencies
pip install -r backend/requirements.txt

# Start the backend API
cd backend/api
python3 server.py

# In another terminal, serve the frontend
cd ../../app
python3 -m http.server 8080

# Open browser
open http://localhost:8080/clean/home.html
```

---

## Project Structure

```
physiqai/
├── app/                    # Frontend (HTML/CSS/JS)
│   ├── clean/             # Main app pages
│   ├── avatar.html        # 3D avatar viewer
│   └── dashboard.html     # Progress tracking
├── backend/               # Python services
│   ├── api/               # FastAPI server
│   ├── photo_fitter.py    # Photo → 3D mesh
│   └── workout_predictor.py  # ML predictions
├── avatar/                # Morphing system
│   ├── morphing/          # Core morphing logic
│   └── viewer.html        # Three.js viewer
├── models/                # ML models & SMPL
│   ├── smpl/              # SMPL body models
│   └── predictor.py       # Body change predictor
├── scrapers/              # Data collection
│   ├── reddit_scraper.py
│   └── overnight_scrape.py
├── docs/                  # Documentation
└── demo/                  # Demo photos & outputs
```

---

## Key Features

| Feature | Status | Notes |
|---------|--------|-------|
| Photo-to-3D Avatar | ✅ Working | SMPL-based fitting |
| Workout Logging | ✅ Working | Firebase backend |
| Real-time Morphing | ✅ Working | Three.js visualization |
| Progress Tracking | ✅ Working | Weight, measurements |
| Mobile App | ✅ Working | PWA-ready |
| AI Predictions | 🟡 Partial | Heuristics + data |

---

## Tech Stack

**Frontend**
- Vanilla JS (no framework)
- Three.js for 3D rendering
- Firebase Auth & Firestore
- PWA with service worker

**Backend**
- Python 3.9+
- FastAPI for API server
- SMPL for 3D body models
- OpenCV for image processing

**ML/Data**
- Reddit transformation data (5,000+ posts)
- NHANES body measurement data
- Kaggle fitness datasets
- Custom heuristics based on exercise science

**Infrastructure**
- Firebase (auth, database, hosting)
- GitHub Actions (planned)
- Self-hosted API server

---

## Environment Setup

Create `.env` in project root:

```bash
# Firebase
FIREBASE_API_KEY=your_key
FIREBASE_PROJECT_ID=your_project

# APIs (optional)
REPLICATE_API_TOKEN=your_token
FAL_KEY=your_key
GOOGLE_API_KEY=your_key

# Reddit (for scrapers)
REDDIT_CLIENT_ID=your_id
REDDIT_CLIENT_SECRET=your_secret
```

---

## Running Tests

```bash
# Photo fitter test
python3 backend/test_photo_fitter.py

# ML model test
python3 backend/test_ml_model_v2.py

# End-to-end test
python3 test_end_to_end.py

# Full test harness
python3 backend/test_harness.py
```

---

## Data Collection

The project includes automated scrapers for training data:

```bash
# Run all scrapers
cd scrapers
python3 overnight_scrape.py

# Or individual sources
python3 reddit_scraper.py
python3 nhanes_scraper.py
```

**Current Dataset:**
- 5,000+ Reddit transformation posts
- NHANES body measurement data
- 6 Kaggle fitness datasets

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) - System design
- [API Reference](docs/API_REFERENCE.md) - Backend endpoints
- [Data Schema](docs/DATA_SCHEMA.md) - Database structure
- [PRD](docs/PRD.md) - Product requirements

---

## Development Status

**Phase:** MVP Complete, Polishing

**Last Major Update:** March 2026

**Known Issues:**
- ML predictions use heuristics (need more training data)
- Photo fitting requires good lighting/angle
- iOS Safari has some WebGL limitations

---

## Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature/name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push: `git push origin feature/name`
5. Open a Pull Request

---

## License

MIT License - See LICENSE file

---

**Questions?** Open an issue or reach out.
