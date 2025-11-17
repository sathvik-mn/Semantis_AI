# Bolt AI Prompt: Implement Sign Up & Login Authentication

## Task
Implement complete signup/login authentication system for Semantis AI. Users should be able to create accounts with email/password and login to access the dashboard.

## Backend Requirements

1. **Database**: Add `password_hash`, `email_verified`, `last_login_at` columns to `users` table in `backend/database.py`. Create migration script.

2. **Dependencies**: Add to `backend/requirements.txt`:
   - `bcrypt==4.1.2`
   - `python-jose[cryptography]==3.3.0`

3. **Auth Module**: Create `backend/auth.py` with:
   - Password hashing (`get_password_hash`, `verify_password`)
   - JWT token creation/verification (`create_access_token`, `verify_token`)
   - Use `JWT_SECRET_KEY` env var (default: "your-secret-key-change-in-production")
   - Token expires in 7 days

4. **Endpoints** in `backend/semantic_cache_server.py`:
   - `POST /api/auth/signup` - Body: `{email, password, name?}`. Validate email format, password strength (min 8 chars, letter+number). Hash password, create user. Return `{user_id, email, name, message}`.
   - `POST /api/auth/login` - Body: `{email, password}`. Verify credentials, generate JWT. Return `{access_token, token_type: "bearer", user: {id, email, name}}`. Update `last_login_at`.
   - `GET /api/auth/me` - Headers: `Authorization: Bearer <token>`. Return current user `{id, email, name, created_at}`.
   - `POST /api/auth/logout` - Return `{message: "Logged out successfully"}`.

5. **Database Functions** in `backend/database.py`:
   - `create_user_with_password(email, password_hash, name?)` → user_id
   - `get_user_by_email(email)` → user dict or None
   - `update_last_login(user_id)`

## Frontend Requirements

1. **Auth API**: Create `frontend/src/api/authAPI.ts` with:
   - `signUp(data: {email, password, name?})` → `{access_token, user}`
   - `login(data: {email, password})` → `{access_token, user}`
   - `getCurrentUser()` → user object
   - `setAuthToken(token)`, `clearAuthToken()`, `getAuthToken()`, `isAuthenticated()`
   - Store token in localStorage as `auth_token`

2. **Pages**:
   - `frontend/src/pages/LoginPage.tsx` - Email/password form, link to signup, redirect to `/playground` on success
   - `frontend/src/pages/SignUpPage.tsx` - Email/password/confirm password/name form, password strength indicator, link to login, redirect to `/playground` on success

3. **Auth Context**: Create `frontend/src/contexts/AuthContext.tsx`:
   - Provide `user` state, `login()`, `logout()`, `signup()` functions
   - Persist token in localStorage
   - Auto-load user on mount if token exists

4. **Update Existing**:
   - `frontend/src/pages/LandingPage.tsx` - Add "Sign Up" and "Login" buttons linking to `/signup` and `/login`
   - `frontend/src/App.tsx` - Update `ProtectedRoute` to check `isAuthenticated() || hasApiKey()` (support both auth methods)
   - `frontend/src/components/Layout.tsx` - Show user email if authenticated, update logout to clear auth token

## Security
- Password validation: min 8 chars, at least one letter and one number
- Hash passwords with bcrypt (never store plaintext)
- Use JWT_SECRET_KEY env variable
- Return generic "Invalid email or password" on login failure (don't reveal if email exists)

## Testing
Test: signup → login → access protected route → logout → cannot access protected route.

## Notes
- Keep API key authentication working (backward compatibility)
- Users can have both account (email/password) + API keys
- API keys remain primary auth for API calls
- User accounts enable dashboard access and key management

