# multi-cloud-llm-abstraction

A unified abstraction layer for interacting with Azure OpenAI, AWS Bedrock, Google Generative AI, Grok, and more using a common interface.

## Features

- **Multi-Provider LLM Support**: Unified API for Azure OpenAI, AWS Bedrock, Google Generative AI, Grok
- **Multi-Provider OAuth**: Sign-in with Google, Microsoft, GitHub (extensible for any OAuth provider)
- **User Management**: Automatic user registration on first sign-in, user profiles
- **Bearer Token Authentication**: JWT-based API access control
- **Stateless Auth**: OAuth tokens exchanged for backend JWT tokens
- **Production-Grade Logging**: Comprehensive logging to file and console with rotation
- **API Documentation**: Auto-generated Swagger docs with Bearer auth support

## Quick Start: OAuth Authentication

This project supports multi-provider OAuth authentication (Google, Microsoft, GitHub) with automatic user registration.

### Supported OAuth Providers

- ✅ **Google** - Gmail/Google Account sign-in
- ✅ **Microsoft** - Azure AD / Office 365 sign-in  
- ✅ **GitHub** - GitHub account sign-in
- 🔧 Easily extensible for Okta, Auth0, etc.

### Setup

Environment variables (`.env`):

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_API_KEY=your-google-api-key

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-client-id
GITHUB_CLIENT_SECRET=your-client-secret

# Backend JWT
JWT_SECRET=replace-with-a-secure-random-string
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### OAuth Endpoints

```bash
# Get available providers
GET /auth/providers
→ { "providers": ["google", "microsoft", "github"] }

# Register new user (creates account if email not registered)
POST /auth/register
{
  "provider": "google",  # or "microsoft", "github"
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
→ { "access_token": "...", "user_id": "...", "is_new_user": true, "provider": "google" }

# Login existing user
POST /auth/login
{
  "provider": "google",
  "id_token": "eyJhbGciOiJSUzI1NiIs..."
}
→ { "access_token": "...", "user_id": "...", "is_new_user": false, "provider": "google" }

# Get current user profile (requires Bearer token)
GET /auth/profile
Authorization: Bearer <your-jwt-token>
→ { "user_id": "...", "email": "..." }

# Logout
POST /auth/logout
```

### Example: Register and Login with Google

```bash
# First time: Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMz..."
  }'

# Response: User created
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_email": "user@gmail.com",
  "is_new_user": true,
  "provider": "google"
}

# Subsequent times: Login with same token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEyMz..."
  }'

# Response: User authenticated
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_email": "user@gmail.com",
  "is_new_user": false,
  "provider": "google"
}

# Use token for API calls
curl -X POST http://localhost:8000/api/v1/llm/call \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "model": "gemini-pro",
    "prompt": "Hello AI!"
  }'
```

### How It Works (OAuth Flow)

1. **Frontend** implements sign-in UI with chosen provider (Google, Microsoft, or GitHub)
2. **Frontend** gets OAuth ID token from provider's SDK
3. **Frontend** POSTs token to `/auth/register` (first time) or `/auth/login` (subsequent)
4. **Backend** verifies token with provider's public keys/API
5. **Backend** creates/finds user in database
6. **Backend** issues JWT access token (valid for 60 minutes by default)
7. **Frontend** stores JWT and includes in `Authorization: Bearer <token>` header
8. **Backend** validates JWT on protected routes (LLM endpoints, profile, etc.)

## LLM API

### Call LLM Provider

