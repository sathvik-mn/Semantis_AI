# Authentication Setup Plan - Sign Up & Login System

## Current State Analysis

### ✅ What Exists:
1. **Database Schema**: `users` table exists with `id`, `email`, `name`, `created_at`, `updated_at`
2. **API Key System**: Working API key generation and authentication
3. **Frontend Routing**: React Router setup with protected routes
4. **Landing Page**: Basic UI for API key entry/generation

### ❌ What's Missing:
1. **Password Storage**: No `password_hash` field in users table
2. **Password Hashing**: No bcrypt/password hashing library
3. **JWT/Session Management**: No token-based authentication
4. **Sign Up Endpoint**: No `/api/auth/signup` endpoint
5. **Login Endpoint**: No `/api/auth/login` endpoint
6. **Frontend Auth Pages**: No LoginPage.tsx or SignUpPage.tsx
7. **Auth Context/State**: No user authentication state management
8. **Protected Routes**: Routes protect API keys, not user sessions

---

## Backend Implementation Requirements

### 1. Database Schema Updates

**File**: `backend/database.py`

Add password field to users table:
```python
# In init_database(), modify users table:
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,  -- NEW FIELD
        name TEXT,
        email_verified BOOLEAN DEFAULT 0,  -- NEW FIELD (for future email verification)
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login_at TIMESTAMP  -- NEW FIELD
    )
''')
```

**Migration Script**: Create `backend/migrate_add_password.py` to add password_hash column to existing users table.

### 2. Dependencies

**File**: `backend/requirements.txt`

Add:
```
bcrypt==4.1.2
python-jose[cryptography]==3.3.0
python-multipart==0.0.9
```

### 3. Authentication Endpoints

**File**: `backend/semantic_cache_server.py` (or create `backend/auth.py`)

#### POST `/api/auth/signup`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securePassword123!",
    "name": "John Doe"
  }
  ```
- **Validation**:
  - Email format validation
  - Password strength (min 8 chars, at least one letter, one number)
  - Check if email already exists
- **Response**:
  ```json
  {
    "user_id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "message": "Account created successfully"
  }
  ```
- **Actions**:
  1. Hash password with bcrypt
  2. Create user in database
  3. Optionally auto-generate API key for user
  4. Return user info (NO password)

#### POST `/api/auth/login`
- **Request Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "securePassword123!"
  }
  ```
- **Response** (Success):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
  ```
- **Response** (Error):
  ```json
  {
    "detail": "Invalid email or password"
  }
  ```
- **Actions**:
  1. Find user by email
  2. Verify password hash
  3. Generate JWT token (expires in 7 days)
  4. Update `last_login_at`
  5. Return token and user info

#### GET `/api/auth/me`
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
  ```json
  {
    "id": 1,
    "email": "user@example.com",
    "name": "John Doe",
    "created_at": "2024-01-15T10:00:00"
  }
  ```
- **Actions**:
  1. Verify JWT token
  2. Return current user info

#### POST `/api/auth/logout`
- **Headers**: `Authorization: Bearer <token>`
- **Response**:
  ```json
  {
    "message": "Logged out successfully"
  }
  ```
- **Note**: For JWT, logout is client-side (token deletion). For production, implement token blacklist.

### 4. JWT Token Configuration

**File**: `backend/auth.py` (new file)

```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
```

### 5. Database Functions

**File**: `backend/database.py`

Add functions:
```python
def create_user_with_password(email: str, password_hash: str, name: Optional[str] = None) -> int:
    """Create user with password hash."""
    
