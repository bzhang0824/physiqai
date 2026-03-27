# Documentation Structure

## 📁 docs/ Directory Layout

```
docs/
├── README.md                 # Documentation index
├── api/                      # API Documentation
│   ├── README.md
│   ├── REST_API.md          # REST endpoint reference
│   ├── AUTHENTICATION.md    # Auth flows
│   └── WEBSOCKET.md         # Real-time API
├── architecture/             # System Design
│   ├── README.md
│   ├── OVERVIEW.md          # High-level architecture
│   ├── DATA_FLOW.md         # How data moves
│   ├── SMPL_INTEGRATION.md  # 3D model details
│   └── FIREBASE_SETUP.md    # Backend config
├── guides/                   # User Guides
│   ├── README.md
│   ├── GETTING_STARTED.md   # First-time setup
│   ├── USER_GUIDE.md        # How to use the app
│   ├── DEVELOPER_GUIDE.md   # Contributing
│   └── DEPLOYMENT.md        # Production deploy
├── reference/                # Technical Reference
│   ├── README.md
│   ├── DATA_SCHEMA.md       # Database schema
│   ├── ML_MODELS.md         # ML documentation
│   ├── COMPONENT_LIBRARY.md # UI components
│   └── TESTING.md           # QA procedures
└── assets/                   # Diagrams, images
    ├── diagrams/
    └── screenshots/
```

## 🔄 Auto-Update Schedule

- **6:00 AM UTC**: Documentation refresh
- **6:00 PM UTC**: Documentation refresh + changelog

## 📝 Documentation Standards

### README.md Template
```markdown
# Title

## Overview
Brief description

## Quick Start
Code example

## Details
In-depth explanation

## Related
- [Link to related doc](path)
```

### API Documentation Format
```markdown
### POST /api/endpoint

Description

**Request:**
\`\`\`json
{}
\`\`\`

**Response:**
\`\`\`json
{}
\`\`\`

**Errors:**
- 400: Bad request
- 401: Unauthorized
```

## 🏷️ Versioning

All docs include:
- Last updated timestamp
- Version number (if applicable)
- Author/owner
