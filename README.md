# Immortal Wall AI

> AI-powered cybersecurity defense platform — real-time monitoring, rule-based
> detection, machine learning, honeypot-based threat intelligence, and automated
> response with full JWT bearer-token authentication and ML drift detection.

---

## Quick Start

```powershell
# 1. Train the ML model
python train.py --samples 8000

# 2. Configure environment (copy and edit)
Copy-Item .env.example .env

# 3. Start the backend
uvicorn backend.app:app --port 8000 --reload

# 4. Start the dashboard
cd dashboard
npm install
npm run dev
# → http://localhost:5173
```

On first run the backend prints your admin credentials:

```
[UserRepository] *** FIRST RUN ***
  Admin account created: analyst@immortalwall.ai
  Auto-generated password: <random>
  Set ADMIN_PASSWORD in your .env to use a fixed password.
```

Set `ADMIN_PASSWORD` in `.env` before the first run to use a fixed password.

---

## Running the project

### 1 — Train the ML model

```powershell
.\venv\Scripts\Activate.ps1
python train.py --samples 8000
```

Expected output: CV F1 macro between **0.85** and **0.97**.  
The trained pipeline is saved to `models/advanced_model.pkl`.

### 2 — Backend (FastAPI)

```powershell
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000/api/health` | Public health check |
| `http://localhost:8000/docs` | Swagger UI (includes auth) |
| `ws://localhost:8000/ws?token=<jwt>` | Live WebSocket feed |

### 3 — Frontend (React + Vite)

```powershell
cd dashboard
npm install       # first time only
npm run dev
```

Dashboard opens at `http://localhost:5173`.  
Enter your email and password on the login screen.

### 4 — Honeypot server (optional)

```powershell
python honeypot/server.py
```

Listens on port 5000. Captures probes to `/admin`, `/phpmyadmin`, `/.env`,
`/backup.zip` etc. and forwards them to the backend threat feed.

### 5 — Simulation mode (development / demo only)

```powershell
$env:IMMORTAL_WALL_SIMULATE = "true"
uvicorn backend.app:app --port 8000 --reload
```

When simulation is enabled the Collector generates synthetic traffic. Every
synthetic event is tagged `"source": "simulation"` so it can be filtered
in analytics. **Do not enable in production.**

---

## Security

### Authentication Flow

All non-public endpoints require a signed **HS256 JWT bearer token**.

**Step 1 — Login**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@immortalwall.ai","password":"<your-password>"}'
```

Response:

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": { "email": "analyst@immortalwall.ai", "role": "Admin" }
}
```

Wrong credentials return **HTTP 401** (never a 200 with `success: false`).

**Step 2 — Use the token**

```bash
TOKEN="eyJhbGci..."

curl http://localhost:8000/api/system-status \
  -H "Authorization: Bearer $TOKEN"

curl http://localhost:8000/api/ml/status \
  -H "Authorization: Bearer $TOKEN"
```

**Public endpoints** (no token required):

- `GET  /api/health`
- `POST /api/auth/login`
- `POST /api/status/event`  ← honeypot ingest

**Protected endpoints** (Bearer token required):

- `GET  /api/threats`
- `GET  /api/logs` and sub-routes (`/blocked`, `/events`, `/alerts`)
- `POST /api/analyze-threat`
- `GET  /api/analytics`
- `GET  /api/system-status`
- `GET  /api/ml/status`

**WebSocket** requires `?token=<jwt>` query parameter.  
Missing or invalid token closes with code **1008** (Policy Violation).

### Password Storage

Passwords are stored as **PBKDF2-HMAC-SHA256** hashes with 100 000 iterations
and a per-user UUID salt. The `UserRepository` is the sole hashing boundary —
no raw passwords appear anywhere else in the codebase.

### JWT Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ADMIN_EMAIL` | `analyst@immortalwall.ai` | Admin account email |
| `ADMIN_PASSWORD` | *(auto-generated)* | Admin account password |
| `JWT_SECRET_KEY` | `CHANGE-THIS-IN-PRODUCTION` | HMAC signing secret |
| `ALGORITHM` | `HS256` | Token algorithm |

Tokens expire after **8 hours**.  
The frontend stores them in a React `ref` (never in `localStorage`) and
attaches them via an axios interceptor.

### Rate Limiting

| Preset | Rate | Applied to |
|--------|------|-----------|
| `AUTH_LIMIT` | 10/min | `POST /api/auth/login` |
| `ANALYSIS_LIMIT` | 30/min | `POST /api/analyze-threat` |
| `API_LIMIT` | 120/min | All other protected endpoints |

Exceeded limits return **HTTP 429**.

---

## Architecture

