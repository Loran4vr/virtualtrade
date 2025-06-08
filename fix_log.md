# VTA Project Fix Log

This document summarizes key issues encountered and their resolutions during the development and deployment of the VTA Flask/React application.

---

## 1. Frontend Routing and Component Loading Issue

**Problem:**
The React frontend (frontend/src/App.jsx) was initially rendering a placeholder "Home Page" instead of the actual application due to incorrect routing and component imports.

**Resolution:**
Corrected import paths for `ThemeProvider` and page components (Login, Dashboard, etc.) in `frontend/src/App.jsx` to reflect their correct locations (e.g., `./theme-provider` instead of `./components/ui/theme-provider`, and `./Login` instead of `./pages/Login`). Restored proper routing using `react-router-dom` to display the application's components.

---

## 2. Google OAuth `redirect_uri_mismatch` Error

**Problem:**
After clicking "sign in" via Google, the application returned `Error 400: redirect_uri_mismatch`. Logs showed `Could not build url for endpoint 'google.login'. Did you mean 'auth.google.login' instead?` and a redundant `/google` in the redirect URI (`https://virtualtrade.onrender.com/auth/google/google/authorized`).

**Resolution:**
1.  **Corrected `url_for` call:** Changed `url_for('google.login')` to `url_for('auth.google.login')` in `auth.py`.
2.  **Removed redundant `url_prefix`:** Removed `url_prefix="/google"` from the `auth_bp.register_blueprint(google_bp, ...)` call in `auth.py` to prevent the duplicate `/google` in the redirect URI.
3.  **Corrected `redirect_to` endpoint:** Changed `redirect_to="/" ` to `redirect_to="index"` in `make_google_blueprint` within `auth.py`, as `url_for` requires an endpoint name, not a path.

---

## 3. Flask Session Persistence Issues (`401 Unauthorized`, `No user_id in session`, `state not found`)

**Problem:**
Users were frequently experiencing `401 Unauthorized` on `/auth/user` and `No user_id in session` despite successful Google OAuth token acquisition. Additionally, `INFO:flask_dance.consumer.oauth2:state not found` indicated session loss during the OAuth flow. This was ultimately traced to session cookie issues.

**Resolution:**
1.  **Ensured Session Permanence:** Confirmed `session.permanent = True` was set in `main.py` within the `google_logged_in` callback.
2.  **Explicit Redirect Post-Login:** Modified `google_logged_in` in `main.py` to explicitly `return redirect('/')` to ensure the session cookie is properly set in the response after login.
3.  **Corrected `SameSite` Policy:** Changed `SESSION_COOKIE_SAMESITE` from `'Lax'` to `'None'` in `config.py` (specifically within `ProductionConfig`) to allow cross-site cookie sending, which is necessary for OAuth redirects.
4.  **Enabled Secure Cookies for HTTPS:** Ensured `SESSION_COOKIE_SECURE = True` was set in `ProductionConfig` in `config.py`. Initial logs showed `Secure=False`, indicating `DevelopmentConfig` was being loaded.
5.  **Environment Variable Mismatch (FLASK_ENV):** This was the most persistent underlying issue. The Flask application on Render was defaulting to `development` configuration even when `FLASK_ENV=production` was set in the Render dashboard and Dockerfile's `ENV` instruction. This was due to how Gunicorn was implicitly invoking the Flask app factory.
    *   **Initial `create_app` factory issue:** The `create_app(config_name='default')` signature meant Gunicorn's default invocation (`main:app`) would always use `default` unless explicitly passed.
    *   **Solution:** Modified `main.py` to:
        *   Remove `config_name` argument from `create_app()`.
        *   Move `config_name = os.getenv('FLASK_ENV', 'development')` inside `create_app()` itself.
        *   Assign the result of `create_app()` to a module-level variable: `application = create_app()`.
    *   **Gunicorn `TypeError` Fix:** After the above, Gunicorn produced `TypeError: create_app() takes 0 positional arguments but 2 were given` because it was trying to pass WSGI `environ` and `start_response` to `create_app()`.
    *   **Solution:** Updated `Dockerfile`'s `CMD` instruction to point Gunicorn directly to the Flask application instance: `CMD ["gunicorn", ..., "main:application"]`. This ensures `create_app()` is called once at startup, and Gunicorn serves the returned app instance.

