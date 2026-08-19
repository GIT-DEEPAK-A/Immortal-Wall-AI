# Immortal Wall AI

> **AI-powered cybersecurity defense and threat intelligence platform for real-time detection, monitoring, analysis, and automated response.**

Immortal Wall AI is a modular cybersecurity defense platform that combines **deterministic security rules, machine-learning threat classification, honeypot telemetry, real-time event monitoring, threat intelligence, JWT authentication, rate limiting, and automated response** into a single system.

The platform is designed to provide a complete security-monitoring workflow:

```text
Incoming Traffic
      │
      ▼
┌──────────────────┐
│ Data Collector   │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────┐
│ Threat Detection Pipeline    │
│                              │
│  ┌────────────┐ ┌─────────┐ │
│  │ Rule Engine│ │ ML Engine│ │
│  └──────┬─────┘ └────┬────┘ │
│         │             │      │
│         └──────┬──────┘      │
│                ▼             │
│        Threat Engine         │
└────────────────┬─────────────┘
                 │
                 ▼
       ┌──────────────────┐
       │ Threat Decision  │
       └────────┬─────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
   Store / Alert    Automated Response
        │                │
        └───────┬────────┘
                ▼
       ┌─────────────────┐
       │ React Dashboard │
       └─────────────────┘
```

---

## Table of Contents

