# UUID & Soft Delete with Data Recovery

This document explains the new UUID and soft delete features with 7-day recovery window.

## Overview

### Benefits
- **Data Safety**: Soft deletes allow data recovery within 7 days
- **Better ID Management**: UUIDs are globally unique and don't expose sequential information
- **Audit Trail**: All soft-deleted records are timestamped for compliance
- **Data Privacy**: Users can request deletion with clear recovery deadline

---

## Database Changes

### All User-Related Tables Now Use UUID

#### Users Table
```
users (Updated)
├── id (UUID, PRIMARY KEY) ← Changed from Integer
├── username (STRING, UNIQUE)
├── email (STRING, UNIQUE)
├── is_active (BOOLEAN)
├── created_at (DATETIME)
├── updated_at (DATETIME)
└── deleted_at (DATETIME, NULLABLE) ← NEW: Soft delete timestamp
```

#### Hyperparameter Configs Table
```
hyperparameter_configs (Updated)
├── id (INTEGER, PRIMARY KEY)
├── user_id (UUID, FK) ← Changed from Integer
├── model_id (INTEGER, FK)
├── parameters (JSON)
├── description (STRING, NULLABLE)
├── is_default (BOOLEAN)
├── created_at (DATETIME)
├── updated_at (DATETIME)
└── deleted_at (DATETIME, NULLABLE) ← NEW: Soft delete timestamp
```

#### LLM Call History Table
```
llm_call_history (Updated)
├── id (INTEGER, PRIMARY KEY)
├── user_id (UUID, FK) ← Changed from Integer
├── provider_id (INTEGER, FK)
├── model_id (INTEGER, FK)
├── prompt (STRING)
├── response (STRING)
├── parameters_used (JSON)
├── tokens_input (INTEGER, NULLABLE)
├── tokens_output (INTEGER, NULLABLE)
├── total_tokens (INTEGER, NULLABLE)
├── cost (FLOAT, NULLABLE)
├── status (STRING)
├── error_message (STRING, NULLABLE)
├── created_at (DATETIME)
└── deleted_at (DATETIME, NULLABLE) ← NEW: Soft delete timestamp
```

---

## Data Recovery & Cleanup

### Timeline
- **Day 0**: User is soft-deleted (all their data is hidden but not deleted)
- **Days 1-6**: Data can be restored at any time
- **Day 7**: Automatic hard delete occurs (data is permanently deleted)

---

## Soft Delete Behavior

### What Happens When User is Deleted?

1. **User record**: `deleted_at` timestamp is set
2. **Call history**: All records get `deleted_at` timestamp
3. **Hyperparameter configs**: All records get `deleted_at` timestamp
4. **Query filters**: All queries automatically exclude soft-deleted records

### Example

**Before Deletion:**
```
User ID: 550e8400-e29b-41d4-a716-446655440000
├── Call history: 45 records
└── Configs: 12 records

Total in DB: 58 records
```

**After Soft Delete:**
```
User ID: 550e8400-e29b-41d4-a716-446655440000
├── deleted_at: 2026-02-16T10:00:00Z
├── Call history: 45 records (all marked deleted_at)
└── Configs: 12 records (all marked deleted_at)

Visible in API: 0 records (filtered out)
Hard delete deadline: 2026-02-23T10:00:00Z
```

---

## API Endpoints

### 1. Preview Deletion (Before Actually Deleting)

**Get deletion preview:**
```bash
GET /admin/users/{user_id}/deletion-preview

Response: 200 OK
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "john_doe",
  "email": "john@example.com",
  "total_call_history_records": 45,
  "total_hyperparameter_configs": 12,
  "recovery_deadline": "2026-02-23T10:00:00Z",
  "message": "User 'john_doe' will be deleted along with:\n- 45 LLM call history records\n- 12 hyperparameter configurations\n\nThe data will be retained for 7 days and can be restored until 2026-02-23T10:00:00Z UTC.\nAfter this period, all data will be permanently deleted."
}
```

**Use Case**: Show this to user before confirming deletion.

---

### 2. Soft Delete User

**Delete a user:**
```bash
DELETE /admin/users/{user_id}

Response: 200 OK
{
  "message": "User soft deleted successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "deleted_at": "2026-02-16T10:00:00Z",
  "recovery_deadline": "2026-02-23T10:00:00Z"
}
```

After deletion:
- User is no longer visible in `GET /admin/users`
- All their history and configs are hidden
- Data can still be restored for 7 days

---

### 3. Restore Deleted User

**Restore within 7 days:**
```bash
POST /admin/users/{user_id}/restore

Response: 200 OK
{
  "message": "User and associated data restored successfully",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "restored_at": "2026-02-16T14:30:00Z"
}
```

