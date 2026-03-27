# PhysiqAI Data Schema

## Firestore Collections
Generated: 2026-03-26 18:00 UTC

### users/
```json
{
  "uid": "string",
  "email": "string",
  "profile": {
    "name": "string",
    "height": "number",
    "age": "number",
    "gender": "string"
  },
  "created_at": "timestamp"
}
```

### weight_logs/
```json
{
  "user_id": "string",
  "date": "timestamp",
  "weight": "number",
  "moving_avg": "number",
  "notes": "string"
}
```

### workouts/
```json
{
  "user_id": "string",
  "date": "timestamp",
  "name": "string",
  "exercises": ["array"],
  "volume": "number"
}
```

### avatar_state/
```json
{
  "user_id": "string",
  "current_params": {
    "smpl_betas": ["array"],
    "measurements": "object"
  },
  "target_params": "object",
  "created_at": "timestamp"
}
```