* [Overview](#overview)
* [Key Capabilities](#key-capabilities)
* [Architecture](#architecture)
* [Technology Stack](#technology-stack)
* [Project Structure](#project-structure)
* [Prerequisites](#prerequisites)
* [Quick Start](#quick-start)
* [Configuration](#configuration)
* [Authentication](#authentication)
* [API](#api)
* [WebSocket](#websocket)
* [Threat Detection Pipeline](#threat-detection-pipeline)
* [Rule Engine](#rule-engine)
* [Machine Learning Engine](#machine-learning-engine)
* [ML Drift Detection](#ml-drift-detection)
* [Threat Intelligence](#threat-intelligence)
* [Automated Response](#automated-response)
* [Honeypot](#honeypot)
* [Agent and Data Collection](#agent-and-data-collection)
* [Simulation Mode](#simulation-mode)
* [Database](#database)
* [Security Architecture](#security-architecture)
* [Rate Limiting](#rate-limiting)
* [Testing](#testing)
* [Development Workflow](#development-workflow)
* [Production Considerations](#production-considerations)
* [Observability](#observability)
* [Troubleshooting](#troubleshooting)
* [Known Limitations](#known-limitations)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)

---

# Overview

Immortal Wall AI is built around a **defense-in-depth detection model** rather than relying exclusively on machine learning.

A threat can be detected through:

1. Known malicious indicators.
2. Deterministic behavioral rules.
3. HTTP/request-level anomalies.
4. Machine-learning classification.
5. Honeypot activity.
6. Threat-intelligence signals.
7. Aggregated threat scoring.

The resulting architecture allows deterministic security controls to remain explainable while ML provides an additional behavioral signal.

The current threat decision model combines rule-based and ML signals:

```text
Threat Score
    │
    ├── 40% Rule Engine
    │
    └── 60% ML Engine
```

This hybrid architecture is intentional.

Machine learning should **augment security controls**, not become the sole authority responsible for blocking production traffic.

---

# Key Capabilities

## Detection

* Real-time event collection.
* Deterministic rule-based detection.
* Machine-learning classification.
* Suspicious IP detection.
* Request-rate anomaly detection.
* Failed-login analysis.
* SQL injection indicators.
* XSS indicators.
* Suspicious path detection.
* Suspicious user-agent detection.
* Error-response analysis.
* Port-scan style behavioral signals.
* Geographic/ASN anomaly indicators.

## Threat Intelligence

* Known malicious IP indicators.
* Suspicious geographic prefixes.
* Suspicious HTTP user-agent tokens.
* Suspicious paths.
* SQL injection indicators.
* Shared threat-intelligence constants across detection components.

## Machine Learning

* 18 engineered security features.
* Multi-model ensemble.
* Feature scaling.
* Probability calibration.
* Cross-validation.
* Multiclass classification.
* Model metadata.
* Feature importance reporting.
* Rolling prediction monitoring.
* Basic prediction-distribution drift detection.

## Automated Response

* Database-backed IP blocking.
* IP unblock operations.
* Whitelist handling.
* Response action execution.
* Structured response logging.

## Security

* JWT bearer authentication.
* HS256 token signing.
* Password hashing with PBKDF2-HMAC-SHA256.
* Per-user salts.
* Protected API routes.
* Authenticated WebSocket connections.
* Authentication rate limiting.
* API rate limiting.
* Analysis endpoint rate limiting.
* CORS configuration.

## Operations

* FastAPI backend.
* React/Vite security dashboard.
* WebSocket live feed.
* Optional honeypot.
* Optional traffic simulation.
* SQLite-compatible persistence.
* Automated test suite.

---

# Architecture

## High-Level Architecture

```text
                           ┌─────────────────────┐
                           │   React Dashboard   │
                           │   React + Vite      │
                           └──────────┬──────────┘
                                      │
                         REST API + WebSocket
                                      │
                                      ▼
                         ┌─────────────────────┐
                         │     FastAPI API     │
                         │                     │
                         │ Authentication      │
                         │ Rate Limiting       │
                         │ API Routes          │
                         │ WebSocket           │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Threat Engine      │
                         │                     │
                         │ Rule Score  ──┐     │
                         │               ├─►   │
                         │ ML Score    ──┘     │
                         └───────┬─────────────┘
                                 │
                 ┌───────────────┼────────────────┐
                 ▼               ▼                ▼
        ┌────────────────┐ ┌────────────┐ ┌──────────────┐
        │ Rule Engine    │ │ ML Engine  │ │ Threat Intel │
        └────────────────┘ └────────────┘ └──────────────┘
                 │               │                │
                 └───────────────┼────────────────┘
                                 ▼
                         ┌─────────────────┐
                         │ Response Engine │
                         └────────┬────────┘
                                  │
                         ┌────────▼────────┐
                         │    Database     │
                         └─────────────────┘


     ┌──────────────┐
     │ Data Agent   │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │ Backend API  │
     └──────────────┘


     ┌──────────────┐
     │  Honeypot    │
     └──────┬───────┘
            │
            ▼
     ┌──────────────┐
     │ Threat Feed  │
     └──────────────┘
```

---

# Technology Stack

| Layer               | Technology                          |
| ------------------- | ----------------------------------- |
| Backend API         | Python, FastAPI                     |
| API Server          | Uvicorn                             |
| Validation          | Pydantic                            |
| Database            | SQLite / SQL-compatible persistence |
| ORM / Persistence   | Repository abstraction              |
| Authentication      | JWT / OAuth2 bearer scheme          |
| Password Hashing    | PBKDF2-HMAC-SHA256                  |
| ML                  | scikit-learn                        |
| Frontend            | React                               |
| Frontend Build      | Vite                                |
| Styling             | Tailwind CSS                        |
| HTTP Client         | Axios                               |
| Real-Time Transport | WebSocket                           |
| Honeypot            | Flask                               |
| Testing             | pytest                              |
| Configuration       | Environment variables / `.env`      |

---

# Project Structure

```text
immortal-wall-ai/
│
├── backend/
│   ├── app.py
│   ├── container.py
│   ├── config.py
│   ├── schemas.py
│   │
│   ├── core/
│   │   ├── security.py
│   │   └── rate_limiter.py
│   │
│   ├── routes/
│   │   ├── auth_routes.py
│   │   ├── threat_routes.py
│   │   ├── log_routes.py
│   │   └── status_routes.py
│   │
│   ├── services/
│   │   ├── ml_engine.py
│   │   ├── rule_engine.py
│   │   ├── threat_engine.py
│   │   ├── response_engine.py
│   │   └── auth_service.py
│   │
│   ├── database/
│   │   ├── models.py
│   │   ├── legacy_models.py
│   │   ├── db.py
│   │   └── repositories/
│   │       ├── threat_repo.py
│   │       ├── log_repo.py
│   │       ├── user_repo.py
│   │       └── blocked_ip_repo.py
│   │
│   └── threat_intel/
│       └── constants.py
│
├── agent/
│   ├── collector.py
│   ├── monitor.py
│   ├── sender.py
│   └── config.py
│
├── honeypot/
│   ├── server.py
│   ├── logger.py
│   └── routes/
│
├── dashboard/
│   ├── src/
│   │   ├── api.js
│   │   ├── App.jsx
│   │   └── components/
│   │       ├── LoginPage.jsx
│   │       └── MLStatusPanel.jsx
│   └── package.json
│
├── models/
│   └── advanced_model.pkl
│
├── tests/
│   ├── test_auth.py
│   ├── test_backend.py
│   └── test_response_engine.py
│
├── train.py
├── .env.example
├── .gitignore
└── README.md
```

---

# Prerequisites

Before running Immortal Wall AI locally, install:

* Python 3.10+
* Node.js 18+
* npm
* Git

Recommended development environment:

```text
Python 3.11+
Node.js 20+
npm 10+
```

A Python virtual environment is strongly recommended.

---

# Quick Start

## 1. Clone the Repository

```bash
git clone <repository-url>
cd immortal-wall-ai
```

---

## 2. Create a Python Virtual Environment

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Python Dependencies

If the repository contains a requirements file:

```bash
pip install -r requirements.txt
```

---

## 4. Train the ML Model

```powershell
python train.py --samples 8000
```

The trained model is written to:

```text
models/advanced_model.pkl
```

A typical training run is expected to produce a macro F1 score in the approximate range:

```text
0.85 - 0.97
```

> **Important:** A high score on synthetic/training data does not establish real-world detection performance. Production evaluation requires representative, independently collected validation data.

---

## 5. Configure the Environment

Copy the example configuration:

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and configure production-appropriate secrets.

---

## 6. Start the Backend

```powershell
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

---

## 7. Start the Dashboard

```powershell
cd dashboard
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

# First-Run Administration

On the first backend startup, the application creates an administrator account if one does not already exist.

Example:

```text
[UserRepository] *** FIRST RUN ***
  Admin account created: analyst@immortalwall.ai
  Auto-generated password: <random>
  Set ADMIN_PASSWORD in your .env to use a fixed password.
```

For deterministic local development credentials, configure:

```env
ADMIN_EMAIL=analyst@immortalwall.ai
ADMIN_PASSWORD=<strong-password>
```

Do this **before the first application startup**.

Never commit real credentials to source control.

---

# Configuration

The recommended configuration is environment-based.

Example:

```env
# --------------------------------------------------
# Authentication
# --------------------------------------------------

ADMIN_EMAIL=analyst@immortalwall.ai
ADMIN_PASSWORD=<strong-password>

JWT_SECRET_KEY=<cryptographically-random-secret>
ALGORITHM=HS256


# --------------------------------------------------
# Database
# --------------------------------------------------

DATABASE_URL=sqlite:///./data/immortal_wall.db


# --------------------------------------------------
# CORS
# --------------------------------------------------

CORS_ORIGINS=http://localhost:5173,http://localhost:5174


# --------------------------------------------------
# Logging
# --------------------------------------------------

LOG_LEVEL=INFO


# --------------------------------------------------
# Agent
# --------------------------------------------------

IMMORTAL_WALL_SIMULATE=false
```

Generate a strong JWT secret with:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

For production, secrets should preferably be injected by a dedicated secret-management system rather than stored in a `.env` file on the server.

---

# Authentication

Immortal Wall AI uses JWT bearer authentication for protected API resources.

## Authentication Flow

```text
Client
  │
  │ POST /api/auth/login
  │ email + password
  ▼
┌──────────────────┐
│ Authentication   │
│ Service          │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ User Repository  │
│ PBKDF2 Verify    │
└────────┬─────────┘
         │
         ▼
   Credentials OK?
      │       │
     No      Yes
      │       │
      ▼       ▼
   HTTP 401  JWT
              │
              ▼
        Bearer Token
```

---

## Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@immortalwall.ai","password":"<your-password>"}'
```

Example response:

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "user": {
    "email": "analyst@immortalwall.ai",
    "role": "Admin"
  }
}
```

Invalid credentials return:

```text
HTTP 401 Unauthorized
```

The API does not return an HTTP 200 response containing an application-level authentication failure.

---

# Password Security

Passwords are not stored in plaintext.

The current implementation uses:

```text
PBKDF2-HMAC-SHA256
100,000 iterations
Per-user UUID salt
```

`UserRepository` is the designated password-hashing boundary.

This means authentication-related code should not duplicate password hashing logic elsewhere in the application.

### Security recommendation

Before a production deployment, review the password hashing configuration against the current security requirements of the target environment. The iteration count should be treated as a configurable security parameter rather than a permanent constant.

---

# JWT Configuration

| Variable         | Default                   | Description                    |
| ---------------- | ------------------------- | ------------------------------ |
| `ADMIN_EMAIL`    | `analyst@immortalwall.ai` | Initial administrator email    |
| `ADMIN_PASSWORD` | Auto-generated            | Initial administrator password |
| `JWT_SECRET_KEY` | Development placeholder   | JWT signing secret             |
| `ALGORITHM`      | `HS256`                   | JWT signing algorithm          |

Tokens currently expire after:

```text
8 hours
```

The frontend keeps the active token in a React `ref` rather than `localStorage`.

Axios attaches the token to protected requests through an interceptor.

> Storing access tokens outside persistent browser storage reduces exposure to some forms of token theft, but it does not eliminate XSS risk. A production deployment should additionally enforce a strong Content Security Policy and carefully review the frontend dependency and rendering model.

---

# Public API Endpoints

The following endpoints do not require a bearer token:

| Method | Endpoint            | Purpose                  |
| ------ | ------------------- | ------------------------ |
| `GET`  | `/api/health`       | Health check             |
| `POST` | `/api/auth/login`   | Authenticate user        |
| `POST` | `/api/status/event` | Honeypot/event ingestion |

---

# Protected API Endpoints

Bearer authentication is required for:

| Method | Endpoint              | Purpose                   |
| ------ | --------------------- | ------------------------- |
| `GET`  | `/api/threats`        | Threat records            |
| `GET`  | `/api/logs`           | Security logs             |
| `GET`  | `/api/logs/blocked`   | Blocked events            |
| `GET`  | `/api/logs/events`    | Event stream              |
| `GET`  | `/api/logs/alerts`    | Alert records             |
| `POST` | `/api/analyze-threat` | Analyze a threat          |
| `GET`  | `/api/analytics`      | Security analytics        |
| `GET`  | `/api/system-status`  | System status             |
| `GET`  | `/api/ml/status`      | ML model and drift status |

---

# Authenticated Requests

```bash
TOKEN="eyJhbGci..."

curl http://localhost:8000/api/system-status \
  -H "Authorization: Bearer $TOKEN"
```

Example:

```bash
curl http://localhost:8000/api/ml/status \
  -H "Authorization: Bearer $TOKEN"
```

---

# WebSocket

The live threat feed is exposed through a WebSocket connection.

```text
ws://localhost:8000/ws?token=<jwt>
```

The WebSocket validates the JWT before allowing access to the stream.

Invalid or missing authentication results in:

```text
1008 Policy Violation
```

This prevents unauthenticated clients from subscribing to live security telemetry.

---

# Threat Detection Pipeline

The detection pipeline is deliberately hybrid.

```text
Raw Security Event
       │
       ▼
Feature Extraction
       │
       ├──────────────────────┐
       ▼                      ▼
 Rule Evaluation       ML Classification
       │                      │
       │                      │
       └──────────┬───────────┘
                  ▼
           Threat Engine
                  │
                  ▼
         Combined Threat Score
                  │
          ┌───────┴────────┐
          ▼                ▼
       Storage          Response
```

The current fusion strategy is:

```text
Final Score = 0.4 × Rule Score + 0.6 × ML Score
```

This allows explicit indicators such as known malicious IPs or suspicious paths to influence the final decision while still giving the ML classifier a larger contribution.

---

# Rule Engine

The rule engine contains deterministic security rules.

Current detection categories include:

* Brute-force behavior.
* Excessive request rate.
* Known malicious IPs.
* Suspicious geographic/ASN prefixes.
* Suspicious user agents.
* Suspicious URL paths.
* SQL injection indicators.
* XSS indicators.
* HTTP error anomalies.
* Request payload anomalies.
* Authentication failures.

Rules are intentionally deterministic and explainable.

For example:

```text
Known malicious IP
       │
       ▼
High-confidence indicator
       │
       ▼
Threat score contribution
```

The rule engine obtains threat-intelligence constants from:

```text
backend/threat_intel/constants.py
```

This file is the single source of truth for shared indicators.

---

# Machine Learning Engine

The ML pipeline currently uses 18 engineered features.

```text
Raw Event
   │
   ▼
FeatureExtractor
   │
   ▼
18-dimensional feature vector
   │
   ▼
StandardScaler
   │
   ▼
Ensemble
   │
   ├── Random Forest
   ├── Gradient Boosting
   └── Logistic Regression
   │
   ▼
Probability Calibration
   │
   ▼
Threat Class
```

## Classification Labels

```text
0 = normal
1 = suspicious
2 = malicious
```

---

# ML Model Architecture

```text
FeatureExtractor
       │
       ▼
StandardScaler
       │
       ▼
CalibratedClassifierCV
       │
       ├── RandomForestClassifier
       │      └── 300 trees
       │
       ├── GradientBoostingClassifier
       │      ├── 200 estimators
       │      └── learning rate = 0.05
       │
       └── LogisticRegression
              └── C = 1.0
```

The ensemble uses balanced class weighting where supported and probability calibration using isotonic calibration with 5-fold cross-validation.

---

# ML Features

The feature extractor currently produces 18 features.

|  # | Feature               | Security Signal                  |
| -: | --------------------- | -------------------------------- |
|  0 | `failed_login`        | Authentication failure           |
|  1 | `high_request_rate`   | Request-rate anomaly             |
|  2 | `suspicious_ip`       | Suspicious source                |
|  3 | `request_rate`        | Requests per second              |
|  4 | `failed_logins_count` | Repeated authentication failures |
|  5 | `distinct_paths`      | Scanning / enumeration behavior  |
|  6 | `payload_length`      | Large payload anomaly            |
|  7 | `session_duration`    | Session behavior                 |
|  8 | `is_night_hour`       | Time-based anomaly               |
|  9 | `is_weekend`          | Temporal signal                  |
| 10 | `is_post_method`      | HTTP method                      |
| 11 | `is_error_response`   | HTTP 4xx/5xx signal              |
| 12 | `has_sql_chars`       | SQL injection indicator          |
| 13 | `has_xss_chars`       | XSS indicator                    |
| 14 | `is_suspicious_path`  | Sensitive endpoint probing       |
| 15 | `is_suspicious_ua`    | Scanner/tool fingerprint         |
| 16 | `is_known_bad_ip`     | Threat intelligence              |
| 17 | `is_geo_anomaly`      | Geographic/ASN anomaly           |

The feature order is part of the model contract.

Any change to feature ordering, preprocessing, or semantics should result in a new model version.

---

# Model Training

Train a new model with:

```bash
python train.py --samples 8000
```

The model is stored at:

```text
models/advanced_model.pkl
```

Training should be treated as a reproducible pipeline rather than a one-off manual operation.

For serious production usage, model artifacts should additionally have:

* Explicit version identifiers.
* Training dataset identifiers.
* Training timestamps.
* Evaluation dataset identifiers.
* Dependency versions.
* Feature-schema versions.
* Reproducible random seeds.
* Artifact integrity verification.

---

# ML Status

The backend exposes:

```http
GET /api/ml/status
```

Example:

```json
{
  "model_version": "2.1.0",
  "trained_at": "2026-08-19T05:41:41Z",
  "n_features": 18,
  "f1_macro": 0.9612,
  "drift_detected": false,
  "recent_threat_rate": 0.12,
  "feature_importances": {
    "session_duration": 0.16
  }
}
```

---

# ML Drift Detection

`AdvancedMLEngine` maintains a rolling prediction window containing the most recent:

```text
1000 predictions
```

The current implementation derives a prediction-distribution signal from the proportion of recent predictions that are non-normal.

Key metrics:

```text
compute_drift_score()
drift_detected
recent_threat_rate
```

The current detection condition includes:

```text
100 consecutive non-normal predictions
AND
non-normal prediction fraction > 0.70
```

### Important distinction

This is **prediction-distribution monitoring**, not a complete statistical feature-drift monitoring system.

A mature production implementation should additionally monitor:

* Feature distribution drift.
* Missing-value rates.
* Feature cardinality changes.
* Input schema changes.
* Prediction confidence.
* Class distribution.
* False-positive rate.
* False-negative rate.
* Population Stability Index (PSI).
* Jensen-Shannon divergence or equivalent metrics.
* Ground-truth performance over time.

This distinction is important because a model can experience feature drift even when its prediction distribution appears stable.

---

# Threat Intelligence

Threat-intelligence indicators are centralized in:

```text
backend/threat_intel/constants.py
```

Current categories include:

```text
KNOWN_BAD_IPS
GEO_BAD_PREFIXES
SUSPICIOUS_UA_TOKENS
SUSPICIOUS_PATHS
SQL_INJECTION_TOKENS
```

Both the rule engine and ML feature extractor consume these shared constants.

This avoids inconsistent security behavior caused by maintaining duplicate indicator lists in multiple modules.

---

# Automated Response

The `ResponseEngine` manages response actions.

Current capabilities include:

* Block IP.
* Unblock IP.
* Whitelist bypass.
* Persist blocked state.
* Structured response logging.

Architecture:

```text
Threat Decision
      │
      ▼
ResponseEngine
      │
      ├── Whitelist Check
      │
      ├── Block / Unblock
      │
      ├── Database Persistence
      │
      └── Structured Audit Logging
```

The `ResponseEngine` is instantiated centrally through:

```text
backend/container.py
```

This is important because multiple independent response-engine instances can otherwise maintain inconsistent in-memory state.

---

# Dependency Injection and Application Container

Shared application services are created in:

```text
backend/container.py
```

Consumers can access the canonical instances through:

```python
from backend.container import (
    db,
    ml_engine,
    response_engine,
    threat_engine,
)
```

The container establishes a single application-level instance for shared components.

This prevents bugs caused by accidentally creating multiple instances of stateful services.

For example:

```text
                    container.py
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
             DB         ML      Response
              │                     │
              └──────────┬──────────┘
                         ▼
                   Threat Engine
```

---

# Honeypot

Immortal Wall AI includes an optional Flask-based honeypot.

Start it with:

```bash
python honeypot/server.py
```

Default port:

```text
5000
```

The honeypot exposes intentionally monitored endpoints such as:

```text
/admin
/phpmyadmin
/.env
/backup.zip
```

Requests are captured and forwarded to the backend threat feed.

The honeypot is useful for collecting:

* Automated scanner activity.
* Credential probing.
* Sensitive-file enumeration.
* Common web exploitation attempts.
* Internet background noise.

> Do not expose a honeypot directly to an untrusted network without appropriate network isolation, resource limits, monitoring, and containment controls.

---

# Agent and Data Collection

The `agent/` package provides data collection components.

```text
agent/
├── collector.py
├── monitor.py
├── sender.py
└── config.py
```

Responsibilities are separated into:

```text
Collector
   │
   ▼
Monitor / Normalize
   │
   ▼
Sender
   │
   ▼
Backend API
```

The collector operates in real-data mode by default.

---

# Simulation Mode

For demonstrations and development, synthetic events can be enabled.

PowerShell:

```powershell
$env:IMMORTAL_WALL_SIMULATE = "true"

uvicorn backend.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

Synthetic events are explicitly tagged:

```json
{
  "source": "simulation"
}
```

This makes it possible to distinguish generated telemetry from real events.

## Production Warning

Do **not** enable simulation mode in production.

Synthetic events can contaminate:

* Threat analytics.
* Detection statistics.
* ML monitoring.
* Alert counts.
* Incident timelines.
* Operational dashboards.

---

# Database

The default development database is SQLite:

```env
DATABASE_URL=sqlite:///./data/immortal_wall.db
```

Persistence is accessed through repository abstractions.

```text
Services
   │
   ▼
Repositories
   │
   ▼
Database Manager
   │
   ▼
Database
```

Repositories currently include:

```text
ThreatRepository
LogRepository
UserRepository
BlockedIPRepository
```

The repository abstraction is intended to keep application services independent of database-specific implementation details.

---

# Database Portability

The threat repository contains database-portable hourly bucketing through:

```text
_hour_bucket_expr
```

This helps keep analytics logic portable across database implementations.

For production deployments with substantial traffic, SQLite should generally be replaced with a server-grade relational database such as PostgreSQL.

---

# Security Architecture

Immortal Wall AI follows a layered security model.

```text
                 Internet
                    │
                    ▼
             Network Controls
                    │
                    ▼
              API Gateway
                    │
                    ▼
          Authentication Layer
                    │
                    ▼
            Rate Limiting
                    │
                    ▼
          Input Validation
                    │
                    ▼
       Detection / Authorization
                    │
                    ▼
          Persistence Layer
                    │
                    ▼
           Response Engine
```

Security controls include:

* JWT authentication.
* Password hashing.
* Request validation.
* Rate limiting.
* CORS restrictions.
* Authenticated WebSocket connections.
* Threat-intelligence checks.
* Audit-oriented structured logging.
* Database-backed block state.
* Whitelist handling.

---

# Rate Limiting

The application defines three primary rate-limit profiles.

| Profile          |    Rate | Scope                |
| ---------------- | ------: | -------------------- |
| `AUTH_LIMIT`     |  10/min | Login                |
| `ANALYSIS_LIMIT` |  30/min | Threat analysis      |
| `API_LIMIT`      | 120/min | Other protected APIs |

Clients exceeding a configured limit receive:

```text
HTTP 429 Too Many Requests
```

Rate limiting should be enforced at multiple layers in a production environment, including the edge/reverse-proxy layer, because application-level rate limiting alone may not protect the application from connection exhaustion or volumetric attacks.

---

# CORS

CORS is configured using:

```env
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

Do not use unrestricted origins in production.

Avoid:

```text
*
```

for security-sensitive deployments.

Explicitly enumerate trusted frontend origins.

---

# Running the Complete Local Stack

A typical development environment contains four processes.

## Terminal 1 — Backend

```powershell
.\venv\Scripts\Activate.ps1

uvicorn backend.app:app `
  --host 0.0.0.0 `
  --port 8000 `
  --reload
```

## Terminal 2 — Dashboard

```powershell
cd dashboard

npm install
npm run dev
```

## Terminal 3 — Honeypot

```powershell
python honeypot/server.py
```

## Terminal 4 — Optional Simulation

```powershell
$env:IMMORTAL_WALL_SIMULATE = "true"
```

---

# Testing

Run the complete test suite:

```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

Or:

```bash
python -m pytest tests/ -v
```

---

# Test Coverage

## Authentication Tests

`tests/test_auth.py`

Covers:

* Valid email/password authentication.
* Invalid credentials.
* HTTP 401 behavior.
* Protected endpoint authentication.
* WebSocket authentication.
* WebSocket rejection with code `1008`.

## Backend Tests

`tests/test_backend.py`

Covers:

* ML feature extraction.
* 18-feature schema.
* Prediction output.
* Brute-force detection.
* Rule-engine behavior.
* Threat-engine fusion.
* Repository CRUD operations.

## Response Engine Tests

`tests/test_response_engine.py`

Covers:

* IP blocking.
* IP unblocking.
* Database persistence.
* In-memory cache behavior.
* Whitelist bypass.
* Response action execution.

---

# Recommended Test Strategy

For a production-grade implementation, the test pyramid should evolve toward:

```text
                 ┌───────────────┐
                 │  E2E Tests    │
                 └───────┬───────┘
                         │
                 ┌───────▼───────┐
                 │ Integration   │
                 │     Tests     │
                 └───────┬───────┘
                         │
              ┌──────────▼──────────┐
              │    Unit Tests       │
              │                    │
              │ Rules              │
              │ ML features        │
              │ Repositories       │
              │ Services            │
              └────────────────────┘
```

Important security tests should include:

* JWT tampering.
* Expired JWTs.
* Wrong signing keys.
* Algorithm confusion attempts.
* Password timing behavior.
* Brute-force authentication.
* Rate-limit bypass attempts.
* Malformed JSON.
* Oversized payloads.
* WebSocket authentication.
* CORS behavior.
* SQL injection against API inputs.
* XSS payload handling.
* Authorization boundary testing.

---

# Development Workflow

A recommended development workflow is:

```text
Feature / Fix
     │
     ▼
Unit Tests
     │
     ▼
Integration Tests
     │
     ▼
Security Review
     │
     ▼
Code Review
     │
     ▼
Build
     │
     ▼
Deployment
```

Before opening a pull request:

```bash
python -m pytest tests/ -v
```

Also verify:

```text
- No secrets committed
- No debug credentials
- No simulation mode
- No production URLs hard-coded
- No unnecessary CORS origins
- API changes documented
- Database migrations considered
- Model version updated where appropriate
```

---

# Production Considerations

Immortal Wall AI should be treated as a security platform prototype/development system unless the deployment has undergone a dedicated security review.

Before production deployment, address the following.

## 1. Secrets

Do not use:

```env
JWT_SECRET_KEY=CHANGE-THIS-IN-PRODUCTION
```

Use a cryptographically random secret and preferably a managed secret store.

---

## 2. Database

SQLite is appropriate for local development and small deployments.

For production workloads, use a server-grade database such as PostgreSQL.

---

## 3. TLS

Never expose authentication endpoints over plain HTTP.

Production architecture should look like:

```text
HTTPS
  │
  ▼
Reverse Proxy / Load Balancer
  │
  ▼
FastAPI
```

---

## 4. Reverse Proxy

A production deployment should normally place FastAPI behind an appropriate reverse proxy or load balancer.

Responsibilities may include:

* TLS termination.
* Connection limits.
* Request-size limits.
* IP-based rate limiting.
* Access logging.
* Security headers.
* Compression.
* Health checks.

---

## 5. JWT Secret Management

JWT secrets must:

* Be unpredictable.
* Never be committed.
* Never appear in logs.
* Never be exposed to the frontend.
* Be rotated according to organizational requirements.

---

## 6. Authentication Hardening

Consider adding:

* Refresh-token rotation.
* Account lockout or progressive delays.
* MFA.
* Password-reset workflows.
* Session/token revocation.
* Audit logs for authentication events.
* Administrative role separation.

---

## 7. WebSocket Security

For production, review the current query-parameter token model.

The following:

```text
/ws?token=<jwt>
```

can result in tokens appearing in infrastructure logs depending on the deployment.

A production architecture should evaluate alternatives such as:

* Secure session cookies.
* Short-lived WebSocket-specific tokens.
* Header-based authentication where supported.
* Reverse-proxy authentication.

---

## 8. Honeypot Isolation

Run the honeypot in an isolated environment.

Recommended:

```text
Internet
   │
   ▼
Honeypot Network
   │
   │ one-way / restricted telemetry
   ▼
Security Backend
```

The honeypot should not become a pivot point into internal infrastructure.

---

## 9. ML Model Security

Treat ML model artifacts as deployable software assets.

Recommended controls:

* Model checksums.
* Artifact signing.
* Version control.
* Immutable artifact storage.
* Dependency pinning.
* Reproducible training.
* Dataset provenance.
* Model rollback.

Never load untrusted serialized model artifacts.

---

# Observability

A production security platform should provide observability across four dimensions.

## Logs

Structured logs should contain:

```text
timestamp
request_id
event_id
source
event_type
severity
decision
response_action
latency
```

Sensitive values should be redacted.

Never log:

```text
passwords
JWT tokens
session secrets
API secrets
```

---

## Metrics

Recommended metrics include:

```text
requests_total
requests_failed
authentication_failures
rate_limit_exceeded
threats_detected
threats_blocked
threats_by_class
ml_predictions_total
ml_prediction_confidence
ml_drift_score
websocket_connections
response_latency
database_latency
```

---

## Health Checks

The public health endpoint:

```http
GET /api/health
```

should remain lightweight.

For production, distinguish between:

```text
Liveness
Readiness
Dependency health
```

A process being alive does not necessarily mean it is ready to serve traffic.

---

# Threat Model

Immortal Wall AI should be designed with the assumption that attackers can:

* Send malformed requests.
* Attempt credential stuffing.
* Enumerate API endpoints.
* Probe sensitive files.
* Manipulate HTTP headers.
* Send malicious payloads.
* Attempt SQL injection.
* Attempt XSS.
* Abuse WebSocket connections.
* Flood endpoints.
* Attempt to poison telemetry.
* Send adversarial or misleading data.
* Attempt to exploit vulnerable dependencies.

The security architecture should therefore treat **all external telemetry as untrusted input**.

A particularly important principle is:

> **Detection data is evidence, not truth.**

An attacker who can influence telemetry must not automatically gain authorization to execute privileged response actions.

---

# Security Boundary

The following components should be treated as untrusted input boundaries:

```text
HTTP Request
     │
     ▼
Pydantic Validation
     │
     ▼
Business Logic
     │
     ▼
Repository
     │
     ▼
Database
```

Likewise:

```text
Honeypot Input
     │
     ▼
Validation
     │
     ▼
Threat Processing
```

and:

```text
Agent Telemetry
     │
     ▼
Validation / Normalization
     │
     ▼
Detection
```

---

# API Documentation

When the backend is running, FastAPI automatically provides:

### Swagger UI

```text
http://localhost:8000/docs
```

### OpenAPI Schema

```text
http://localhost:8000/openapi.json
```

Swagger UI is useful for:

* API exploration.
* Authentication testing.
* Request validation.
* Response inspection.
* Development debugging.

Production deployments should carefully consider whether interactive API documentation should remain publicly accessible.

---

# Troubleshooting

## Backend does not start

Verify:

```bash
python --version
pip --version
```

Confirm the virtual environment is active:

```powershell
.\venv\Scripts\Activate.ps1
```

Then reinstall dependencies:

```bash
pip install -r requirements.txt
```

---

## Model not found

Run:

```bash
python train.py --samples 8000
```

Then verify:

```text
models/advanced_model.pkl
```

exists.

---

## Login fails

Check:

```env
ADMIN_EMAIL=...
ADMIN_PASSWORD=...
JWT_SECRET_KEY=...
```

Remember that the initial administrator configuration is applied during first-run account creation.

---

## Dashboard cannot connect

Verify that the backend is running:

```text
http://localhost:8000/api/health
```

Then check:

```env
CORS_ORIGINS=http://localhost:5173
```

Also confirm that the frontend is targeting the correct API base URL.

---

## WebSocket closes immediately

Verify:

```text
/ws?token=<valid-jwt>
```

A missing or invalid token results in:

```text
1008 Policy Violation
```

---

## No threat events appear

Check:

1. Backend status.
2. Agent status.
3. Simulation mode.
4. Honeypot status.
5. Database connectivity.
6. Browser network logs.
7. Backend logs.

For development, enable:

```powershell
$env:IMMORTAL_WALL_SIMULATE = "true"
```

---

# Known Limitations

Immortal Wall AI currently has several limitations that should be understood before production deployment.

### ML Evaluation

Current reported F1 scores may be based on generated or controlled datasets and therefore may not represent production performance.

### Drift Detection

The current drift mechanism primarily monitors prediction distribution and should not be interpreted as comprehensive statistical drift monitoring.

### Database

SQLite is suitable for development but is not the preferred architecture for a horizontally scaled security platform.

### JWT

HS256 requires secure symmetric-secret management across all token-verifying services.

### WebSocket Authentication

The current query-parameter token approach should be reviewed before production deployment because URLs may be logged by infrastructure.

### Threat Intelligence

Static indicator lists require a controlled update process and should not be considered a complete external threat-intelligence service.

### Automated Blocking

Automatic blocking can generate false positives. Production deployments should consider:

* Confidence thresholds.
* Block duration.
* Human approval for high-impact actions.
* Automatic rollback.
* Whitelists.
* Rate-based escalation.
* Audit trails.

---

# Roadmap

Potential future improvements include:

## Detection

* [ ] Stateful behavioral detection.
* [ ] Temporal attack correlation.
* [ ] Multi-event attack chains.
* [ ] MITRE ATT&CK technique mapping.
* [ ] Improved anomaly detection.
* [ ] Entity-based risk scoring.

## Machine Learning

* [ ] Feature-drift detection.
* [ ] Model registry.
* [ ] Automated model evaluation.
* [ ] Model rollback.
* [ ] Explainable predictions.
* [ ] Production validation datasets.
* [ ] Precision/recall monitoring.
* [ ] False-positive tracking.
* [ ] Continuous evaluation pipeline.

## Security

* [ ] MFA.
* [ ] Refresh-token rotation.
* [ ] Token revocation.
* [ ] Stronger password-policy enforcement.
* [ ] Security headers.
* [ ] CSP.
* [ ] CSRF strategy where applicable.
* [ ] Centralized secret management.
* [ ] Comprehensive audit logging.

## Infrastructure

* [ ] PostgreSQL support.
* [ ] Redis-backed rate limiting.
* [ ] Distributed WebSocket infrastructure.
* [ ] Docker deployment.
* [ ] Kubernetes deployment.
* [ ] Horizontal scaling.
* [ ] Centralized metrics.
* [ ] Prometheus integration.
* [ ] Grafana dashboards.

## Threat Intelligence

* [ ] External threat-intelligence feeds.
* [ ] IOC lifecycle management.
* [ ] IOC confidence scores.
* [ ] IOC expiration.
* [ ] Feed provenance.
* [ ] Automated feed synchronization.

---

# Design Principles

Immortal Wall AI follows several engineering principles.

## 1. Defense in Depth

No single detection mechanism should be trusted as the entire security boundary.

```text
Rules
 +
Threat Intelligence
 +
ML
 +
Behavior
 +
Authentication
 +
Rate Limiting
 +
Response Controls
```

---

## 2. Explainability

Security decisions should be explainable whenever possible.

A security analyst should be able to answer:

```text
Why was this event classified as malicious?
```

rather than receiving only:

```text
malicious = true
```

---

## 3. Single Source of Truth

Shared state and security constants should have a canonical owner.

Examples:

```text
Threat intelligence → backend/threat_intel/constants.py

Application singletons → backend/container.py

Password hashing → UserRepository
```

---

## 4. Separation of Responsibilities

The architecture separates:

```text
Routes
Services
Repositories
Models
Detection
Response
Threat Intelligence
```

This reduces coupling and makes components independently testable.

---

## 5. Secure Defaults

Production-sensitive functionality should default toward the safer behavior.

Examples:

```text
Simulation = disabled
Protected endpoints = authenticated
Invalid JWT = rejected
Invalid login = HTTP 401
Rate limits = enabled
```

---

# Engineering Notes

The project intentionally keeps the core security pipeline modular:

```text
API Layer
   ↓
Service Layer
   ↓
Detection Layer
   ↓
Repository Layer
   ↓
Persistence
```

This makes it possible to evolve individual components without rewriting the entire application.

For example, the ML engine can eventually be replaced with another inference implementation without requiring the dashboard or repository layer to understand model internals.

---

# Performance Considerations

The most likely scaling pressure points are:

1. Event ingestion.
2. Database writes.
3. Threat analytics queries.
4. WebSocket fan-out.
5. ML inference.
6. Rate-limit state.

A production architecture should avoid coupling event ingestion directly to expensive synchronous processing.

A scalable evolution could look like:

```text
                    ┌─────────────┐
                    │ API Gateway │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Event Queue │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          Rule Worker   ML Worker   Analytics
              │            │            │
              └────────────┼────────────┘
                           ▼
                     Event Storage
                           │
                           ▼
                     WebSocket Feed
```

This architecture would allow the ingestion layer and analysis workers to scale independently.

---

# Deployment Checklist

Before calling a deployment production-ready:

* [ ] Replace development JWT secret.
* [ ] Remove default credentials.
* [ ] Disable simulation.
* [ ] Restrict CORS.
* [ ] Enable HTTPS.
* [ ] Put API behind a reverse proxy.
* [ ] Configure request-size limits.
* [ ] Configure connection limits.
* [ ] Review rate limiting.
* [ ] Move from SQLite to PostgreSQL if required.
* [ ] Configure backups.
* [ ] Configure structured logging.
* [ ] Configure metrics.
* [ ] Configure alerting.
* [ ] Isolate the honeypot.
* [ ] Review WebSocket authentication.
* [ ] Review password hashing parameters.
* [ ] Scan dependencies for known vulnerabilities.
* [ ] Scan container images if containers are used.
* [ ] Validate ML performance on representative data.
* [ ] Configure model versioning.
* [ ] Configure model rollback.
* [ ] Perform penetration testing.
* [ ] Perform authorization testing.
* [ ] Perform incident-response testing.
* [ ] Document operational runbooks.

---

# Contributing

Contributions should preserve the architectural boundaries of the project.

Before submitting a change:

```bash
python -m pytest tests/ -v
```

For security-sensitive changes, include tests demonstrating both:

```text
Expected behavior
+
Rejected/abuse behavior
```

Examples:

```text
Valid JWT
Invalid JWT

Valid login
Invalid login

Allowed request
Rate-limited request

Allowed IP
Blocked IP

Normal event
Malicious event
```

Avoid introducing:

* Hard-coded secrets.
* Global mutable state without justification.
* Duplicate threat-intelligence constants.
* Authentication logic outside the security/authentication layer.
* Database access directly inside API routes.
* `print()`-based production logging.
* Production-only behavior hidden behind undocumented environment variables.

---

# License

This project does not currently specify a license.

Until a license is added to the repository, the default assumption should be that the source code is **not licensed for unrestricted redistribution or commercial use**.

Add a `LICENSE` file before publishing the project for external use.

Recommended choices should be evaluated based on the project's intended distribution model.

---

# Disclaimer

Immortal Wall AI is a cybersecurity engineering project intended for **authorized defensive security monitoring, research, development, and testing**.

Do not deploy the platform against systems, networks, applications, or infrastructure that you do not own or have explicit authorization to monitor.

Automated response mechanisms can cause operational impact if detection produces false positives. Always validate detection and response policies in a controlled environment before enabling automatic blocking in production.

---

# Summary

Immortal Wall AI combines:

```text
┌──────────────────────────────────────────┐
│            IMMORTAL WALL AI              │
├──────────────────────────────────────────┤
│                                          │
│  Real-Time Monitoring                    │
│  Rule-Based Detection                    │
│  Machine Learning                        │
│  Threat Intelligence                     │
│  Honeypot Telemetry                      │
│  Automated Response                      │
│  JWT Authentication                      │
│  Rate Limiting                            │
│  ML Monitoring                            │
│  React Security Dashboard                │
│  WebSocket Live Feed                     │
│  Persistent Threat Data                  │
│                                          │
└──────────────────────────────────────────┘
```

The core design goal is straightforward:

> **Detect threats early, explain why they were detected, persist the evidence, and provide controlled automated response capabilities.**

The architecture is intentionally modular so that individual detection, ML, storage, authentication, and response components can evolve independently as the platform matures.