**After 7 days:**
```bash
POST /admin/users/{user_id}/restore

Response: 400 Bad Request
{
  "detail": "Recovery window has expired. Data was permanently deleted on 2026-02-23T10:00:00Z"
}
```

---

### 4. List Soft-Deleted Users

**View all soft-deleted users:**
```bash
GET /admin/users/deleted/list

Response: 200 OK
{
  "total": 2,
  "users": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "john_doe",
      "email": "john@example.com",
      "deleted_at": "2026-02-16T10:00:00Z",
      "recovery_deadline": "2026-02-23T10:00:00Z",
      "is_expired": false
    },
    {
      "user_id": "650e8400-e29b-41d4-a716-446655440001",
      "username": "jane_smith",
      "email": "jane@example.com",
      "deleted_at": "2026-02-09T08:00:00Z",
      "recovery_deadline": "2026-02-16T08:00:00Z",
      "is_expired": true
    }
  ]
}
```

---

### 5. Trigger Hard Delete (Cleanup)

**Permanently delete expired records:**
```bash
POST /admin/maintenance/hard-delete-expired

Response: 200 OK
{
  "message": "Hard deleted 2 expired users",
  "deleted_count": 2,
  "deleted_user_ids": [
    "650e8400-e29b-41d4-a716-446655440001",
    "750e8400-e29b-41d4-a716-446655440002"
  ],
  "cutoff_date": "2026-02-09T10:00:00Z"
}
```

**When to call**: Daily via cron job or scheduled task.
**What it does**: Permanently deletes users who were soft-deleted >7 days ago.

---

### 6. View Soft-Deleted Records

**Get all users (including deleted):**
```bash
GET /admin/users?include_deleted=true

Response: 200 OK
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": false,
    "created_at": "2026-02-01T10:00:00Z",
    "updated_at": "2026-02-16T10:00:00Z",
    "deleted_at": "2026-02-16T10:00:00Z"
  }
]
```

---

## UUID Format

### What Changed
- User ID is now a **UUID (Universally Unique Identifier)**
- Format: `550e8400-e29b-41d4-a716-446655440000`
- Automatically generated when user is created
- Used in all API requests

### Example Request with UUID

**Before (Integer ID):**
```bash
POST /api/generate
{
  "user_id": 1,
  "provider": "azure",
  "model": "gpt-4",
  "prompt": "Hello"
}
```

**After (UUID):**
```bash
POST /api/generate
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "azure",
  "model": "gpt-4",
  "prompt": "Hello"
}
```

---

## Implementation Guide

### Step 1: Create a User
```bash
POST /admin/users
{
  "username": "alice_wonder",
  "email": "alice@example.com"
}

Response:
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  ...
}
```

### Step 2: Generate LLM Calls (Using UUID)
```bash
POST /api/generate
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "provider": "azure",
  "model": "gpt-4",
  "prompt": "Explain quantum computing"
}
```

### Step 3: Preview Before Deletion
```bash
GET /admin/users/550e8400-e29b-41d4-a716-446655440000/deletion-preview
```

### Step 4: Delete User
```bash
DELETE /admin/users/550e8400-e29b-41d4-a716-446655440000
```

### Step 5: Restore Within 7 Days (if needed)
```bash
POST /admin/users/550e8400-e29b-41d4-a716-446655440000/restore
```

### Step 6: Run Cleanup (Daily)
```bash
# Schedule this daily (via cron or task scheduler)
POST /admin/maintenance/hard-delete-expired
```

---

## Compliance Benefits

### GDPR Compliance
- ✅ Right to be forgotten (soft delete visible to user)
- ✅ Data recovery period (7 days to change mind)
- ✅ Audit trail (timestamped deletions)
- ✅ Full data purge (hard delete after period)

### Data Privacy
- ✅ Users can request deletion
- ✅ Clear recovery deadline
- ✅ Automatic permanent deletion
- ✅ No manual intervention needed

---

## Important Notes

1. **Queries automatically filter soft-deleted data**: Regular API calls won't see deleted users
2. **Only admins can restore**: Use `/admin/users/{user_id}/restore`
3. **Hard delete is automatic**: No manual cleanup needed after 7 days
4. **Call `/admin/maintenance/hard-delete-expired` regularly**: Recommended daily

---

## Migration Info

If migrating from old integer-based user IDs:
1. Run database migration to add UUID column
2. Generate UUIDs for existing users
3. Update foreign keys in related tables
4. Run tests to verify UUID relationships

See database migration scripts in `migrations/` folder.
