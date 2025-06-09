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
- **Status**: 🟢 DEPLOYED - Changes deployed to remote, awaiting user redeployment and verification.

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
- **Status**: 🟢 DEPLOYED - Changes deployed to remote, awaiting user redeployment and verification.

### 5. OAuth State Management
- **Issue**: OAuth state not being preserved between requests
- **Fix Attempts**:
  1. Added explicit state storage in session.
  2. Used Flask-Dance's built-in session storage with the corrected import from `flask_dance.consumer.storage.session import SessionStorage`.
  3. Connected the OAuth handler to the blueprint instance.
  4. Removed `session.get_cookie_value()` call, which was causing `AttributeError`.
- **Status**: 🟢 DEPLOYED - Changes deployed to remote, awaiting user redeployment and verification.

### 6. Subscription Page Not Visible
- **Issue**: The Subscription page and its navigation link were not visible in the frontend.
- **Fix Attempts**:
  1. Added a new route for the `Subscription` component in `frontend/src/App.jsx`.
  2. Added a navigation link for the `Subscription` page in `frontend/src/Layout.jsx`.
- **Status**: 🟢 DEPLOYED - Changes deployed, awaiting user verification after redeployment.

### 7. Portfolio Data Not Persisting / Initial Balance Missing
- **Issue**: Portfolio data (cash balance, holdings, transactions) was not persisting across deployments, and the initial 10 lakh balance was not being granted to new users.
- **Diagnosis**: The backend was using a mix of in-memory dictionaries (`portfolios`, `transactions` in `portfolio.py`) and SQLAlchemy models for portfolio management, leading to data loss on application restarts.
- **Fix Attempts**:
  1. Refactored `portfolio.py` to use SQLAlchemy `Portfolio`, `Holding`, and `Transaction` models exclusively for all data persistence.
  2. Ensured the initial 10 lakh (`FREE_TIER_LIMIT`) cash balance is set when a new portfolio is created in the database.
  3. Removed redundant and conflicting portfolio-related helper functions and API routes from `main.py` (e.g., `check_subscription`, `check_trading_limit`, `trading_limit_required`, `/api/portfolio/buy`, `/api/portfolio/sell`, `/api/portfolio`, `/api/transactions`) to centralize all portfolio logic in `portfolio.py`.
- **Status**: ✅ RESOLVED - Portfolio cash balance and holdings now persist and load correctly. Initial 10 lakh balance is applied for new portfolios.

### 8. Database Persistence Configuration
- **Issue**: User data and portfolio were not persisting due to the database defaulting to an in-memory SQLite instance.
- **Diagnosis**: `SQLALCHEMY_DATABASE_URI` was not explicitly set in `config.py`, causing data loss on application restarts or across different Gunicorn worker processes.
- **Fix Attempts**:
  1. Configured `SQLALCHEMY_DATABASE_URI` in `config.py` to load from the `DATABASE_URL` environment variable for production (as provided by Render).
  2. Set `SQLALCHEMY_DATABASE_URI` to a local file (`sqlite:///site.db`) for development.
  3. Set `SQLALCHEMY_TRACK_MODIFICATIONS` to `False` as a best practice.
- **Status**: ✅ RESOLVED - Database is now configured for persistence, allowing user and portfolio data to be stored correctly.

### 9. Frontend Build Failure - Unreachable Code Error
- **Issue**: The frontend build failed with an ESLint `unreachable code` error in `src/Subscription.jsx`.
- **Diagnosis**: A `return;` statement was added to `handlePurchase` function to temporarily disable purchase, causing subsequent code to be flagged as unreachable by ESLint.
- **Fix Attempts**:
  1. Removed the explicit `return;` statement from `handlePurchase` in `frontend/src/Subscription.jsx`.
  2. Commented out the `fetch` call for purchasing within `handlePurchase` to effectively disable it without causing unreachable code errors.
- **Status**: ✅ RESOLVED - Frontend builds successfully, and subscription purchase is gracefully disabled.

### 10. `AttributeError: 'Transaction' object has no attribute 'timestamp'`
- **Issue**: The application crashed with an `AttributeError` when trying to access `Transaction.timestamp`.
- **Diagnosis**: The `Transaction` model in `backend/models.py` uses `created_at` for the timestamp field, but `portfolio.py` was attempting to order and filter transactions using `timestamp`.
- **Fix Attempts**:
  1. Modified `portfolio.py` to correctly use `Transaction.created_at` instead of `Transaction.timestamp` when querying and filtering transactions.
- **Status**: ✅ RESOLVED - Transaction history now loads correctly without errors.

### 11. Historical Stock Data Caching
- **Issue**: Stock data was only available in real-time from Alpha Vantage; historical data was not persisted for display when markets are closed.
- **Diagnosis**: The application directly queried Alpha Vantage, without a local cache for historical prices.
- **Fix Attempts**:
  1. Added a new `HistoricalPrice` SQLAlchemy model to `backend/models.py` to store daily stock data (symbol, date, open, high, low, close, volume).
  2. Modified the `/api/market/quote/<symbol>` endpoint in `main.py` to:
     - First check the `HistoricalPrice` table for cached data.
     - If data is not found or is outdated, fetch from Alpha Vantage.
     - Store the fetched daily data (especially the close price) into the `HistoricalPrice` table.
     - Serve the cached data (last known closing price) when the market is closed.
  3. **Implemented fallback to `TIME_SERIES_DAILY_ADJUSTED`**: When the market is closed or `GLOBAL_QUOTE` fails, the system now fetches historical daily data to ensure a displayable last recorded price.
- **Status**: 🟢 DEPLOYED - Changes deployed to remote, awaiting user redeployment and verification.

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

### Current Status Summary:
- OAuth flow successfully obtains token from Google
- Session configuration is properly set
- Cookie settings are correct for cross-site requests
- Debug logging is in place to track session state
- Explicit state handling added to session
- Using Flask-Dance's session storage with correct import 