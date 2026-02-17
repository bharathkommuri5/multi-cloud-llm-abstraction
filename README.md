# multi-cloud-llm-abstraction
A unified abstraction layer for interacting with Azure OpenAI, AWS Bedrock, and Google Generative AI using a common interface.

## Google Sign-In / Backend token exchange

This project includes a simple backend endpoint to exchange a Google ID token (from Google Identity Services) for a backend-issued JWT access token.

Example `.env` entries:

```
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_API_KEY=...
JWT_SECRET=replace-with-a-secure-random-string
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
API_TOKEN=some-internal-api-token-for-swagger
```

How it works (recommended production flow):
- Frontend implements Google Sign-In and obtains a Google ID token (JWT).
- Frontend POSTs the ID token to `POST /api/v1/auth/google`.
- Backend verifies the ID token with Google's public keys, upserts the user, and issues a short-lived backend JWT access token.
- Use the backend-issued token in `Authorization: Bearer <token>` (paste into Swagger Authorize or include in API clients).

Notes:
- For production, validate audience (`aud`) equals your `GOOGLE_CLIENT_ID` and use HTTPS.
- Prefer issuing your own short-lived tokens and refresh tokens rather than using Google ID tokens directly as API credentials.

