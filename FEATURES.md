# Multi-Cloud LLM Abstraction - Feature Documentation

## New Features: User Management, Hyperparameter Configuration, and Call History

### Overview

This update adds three major features:
1. **User Management** - Track users and their LLM usage
2. **Model-Specific Hyperparameter Configuration** - Store different hyperparameters for different models per user
3. **LLM Call History** - Log and retrieve all LLM API calls for audit trails and usage analysis

---

## Database Schema

### 1. Users Table
```
users
├── id (PK)
├── username (STRING, UNIQUE)
├── email (STRING, UNIQUE)
├── is_active (BOOLEAN)
├── created_at (DATETIME)
└── updated_at (DATETIME)
```

**Purpose**: Store user information and track which user made which LLM calls.

---

### 2. Hyperparameter Configs Table
```
hyperparameter_configs
├── id (PK)
├── user_id (FK → users.id)
├── model_id (FK → llm_models.id)
├── parameters (JSON)
│   └── Example: {"temperature": 0.7, "top_p": 0.9, "presence_penalty": 0.5}
├── description (STRING, NULLABLE)
├── is_default (BOOLEAN)
├── created_at (DATETIME)
└── updated_at (DATETIME)
```

**Purpose**: Store model-specific hyperparameter configurations for each user.
- One config per user-model combination (can have multiple)
- `is_default` flag to mark the preferred config for a model
- Parameters stored as JSON (flexible for different model types)

---

### 3. LLM Call History Table
```
llm_call_history
├── id (PK)
├── user_id (FK → users.id)
├── provider_id (FK → providers.id)
├── model_id (FK → llm_models.id)
├── prompt (STRING)
├── response (STRING)
├── parameters_used (JSON)
├── tokens_input (INTEGER, NULLABLE)
├── tokens_output (INTEGER, NULLABLE)
├── total_tokens (INTEGER, NULLABLE)
├── cost (FLOAT, NULLABLE)
├── status (STRING) [success/error/timeout]
├── error_message (STRING, NULLABLE)
└── created_at (DATETIME)
```

**Purpose**: Audit trail and history tracking for all LLM calls.
- Track all requests and responses
- Store the exact parameters used
- Record token usage and costs (for future billing)
- Status tracking for error handling

---

## API Endpoints

### User Management Endpoints

#### Create User
```bash
POST /admin/users
Content-Type: application/json

{
  "username": "john_doe",
  "email": "john@example.com"
}

Response: 201 Created
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "is_active": true,
  "created_at": "2026-02-16T10:00:00Z",
  "updated_at": "2026-02-16T10:00:00Z"
}
```

#### Get All Users
```bash
GET /admin/users

Response: 200 OK
[
  {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "is_active": true,
    "created_at": "2026-02-16T10:00:00Z",
    "updated_at": "2026-02-16T10:00:00Z"
  }
]
```

#### Get Specific User
```bash
GET /admin/users/{user_id}
```

#### Update User
```bash
PUT /admin/users/{user_id}
{
  "username": "jane_doe",
  "email": "jane@example.com"
}
```

#### Delete User (Soft Delete)
```bash
DELETE /admin/users/{user_id}
```

---

### Hyperparameter Configuration Endpoints

#### Create Hyperparameter Config
```bash
POST /admin/users/{user_id}/hyperparameters
Content-Type: application/json

{
  "model_id": 1,
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9,
    "frequency_penalty": 0.5,
    "presence_penalty": 0
  },
  "description": "Balanced config for GPT-4",
  "is_default": true
}

Response: 201 Created
{
  "id": 1,
  "user_id": 1,
  "model_id": 1,
  "parameters": {
    "temperature": 0.7,
    "top_p": 0.9,
    "frequency_penalty": 0.5,
    "presence_penalty": 0
  },
  "description": "Balanced config for GPT-4",
  "is_default": true,
  "created_at": "2026-02-16T10:00:00Z",
  "updated_at": "2026-02-16T10:00:00Z"
}
```

**Note**: Different models support different hyperparameters:
- **Claude**: `temperature`, `max_tokens`, `top_p`, `top_k`
- **GPT (OpenAI)**: `temperature`, `max_tokens`, `top_p`, `frequency_penalty`, `presence_penalty`
- **Bedrock**: Model-dependent
- **Gemini (Google)**: `temperature`, `max_output_tokens`, `top_p`, `top_k`

#### Get All Configs for User
```bash
GET /admin/users/{user_id}/hyperparameters
```

#### Get Specific Config
```bash
GET /admin/users/{user_id}/hyperparameters/{config_id}
```

#### Update Config
```bash
PUT /admin/users/{user_id}/hyperparameters/{config_id}
{
  "parameters": {
    "temperature": 0.5
  },
  "is_default": true
}
```

