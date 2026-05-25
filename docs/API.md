# API Documentation

## Endpoints Overview

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login with credentials
- `POST /auth/google-login` - Google OAuth login
- `GET /auth/verify-email` - Verify email address
- `POST /auth/refresh-token` - Refresh access token

### Presentations
- `GET /presentations` - List user presentations
- `POST /presentations/upload` - Upload document
- `GET /presentations/{id}` - Get presentation details
- `PUT /presentations/{id}` - Update presentation
- `DELETE /presentations/{id}` - Delete presentation

### Avatars
- `GET /avatars` - List available avatars
- `GET /avatars/{id}` - Get avatar details

### Voices
- `GET /voices` - List available voices
- `GET /voices/languages` - List supported languages
- `POST /voices/upload` - Upload custom voice

### API Keys
- `GET /api-keys` - List user API keys
- `POST /api-keys` - Generate new API key
- `DELETE /api-keys/{id}` - Revoke API key

---

## Authentication Flow

1. User registers with email/password or Google OAuth
2. Email verification required (for email signup)
3. Token generated upon successful login
4. Access token used in Authorization header: `Bearer {token}`

---

## Rate Limiting

Default: 60 requests per minute per user
Premium: Higher limits based on subscription

---

More detailed documentation to be added during implementation.