def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email."""
    
def update_last_login(user_id: int):
    """Update last login timestamp."""
```

---

## Frontend Implementation Requirements

### 1. New Pages

#### `frontend/src/pages/LoginPage.tsx`
- Email input
- Password input
- "Login" button
- Link to signup page
- Error message display
- Redirect to `/playground` on success

#### `frontend/src/pages/SignUpPage.tsx`
- Email input
- Password input (with strength indicator)
- Confirm password input
- Name input (optional)
- "Sign Up" button
- Link to login page
- Error message display
- Redirect to `/playground` on success

### 2. Authentication API Client

**File**: `frontend/src/api/authAPI.ts` (new file)

```typescript
export interface SignUpRequest {
  email: string;
  password: string;
  name?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: number;
    email: string;
    name?: string;
  };
}

export async function signUp(data: SignUpRequest): Promise<AuthResponse>
export async function login(data: LoginRequest): Promise<AuthResponse>
export async function getCurrentUser(): Promise<User>
export function setAuthToken(token: string): void
export function clearAuthToken(): void
export function getAuthToken(): string | null
export function isAuthenticated(): boolean
```

### 3. Auth Context/State Management

**File**: `frontend/src/contexts/AuthContext.tsx` (new file)

- Provide `user` state
- Provide `login`, `logout`, `signup` functions
- Persist token in localStorage
- Auto-refresh token logic (optional)

### 4. Update Landing Page

**File**: `frontend/src/pages/LandingPage.tsx`

Add buttons:
- "Sign Up" button → `/signup`
- "Login" button → `/login`
- Keep existing API key flow for backward compatibility

### 5. Update Protected Routes

**File**: `frontend/src/App.tsx`

Modify `ProtectedRoute`:
```typescript
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuth = isAuthenticated() || hasApiKey(); // Support both auth methods
  if (!isAuth) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
```

### 6. Update Layout Component

**File**: `frontend/src/components/Layout.tsx`

- Show user email/name if authenticated
- Update logout to clear both API key and auth token
- Show "Login" button if not authenticated

---

## Security Considerations

1. **Password Requirements**:
   - Minimum 8 characters
   - At least one letter and one number
   - Consider special characters

2. **JWT Secret**:
   - Use environment variable `JWT_SECRET_KEY`
   - Generate strong random secret for production
   - Never commit secret to git

3. **Token Expiration**:
   - 7 days default
   - Consider refresh tokens for production

4. **Rate Limiting**:
   - Add rate limiting to `/api/auth/login` (prevent brute force)
   - Max 5 attempts per IP per 15 minutes

5. **HTTPS**:
   - Require HTTPS in production
   - Never send passwords over HTTP

6. **Password Reset** (Future):
   - Add password reset flow
   - Email verification

---

## Database Migration

**File**: `backend/migrate_add_password.py`

```python
"""
Migration script to add password_hash column to existing users table.
Run this once before deploying authentication.
"""
import sqlite3
from database import get_db_connection

def migrate():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        try:
            # Add password_hash column (nullable for existing users)
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN password_hash TEXT
            ''')
            
            # Add email_verified column
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN email_verified BOOLEAN DEFAULT 0
            ''')
            
            # Add last_login_at column
            cursor.execute('''
                ALTER TABLE users 
                ADD COLUMN last_login_at TIMESTAMP
            ''')
            
            print("Migration completed successfully")
        except sqlite3.OperationalError as e:
            if "duplicate column" in str(e).lower():
                print("Columns already exist, skipping migration")
            else:
                raise
```

---

## Testing Checklist

- [ ] Sign up with new email
- [ ] Sign up with existing email (should fail)
- [ ] Sign up with weak password (should fail)
- [ ] Login with correct credentials
- [ ] Login with wrong password (should fail)
- [ ] Login with non-existent email (should fail)
- [ ] Access protected route without token (should redirect)
- [ ] Access protected route with valid token (should work)
- [ ] Logout clears token
- [ ] Token expiration works
- [ ] Password is hashed in database (never stored plaintext)

---

## Integration Points

1. **API Key Generation**: After signup, optionally auto-generate API key
2. **User Dashboard**: Show user's API keys in settings page
3. **Admin Panel**: Link users to their API keys
4. **Analytics**: Track signups/logins in admin dashboard

---

## Environment Variables

Add to `.env`:
```
JWT_SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
JWT_EXPIRE_DAYS=7
```

---

## File Structure Summary

### Backend Files to Create/Modify:
- ✅ `backend/database.py` - Add password_hash column and auth functions
- ✅ `backend/auth.py` - NEW: JWT and password hashing utilities
- ✅ `backend/semantic_cache_server.py` - Add `/api/auth/*` endpoints
- ✅ `backend/migrate_add_password.py` - NEW: Database migration script
- ✅ `backend/requirements.txt` - Add bcrypt, python-jose

### Frontend Files to Create/Modify:
- ✅ `frontend/src/pages/LoginPage.tsx` - NEW: Login page
- ✅ `frontend/src/pages/SignUpPage.tsx` - NEW: Signup page
- ✅ `frontend/src/api/authAPI.ts` - NEW: Auth API client
- ✅ `frontend/src/contexts/AuthContext.tsx` - NEW: Auth state management
- ✅ `frontend/src/pages/LandingPage.tsx` - Add login/signup buttons
- ✅ `frontend/src/App.tsx` - Update protected routes
- ✅ `frontend/src/components/Layout.tsx` - Show user info, update logout

---

## Implementation Order

1. **Backend Database** (migration + schema)
2. **Backend Auth Utilities** (password hashing, JWT)
3. **Backend Auth Endpoints** (signup, login, me, logout)
4. **Frontend Auth API Client**
5. **Frontend Auth Context**
6. **Frontend Login/Signup Pages**
7. **Update Landing Page**
8. **Update Protected Routes**
9. **Testing**

---

## Notes

- Keep API key authentication working for backward compatibility
- Users can have both: account (email/password) + API keys
- API keys are still the primary auth for API calls
- User accounts enable dashboard access and key management