```bash
POST /api/v1/llm/call
Authorization: Bearer <your-jwt-token>

{
  "provider": "google",  # or "azure", "bedrock", "grok"
  "model": "gemini-pro",
  "prompt": "Tell me about machine learning",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

### Supported LLM Providers

| Provider | Models | Status |
|----------|--------|--------|
| **Google** | `gemini-pro`, `gemini-pro-vision` | ✅ Active |
| **Azure OpenAI** | `gpt-4`, `gpt-35-turbo` | ✅ Active |
| **AWS Bedrock** | `anthropic.claude-3-sonnet-20240229-v1:0` | ✅ Active |
| **Grok** | `grok-beta` | ✅ Active |

## Installation

```bash
# Clone repository
git clone <repo-url>
cd multi-cloud-llm-abstraction

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys and OAuth credentials

# Run server
python -m uvicorn app.main:app --reload
```

Server runs on `http://localhost:8000`

## API Documentation

Access Swagger UI at: **http://localhost:8000/docs**

In Swagger, use the green "Authorize" button at the top-right to paste your Bearer token for testing protected endpoints.

## Architecture

```
app/
├── main.py                      # FastAPI app, middleware setup
├── core/
│   ├── config.py               # Settings & environment variables
│   ├── database.py             # SQLAlchemy session
│   ├── auth_middleware.py      # JWT validation middleware
│   └── exceptions.py           # Custom exceptions
├── api/v1/endpoints/
│   ├── auth.py                # OAuth endpoints (register, login, profile)
│   ├── llm.py                 # LLM call endpoint
│   └── ...
├── services/
│   ├── oauth_service.py       # OAuth provider factory & implementations
│   ├── llm_service.py         # LLM provider factory & orchestration
│   └── ...
├── llm/
│   ├── base.py                # LLM client base class
│   ├── google_client.py        # Google provider implementation
│   ├── azure_client.py         # Azure provider implementation
│   ├── bedrock_client.py       # AWS provider implementation
│   └── grok_client.py          # Grok provider implementation
├── models/
│   ├── user.py                # User database model
│   └── ...
├── schemas/
│   ├── auth.py                # OAuth request/response schemas
│   ├── request.py             # LLM request schema
│   ├── response.py            # LLM response schema
│   └── ...
└── utils/
    ├── logger.py              # Centralized logging
    └── helpers.py             # Utility functions (JWT, validation, etc.)
```

## Security Best Practices

- **JWT tokens** expire after configured time (default: 60 minutes)
- **Bearer auth** required for all protected endpoints
- **OAuth tokens** never stored; exchanged immediately for JWT
- **Passwords** not used; OAuth providers handle authentication
- **HTTPS** required in production (redirects must use `https://`)
- **CORS** configured for trusted frontend origins only
- **Environment variables** used for all secrets (never commit `.env` to git)

## Error Handling

| Status | Error | Solution |
|--------|-------|----------|
| **400** | "Unsupported provider" | Ensure provider is configured in `.env` |
| **401** | "Invalid [provider] token" | Token expired or invalid; get new token from provider |
| **404** | "User not found. Please register first." | Use `/auth/register` instead of `/auth/login` |
| **409** | "User already registered. Use login instead." | Use `/auth/login` instead of `/auth/register` |
| **500** | "Server JWT secret not configured" | Add `JWT_SECRET` to `.env` |

## Adding New OAuth Providers

To support a new OAuth provider (e.g., Okta, Auth0):

1. **Create provider class** in `app/services/oauth_service.py`:
   ```python
   class OktaOAuthProvider(OAuthProvider):
       def verify_token(self, token: str) -> Dict[str, str]:
           # Call Okta API to verify token
           # Return: {"email": "...", "name": "...", "sub": "...", "provider": "okta", "raw_payload": {...}}
   ```

2. **Register in factory** (in `OAuthProviderFactory.get_provider()`):
   ```python
   elif provider == "okta":
       if not settings.OKTA_CLIENT_ID:
           raise ValueError("Okta client ID not configured")
       return OktaOAuthProvider(client_id=settings.OKTA_CLIENT_ID)
   ```

3. **Add environment variables** to `.env.example`

4. **Update schemas** in `app/schemas/auth.py` to allow new provider

## License

See [LICENSE](./LICENSE)