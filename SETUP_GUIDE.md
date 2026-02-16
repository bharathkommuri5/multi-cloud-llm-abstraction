# Installation & Setup Guide for UUID & Soft Delete Features

## Prerequisites
- Python 3.10+
- PostgreSQL (recommended for UUID support)
- SQLite (should work but UUID handling differs)

## Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Update Database Configuration
Edit `.env`:
```env
# For PostgreSQL
DATABASE_URL=postgresql://user:password@localhost/llm_db

# For SQLite (still works, but UUIDs handled differently)
DATABASE_URL=sqlite:///./llm.db
```

### 3. Run Database Migrations
```bash
# The models are auto-created in main.py, but for production use:
# python -m alembic upgrade head
```

### 4. Verify Tables Are Created
```bash
# Check your database has these columns:
# users.id (UUID)
# users.deleted_at (DATETIME)
# llm_call_history.user_id (UUID)
# llm_call_history.deleted_at (DATETIME)
# hyperparameter_configs.user_id (UUID)
# hyperparameter_configs.deleted_at (DATETIME)
```

### 5. Start the Server
```bash
uvicorn app.main:app --reload
```

---

## Quick Start Examples

### Create a User
```bash
curl -X POST http://localhost:8000/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com"
  }'
```

Response will contain UUID:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "testuser",
  "email": "test@example.com",
  "is_active": true,
  "created_at": "2026-02-16T10:00:00Z",
  "updated_at": "2026-02-16T10:00:00Z",
  "deleted_at": null
}
```

### Generate LLM Call (With UUID)
```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "provider": "azure",
    "model": "gpt-4",
    "prompt": "What is AI?",
    "temperature": 0.7,
    "max_tokens": 300
  }'
```

### Preview Deletion
```bash
curl -X GET http://localhost:8000/admin/users/550e8400-e29b-41d4-a716-446655440000/deletion-preview
```

### Soft Delete User
```bash
curl -X DELETE http://localhost:8000/admin/users/550e8400-e29b-41d4-a716-446655440000
```

### Restore User (Within 7 Days)
```bash
curl -X POST http://localhost:8000/admin/users/550e8400-e29b-41d4-a716-446655440000/restore
```

### List Deleted Users
```bash
curl -X GET http://localhost:8000/admin/users/deleted/list
```

### Hard Delete Expired Records (Run Daily)
```bash
curl -X POST http://localhost:8000/admin/maintenance/hard-delete-expired
```

---

## Scheduled Task Setup

### Option 1: Using APScheduler (Python)
```python
from apscheduler.schedulers.background import BackgroundScheduler
import requests

scheduler = BackgroundScheduler()

def cleanup_job():
    requests.post("http://localhost:8000/admin/maintenance/hard-delete-expired")

scheduler.add_job(cleanup_job, 'cron', hour=2, minute=0)  # Daily at 2 AM
scheduler.start()
```

### Option 2: Using Cron (Linux/Mac)
```bash
# Add to crontab
0 2 * * * curl -X POST http://localhost:8000/admin/maintenance/hard-delete-expired
```

### Option 3: Using Windows Task Scheduler
1. Create a `.bat` file:
```batch
@echo off
curl -X POST http://localhost:8000/admin/maintenance/hard-delete-expired
```
2. Schedule it to run daily at 2 AM

---

## Testing

### Create Test Data
```python
import requests
from uuid import uuid4

# Create user
user_resp = requests.post(
    "http://localhost:8000/admin/users",
    json={"username": "testuser", "email": "test@example.com"}
)
user_id = user_resp.json()["id"]

# Generate LLM call
call_resp = requests.post(
    "http://localhost:8000/api/generate",
    json={
        "user_id": user_id,
        "provider": "azure",
        "model": "gpt-4",
        "prompt": "Test prompt"
    }
)

# Preview deletion
preview = requests.get(
    f"http://localhost:8000/admin/users/{user_id}/deletion-preview"
)
print(preview.json()["message"])

# Soft delete
delete = requests.delete(
    f"http://localhost:8000/admin/users/{user_id}"
)
print(delete.json())

# Try to restore
restore = requests.post(
    f"http://localhost:8000/admin/users/{user_id}/restore"
)
print(restore.json())
```

---

## Troubleshooting

### Issue: "Invalid user ID format"
**Cause**: Passing integer instead of UUID
**Fix**: Use full UUID format: `550e8400-e29b-41d4-a716-446655440000`

### Issue: "User not found or has been deleted"
**Cause**: User was soft-deleted or doesn't exist
**Fix**: Check if user is deleted: `GET /admin/users/deleted/list`

### Issue: "Recovery window has expired"
**Cause**: Trying to restore user after 7 days
**Fix**: User data was permanently deleted automatically

### Issue: UUID import error
**Cause**: SQLAlchemy/PostgreSQL version mismatch
**Fix**: Update packages: `pip install --upgrade sqlalchemy psycopg2-binary`

---

## Key Files Modified

- `app/models/user.py` - UUID primary key + deleted_at
- `app/models/hyperparameter_config.py` - UUID foreign key + deleted_at
- `app/models/llm_call_history.py` - UUID foreign key + deleted_at
- `app/schemas/user.py` - UUID types + deletion schemas
- `app/schemas/request.py` - UUID for user_id
- `app/schemas/history.py` - UUID + deleted_at fields
- `app/schemas/hyperparameter.py` - UUID + deleted_at fields
- `app/api/routes.py` - UUID handling + soft delete filtering
- `app/api/admin_routes.py` - New deletion/restore endpoints
- `app/core/deletion_service.py` - **NEW** - Soft delete utilities

---

## Architecture

```
User deletes account
         ↓
Preview deletion (shows what will be deleted)
         ↓
Confirm deletion
         ↓
Soft delete (deleted_at timestamp set)
         ↓ (Within 7 days)
Restore available
         ↓ (After 7 days)
Hard delete (automatic, permanent)
```

---

## Next Steps

1. Install dependencies
2. Configure database URL in `.env`
3. Start the server
4. Create test users
5. Set up daily cleanup task
6. Integrate with frontend UI

---

## Support

For issues or questions, check:
- `UUID_SOFT_DELETE.md` - Full feature documentation
- `FEATURES.md` - All features overview
- Database migration guide in `migrations/` (if using)