```
dashboard/              React + Vite + Tailwind
  src/
    api.js              axios factory (Bearer token + 401 interceptor)
    App.jsx             splash → login → dashboard phases; JWT in ref
    components/
      LoginPage.jsx     email + password form (replaces passkey numpad)
      MLStatusPanel.jsx drift detection card

backend/
  app.py                FastAPI app; imports all singletons from container.py
  container.py          Single source of truth for all shared singletons
  schemas.py            Pydantic request models (ThreatEventSchema, RawEventSchema)
  config.py             All settings and CORS_ORIGINS
  core/
    security.py         create_access_token, get_current_user, oauth2_scheme
    rate_limiter.py     limiter instance + limit presets
  routes/
    auth_routes.py      POST /api/auth/login — email+password, returns 401 on failure
    threat_routes.py    uses container singletons
    log_routes.py       uses container singletons
    status_routes.py    uses container singletons
  services/
    ml_engine.py        18-feat extractor, calibrated ensemble, drift detection
    rule_engine.py      13 deterministic rules; imports from threat_intel/constants
    threat_engine.py    0.4*rule + 0.6*ml fusion; injected dependencies
    response_engine.py  DB-backed block/unblock; structured logging (no print())
    auth_service.py     delegates to UserRepository
  database/
    models.py           ORM models (OTPEntry retired to legacy_models.py)
    legacy_models.py    Retired OTPEntry — kept for migration reference only
    db.py               DatabaseManager with context-manager session handling
    repositories/
      threat_repo.py    DB-portable hourly bucketing (_hour_bucket_expr)
      log_repo.py
      user_repo.py      PBKDF2 hashing; auto-generates admin password on first run
      blocked_ip_repo.py
  threat_intel/
    constants.py        Single source of truth: KNOWN_BAD_IPS, GEO_BAD_PREFIXES,
                        SUSPICIOUS_UA_TOKENS, SUSPICIOUS_PATHS, SQL_INJECTION_TOKENS

agent/
  collector.py          Real-data mode by default; simulation via env var
  monitor.py
  sender.py
  config.py

honeypot/
  server.py             Flask honeypot on port 5000
  logger.py
  routes/               Fake login, /admin, /phpmyadmin, /backup.zip

tests/
  test_auth.py
  test_backend.py
  test_response_engine.py
```

### Dependency Injection

All services share **one** `DatabaseManager` and **one** `ResponseEngine`
instance created in `backend/container.py`:

```python
from backend.container import db, ml_engine, response_engine, threat_engine
```

This eliminates the previous bug where multiple `ResponseEngine` instances
maintained separate in-memory `blocked_ips` caches that could drift apart.

---

## ML Status

### Model Architecture

```
FeatureExtractor (18 hand-crafted features)
      │
StandardScaler
      │
CalibratedClassifierCV (isotonic, 5-fold)
  ├── RandomForestClassifier     (300 trees, balanced weights)
  ├── GradientBoostingClassifier (200 estimators, lr=0.05)
  └── LogisticRegression         (C=1.0, multinomial)
```

Labels: `0=normal`, `1=suspicious`, `2=malicious`

### Feature List (18 features)

| Index | Feature | Description |
|-------|---------|-------------|
| 0 | `failed_login` | Binary flag |
| 1 | `high_request_rate` | Binary flag |
| 2 | `suspicious_ip` | Binary flag |
| 3 | `request_rate` | Normalised req/s |
| 4 | `failed_logins_count` | Normalised count |
| 5 | `distinct_paths` | Port-scan signal |
| 6 | `payload_length` | Large payload signal |
| 7 | `session_duration` | Normalised seconds |
| 8 | `is_night_hour` | 01:00–05:00 UTC |
| 9 | `is_weekend` | Saturday/Sunday |
| 10 | `is_post_method` | HTTP method |
| 11 | `is_error_response` | 4xx/5xx response |
| 12 | `has_sql_chars` | SQL injection chars |
| 13 | `has_xss_chars` | XSS chars |
| 14 | `is_suspicious_path` | `/admin`, `/.env`, etc. |
| 15 | `is_suspicious_ua` | sqlmap, nmap, etc. |
| 16 | `is_known_bad_ip` | Threat intel list |
| 17 | `is_geo_anomaly` | High-risk ASN prefix |

All threat-intel constants (known-bad IPs, suspicious UA tokens, etc.) live
in `backend/threat_intel/constants.py` — the single source of truth imported
by both `rule_engine.py` and `ml_engine.py`.

### Drift Detection

`AdvancedMLEngine` maintains a rolling window of the last **1000 predictions**.

- `compute_drift_score()` — fraction of recent predictions that are non-normal.
- `drift_detected` — `True` after 100 consecutive non-normal predictions with
  fraction > 0.70.
- `recent_threat_rate` — exposed via `GET /api/ml/status`.

```bash
curl http://localhost:8000/api/ml/status \
  -H "Authorization: Bearer $TOKEN"
```

```json
{
  "model_version": "2.1.0",
  "trained_at": "2026-08-19T05:41:41Z",
  "n_features": 18,
  "f1_macro": 0.9612,
  "drift_detected": false,
  "recent_threat_rate": 0.12,
  "feature_importances": { "session_duration": 0.16, "..." : "..." }
}
```

---

## Environment Variables

Copy `.env.example` to `.env` and set real values before first run:

```bash
# Authentication
ADMIN_EMAIL=analyst@immortalwall.ai
ADMIN_PASSWORD=<choose-a-strong-password>
JWT_SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">

# Database
DATABASE_URL=sqlite:///./data/immortal_wall.db

# CORS (comma-separated)
CORS_ORIGINS=http://localhost:5173,http://localhost:5174

# Logging
LOG_LEVEL=INFO

# Agent mode — set to true for demo/development only
IMMORTAL_WALL_SIMULATE=false
```

---

## Tests

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

Test coverage:
- `test_auth.py` — email+password login, 401 on bad creds, protected endpoints,
  WebSocket 1008 rejection
- `test_backend.py` — ML feature extraction (18 features), prediction keys,
  brute-force detection, rule engine firing, threat engine fusion (0.4/0.6),
  DB repository CRUD
- `test_response_engine.py` — DB-backed block/unblock, memory cache,
  whitelist bypass, `execute_response` for all action types
