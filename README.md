# PhysiqAI - AI-Powered 3D Body Transformation

**Last Updated:** 2026-03-26 18:00 UTC

## 🎯 What is PhysiqAI?

PhysiqAI creates personalized 3D avatars that morph and transform based on your fitness journey. Upload a photo, log your workouts, and watch your avatar change in real-time.

## ✨ Features

- 📸 **Photo-to-3D Avatar**: Upload a photo, get your personalized 3D body model
- 💪 **Workout Tracking**: Log exercises, sets, reps, and weight
- 🔄 **Real-time Morphing**: Watch your avatar change as you progress
- 📊 **Progress Visualization**: Track weight, body composition, and measurements
- 🎯 **Goal Setting**: Set targets and see predicted future avatar
- 📱 **Mobile-First**: Works on any device, PWA ready

## 🚀 Quick Start

```bash
# Start the app
cd app
python3 -m http.server 8080

# Open in browser
open http://localhost:8080/clean/home.html
```

## 📁 Project Structure

```
physiqai/
├── app/                    # Frontend application
│   ├── clean/             # Clean, minimalist UI
│   └── *.html             # Individual pages
├── backend/               # Python backend services
│   ├── photo_fitter.py    # Photo → 3D avatar
│   └── workout_predictor.py  # ML predictions
├── models/                # ML models and SMPL
├── docs/                  # Documentation
└── storage/               # User data and meshes
```

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3, Vanilla JS, Three.js
- **Backend**: Python, FastAPI, Firebase
- **ML**: Custom heuristics + Reddit data training
- **3D**: SMPL models, Three.js rendering
- **Database**: Firestore (Firebase)

## 📊 Current Stats

- **Users**: 0 test profiles
- **Avatars Generated**: 0
- **ML Model Accuracy**: 89.3% correlation
- **Test Coverage**: 5 test files

## 🧪 Testing

```bash
# Run QA validator
python3 scripts/qa_validator.py

# Run continuous QA monitor
python3 scripts/continuous_qa.py

# Run specific tests
python3 backend/test_photo_fitter.py
```

## 📚 Documentation

- [API Reference](docs/API_REFERENCE.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Data Schema](docs/DATA_SCHEMA.md)
- [Changelog](docs/CHANGELOG.md)

## 🏗️ Development

### Continuous QA
This project uses automated QA that runs on every file change:
- Syntax checking
- Import verification
- Auto-formatting
- Integration testing

### Documentation
Documentation auto-updates twice daily (6 AM/PM UTC) via cron.

## 📝 License

MIT License - See LICENSE file

---
**Built with ❤️ by the PhysiqAI team**