#### Delete Config
```bash
DELETE /admin/users/{user_id}/hyperparameters/{config_id}
```

---

### LLM Call Generation (Updated)

#### Generate LLM Response
```bash
POST /api/generate
Content-Type: application/json

{
  "user_id": 1,
  "provider": "azure",
  "model": "gpt-4",
  "prompt": "What is machine learning?",
  "temperature": 0.7,
  "max_tokens": 300,
  "hyperparameter_config_id": 1  // Optional: use saved config
}

Response: 200 OK
{
  "provider": "azure",
  "model": "gpt-4",
  "response": "Machine learning is a subset of artificial intelligence...",
  "history_id": 1001
}
```

**How it works**:
1. If `hyperparameter_config_id` is provided, load those parameters
2. If `custom_parameters` is provided, override specific values
3. Apply to the LLM call
4. Log the entire call to `llm_call_history` table with actual parameters used
5. Return `history_id` for future reference

---

### Call History Endpoints

#### Get User's Call History
```bash
GET /api/history?user_id=1&limit=50&offset=0

Response: 200 OK
[
  {
    "id": 1001,
    "user_id": 1,
    "provider_id": 1,
    "model_id": 1,
    "prompt": "What is machine learning?",
    "response": "Machine learning is a subset of artificial intelligence...",
    "parameters_used": {
      "temperature": 0.7,
      "max_tokens": 300
    },
    "tokens_input": 10,
    "tokens_output": 50,
    "total_tokens": 60,
    "cost": 0.0015,
    "status": "success",
    "error_message": null,
    "created_at": "2026-02-16T10:00:00Z"
  }
]
```

#### Get Specific Call Details
```bash
GET /api/history/{history_id}

Response: 200 OK
{
  "id": 1001,
  "user_id": 1,
  "provider_id": 1,
  "model_id": 1,
  "prompt": "What is machine learning?",
  "response": "Machine learning is a subset of artificial intelligence...",
  "parameters_used": {
    "temperature": 0.7,
    "max_tokens": 300
  },
  "tokens_input": 10,
  "tokens_output": 50,
  "total_tokens": 60,
  "cost": 0.0015,
  "status": "success",
  "error_message": null,
  "created_at": "2026-02-16T10:00:00Z"
}
```

---

## Usage Workflow

### Example: Setting up a user with model-specific configs

1. **Create a user**:
```bash
POST /admin/users
{
  "username": "data_scientist_1",
  "email": "ds1@company.com"
}
# Returns: user_id = 1
```

2. **Create hyperparameter configs for different models**:

For GPT-4 (more creative):
```bash
POST /admin/users/1/hyperparameters
{
  "model_id": 1,  // gpt-4
  "parameters": {
    "temperature": 0.9,
    "top_p": 0.95,
    "frequency_penalty": 0.0,
    "presence_penalty": 0.0
  },
  "description": "Creative writing config for GPT-4",
  "is_default": false
}
```

For Claude (more precise):
```bash
POST /admin/users/1/hyperparameters
{
  "model_id": 2,  // claude
  "parameters": {
    "temperature": 0.5,
    "top_p": 0.8,
    "top_k": 40
  },
  "description": "Precise code generation config for Claude",
  "is_default": true
}
```

3. **Make LLM calls using the configs**:

Using saved config:
```bash
POST /api/generate
{
  "user_id": 1,
  "provider": "azure",
  "model": "gpt-4",
  "prompt": "Write a creative story about AI",
  "hyperparameter_config_id": 1
}
```

With custom override:
```bash
POST /api/generate
{
  "user_id": 1,
  "provider": "openai",
  "model": "claude",
  "prompt": "Write Python code for bubble sort",
  "hyperparameter_config_id": 2,
  "custom_parameters": {
    "temperature": 0.3  // Override temp to be even more precise
  }
}
```

4. **Review call history**:
```bash
GET /api/history?user_id=1
```

---

## Benefits

### For Users
- Save and reuse hyperparameter configurations
- Track all their LLM usage
- View cost/token analytics
- Compare different configurations

### For Admins
- Full audit trail of all LLM calls
- User usage analytics
- Cost tracking per user
- Model performance monitoring

### For Frontend
- Configuration UI to manage hyperparameters per model
- History view showing all past calls
- Allow users to regenerate with different configs
- Usage dashboard and analytics

---

## Future Enhancements

1. **Cost Tracking**: Add pricing per model and track costs automatically
2. **Token Prediction**: Estimate tokens before making requests
3. **Rate Limiting**: Per-user or per-model rate limits
4. **A/B Testing**: Test different configs on same models
5. **Conversation Sessions**: Group related calls into sessions
6. **Favorite Configs**: Star/favorite configs for quick access
7. **Config Templates**: Pre-built configs for common use cases (summarization, Q&A, code generation)
