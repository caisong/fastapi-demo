# JWT Authentication for Regular Users

This document explains how regular users can use JWT (JSON Web Token) authentication in the FastAPI application.

## Overview

The application provides a complete JWT authentication system that allows regular users to:
- Register new accounts
- Login and receive JWT tokens
- Access protected endpoints using JWT tokens
- Refresh expired tokens
- Maintain secure sessions

## Authentication Flow

### 1. User Registration

**Endpoint**: `POST /api/v1/auth/register`
**Access**: Public (no authentication required)

```bash
curl -X POST "http://localhost:8010/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Response**:
```json
{
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "first_name": "John",
  "last_name": "Doe",
  "id": 5,
  "created_at": "2025-09-04T12:15:30.123456Z",
  "updated_at": null
}
```

### 2. User Login

#### Option A: OAuth2 Compatible Login (Form-based)

**Endpoint**: `POST /api/v1/auth/login`
**Content-Type**: `application/x-www-form-urlencoded`

```bash
curl -X POST "http://localhost:8010/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepassword123"
```

#### Option B: JSON Login (Web-friendly)

**Endpoint**: `POST /api/v1/auth/login-json`
**Content-Type**: `application/json`

```bash
curl -X POST "http://localhost:8010/api/v1/auth/login-json" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepassword123"
  }'
```

**Response** (both methods):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 5,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_superuser": false
  }
}
```

### 3. Accessing Protected Endpoints

Once you have an access token, include it in the Authorization header:

```bash
curl -X GET "http://localhost:8010/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response**:
```json
{
  "email": "user@example.com",
  "is_active": true,
  "is_superuser": false,
  "first_name": "John",
  "last_name": "Doe",
  "id": 5,
  "created_at": "2025-09-04T12:15:30.123456Z",
  "updated_at": null
}
```

### 4. Token Refresh

When your access token expires, use the refresh token to get new tokens:

**Endpoint**: `POST /api/v1/auth/refresh`

```bash
curl -X POST "http://localhost:8010/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

**Response**:
```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "bearer"
}
```

### 5. Token Validation

Test if your current token is valid:

**Endpoint**: `POST /api/v1/auth/test-token`

```bash
curl -X POST "http://localhost:8010/api/v1/auth/test-token" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Response**:
```json
{
  "message": "Token is valid",
  "user_id": 5,
  "email": "user@example.com"
}
```

## JWT Token Structure

### Access Token
- **Purpose**: Authenticate API requests
- **Expiration**: 24 hours (configurable)
- **Usage**: Include in Authorization header as `Bearer TOKEN`

### Refresh Token
- **Purpose**: Obtain new access tokens
- **Expiration**: 30 days (configurable)
- **Usage**: Send to refresh endpoint when access token expires

## Available Endpoints for Regular Users

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/v1/auth/register` | POST | ❌ No | Register new user |
| `/api/v1/auth/login` | POST | ❌ No | OAuth2 login |
| `/api/v1/auth/login-json` | POST | ❌ No | JSON login |
| `/api/v1/auth/refresh` | POST | ❌ No | Refresh tokens |
| `/api/v1/auth/test-token` | POST | ✅ Yes | Validate token |
| `/api/v1/users/me` | GET | ✅ Yes | Get profile |
| `/api/v1/users/me` | PUT | ✅ Yes | Update profile |
| `/api/v1/items/` | GET | ✅ Yes | List user's items |
| `/api/v1/items/` | POST | ✅ Yes | Create item |
| `/api/v1/items/{id}` | GET | ✅ Yes | Get item |
| `/api/v1/items/{id}` | PUT | ✅ Yes | Update item |
| `/api/v1/items/{id}` | DELETE | ✅ Yes | Delete item |

## Security Features

✅ **Password Security**: Bcrypt hashing with salt  
✅ **Token Security**: JWT with configurable expiration  
✅ **Permission Control**: Separation between regular and admin users  
✅ **Input Validation**: Pydantic schemas for all requests  
✅ **CORS Protection**: Configurable allowed origins  
✅ **Rate Limiting**: Configurable request limits  

## Error Handling

### Common Error Responses

**401 Unauthorized** - Invalid credentials or expired token:
```json
{
  "detail": "Incorrect email or password"
}
```

**400 Bad Request** - Insufficient privileges:
```json
{
  "detail": "The user doesn't have enough privileges"
}
```

**422 Validation Error** - Invalid input data:
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Configuration

JWT settings can be configured in `.env` file:

```env
# JWT Configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
REFRESH_TOKEN_EXPIRE_MINUTES=43200  # 30 days
ALGORITHM=HS256
```

## Integration Examples

### JavaScript (Web Application)

```javascript
// Login
const loginResponse = await fetch('/api/v1/auth/login-json', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'password123'
  })
});

const { access_token, refresh_token, user } = await loginResponse.json();

// Store tokens
localStorage.setItem('access_token', access_token);
localStorage.setItem('refresh_token', refresh_token);

// Make authenticated requests
const profileResponse = await fetch('/api/v1/users/me', {
  headers: {
    'Authorization': `Bearer ${access_token}`
  }
});
```

### Python Client

```python
import requests

# Login
login_data = {
    'email': 'user@example.com',
    'password': 'password123'
}

response = requests.post('http://localhost:8010/api/v1/auth/login-json', json=login_data)
tokens = response.json()

# Use access token
headers = {'Authorization': f'Bearer {tokens["access_token"]}'}
profile = requests.get('http://localhost:8010/api/v1/users/me', headers=headers)
```

## Best Practices

1. **Store tokens securely** - Use secure storage mechanisms
2. **Handle token expiration** - Implement automatic refresh logic
3. **Validate responses** - Always check HTTP status codes
4. **Use HTTPS** - Never send tokens over unencrypted connections
5. **Implement logout** - Clear tokens from client storage
6. **Handle errors gracefully** - Provide user-friendly error messages

This JWT authentication system provides a secure, scalable solution for regular user authentication in the FastAPI application.