---

## 4. Dockerfile `CMD` Syntax Error

**Problem:**
After explicitly setting `FLASK_ENV` within the `CMD` as `FLASK_ENV=production exec gunicorn ... main:create_app()`, a `/bin/sh: 1: Syntax error: "(" unexpected` error occurred.

**Resolution:**
Removed the parentheses `()` from `main:create_app()` in the `Dockerfile`'s `CMD` instruction. Gunicorn expects `main:create_app` (module:callable) to import the callable and execute it, not literal shell execution of `create_app()`. 

---

## OAuth and Session Issues

### 1. Redirect URI Mismatch
- **Issue**: `redirect_uri_mismatch` error with URL `https://virtualtrade.onrender.com/auth/google/google/authorized`
- **Fix Attempts**:
  1. Changed `url_prefix` in `main.py` from `/auth/google` to `/auth`
  2. Added explicit `redirect_url` in `make_google_blueprint`
- **Status**: ✅ RESOLVED - Redirect URI now correctly set to `https://virtualtrade.onrender.com/auth/google/authorized`

### 2. Session Persistence
- **Issue**: Session not persisting after OAuth login, causing "state not found" error
- **Fix Attempts**:
  1. Added explicit session configuration in `create_app()`:
     ```python
     app.config['SESSION_COOKIE_SECURE'] = True
     app.config['SESSION_COOKIE_HTTPONLY'] = True
     app.config['SESSION_COOKIE_SAMESITE'] = 'None'
     app.config['SESSION_COOKIE_DOMAIN'] = None
     app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
     ```
  2. Modified `google_logged_in` handler:
     - Clear existing session data
     - Mark session as modified
     - Create response with explicit cookie settings
     - Set session cookie with proper security settings
  3. Added explicit state handling:
     - Using Flask-Dance's `SessionStorage` explicitly
     - Storing OAuth state in session
     - Connecting OAuth handler to blueprint instead of app
- **Status**: 🔄 TESTING - Latest changes deployed, awaiting verification

### 5. OAuth State Management
- **Issue**: OAuth state not being preserved between requests
- **Fix Attempts**:
  1. Added explicit state storage in session
  2. Using Flask-Dance's built-in session storage
     - Corrected import from `flask_dance.consumer.storage.session import SessionStorage`
     - Using `SessionStorage()` for OAuth state management
  3. Connecting OAuth handler to blueprint instance
- **Status**: 🔄 TESTING - Latest changes deployed, awaiting verification

## Current Status
- OAuth flow successfully obtains token from Google
- Session configuration is properly set
- Cookie settings are correct for cross-site requests
- Debug logging is in place to track session state
- Explicit state handling added to session
- Using Flask-Dance's session storage with correct import

## Next Steps
1. Monitor session persistence after OAuth login
2. Verify user authentication state is maintained
3. Test cross-site cookie handling
4. Monitor for any new session-related issues
5. Verify OAuth state is properly maintained

## Debug Logging Points
1. Session creation in `google_logged_in`
2. Cookie settings in `create_app`
3. Environment variables at startup
4. OAuth state management
5. User authentication status
6. OAuth state storage and retrieval

## Important Notes
- All cookie settings must be consistent across the application
- Session must be marked as modified when changed
- Cross-site requests require `SameSite=None`
- Secure cookies require HTTPS
- Session lifetime is set to 7 days
- OAuth state must be preserved in session
- Flask-Dance session storage is explicitly configured with correct import 