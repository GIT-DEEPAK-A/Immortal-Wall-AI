# Immortal Wall AI

> AI-powered cybersecurity defense platform — real-time monitoring, rule-based detection, machine learning, honeypot-based threat intelligence, and automated response.

---

## Running the project

### 1 — Backend (FastAPI)

```powershell
# from project root — immortal-wall-ai/
.\venv\Scripts\Activate.ps1
uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```

API  →  `http://localhost:8000`  
Docs →  `http://localhost:8000/docs`  
WS   →  `ws://localhost:8000/ws`

### 2 — Frontend (React + Vite)

```powershell
cd dashboard
npm install       # first time only
npm run dev
```

Dashboard → `http://localhost:5173`

### 3 — Honeypot server *(optional)*

```powershell
python -m honeypot.server
```

Runs on `http://localhost:5001`. Logs to `logs/honeypot.log`.

### 4 — Traffic simulation *(optional — populates the dashboard)*

```powershell
python -m simulation.traffic_generator
```

---

## Login

The dashboard is protected by a single system passkey.

```
Passkey: 123456
```

Flow: **Splash screen → Login → Dashboard**

Change the passkey by setting `SYSTEM_PASSKEY=your_new_key` in `.env`.

---

## Architecture

```
Incoming traffic
      │
      ▼
   Agent  (monitor + collector + sender)
      │
      ▼
   Backend API  (FastAPI · port 8000)
      ├── Rule Engine      → deterministic threat score
      ├── ML Engine        → behavioral anomaly score
      └── Threat Engine    → combined verdict
                │
                ├── Response Engine  → block / rate-limit / alert / isolate
                ├── Database         → SQLite via SQLAlchemy
                └── WebSocket hub    → pushes live events to dashboard
                                            │
                                            ▼
                                    React Dashboard  (Vite · port 5173)
```

| Component | Path | Responsibility |
|---|---|---|
| Agent | `agent/` | Collects system events, tags threat flags, forwards to backend |
| Backend | `backend/` | FastAPI API server, WS hub, auth, analysis pipeline |
| Rule Engine | `backend/services/rule_engine.py` | Deterministic pattern matching |
| ML Engine | `backend/services/ml_engine.py` | Ensemble classifier (RF + GBM) |
| Threat Engine | `backend/services/threat_engine.py` | Combines rule + ML scores |
| Response Engine | `backend/services/response_engine.py` | Executes block / alert actions |
| Honeypot | `honeypot/` | Flask decoy server, captures attacker behaviour |
| Simulation | `simulation/` | Generates synthetic normal + attack traffic |
| Dashboard | `dashboard/src/` | React 19 + Vite + Tailwind |

---

## Project structure

```
immortal-wall-ai/
├── agent/                 # host monitoring agent
├── backend/
│   ├── app.py             # FastAPI app, WS hub, lifespan
│   ├── config.py
│   ├── database/          # SQLAlchemy models + queries
│   ├── routes/            # auth, threats, logs, status
│   └── services/          # threat/rule/ml/response engines
├── dashboard/
│   ├── src/
│   │   ├── App.jsx                      # splash → login → dashboard
│   │   └── components/
│   │       ├── SplashScreen.jsx         # cinematic intro
│   │       ├── LoginPage.jsx            # passkey entry
│   │       ├── Dashboard.jsx            # main shell + router
│   │       ├── Sidebar.jsx
│   │       ├── StatusCards.jsx
│   │       ├── GlobeVisualization.jsx
│   │       ├── ThreatAlerts.jsx
│   │       ├── TerminalLogs.jsx
│   │       ├── HoneypotCards.jsx
│   │       ├── AnalyticsPage.jsx
│   │       ├── LiveAttacksPage.jsx
│   │       ├── HoneypotsPage.jsx
│   │       ├── ThreatPredictionPage.jsx
│   │       └── SettingsPage.jsx
│   ├── tailwind.config.js
│   └── vite.config.js
├── honeypot/              # Flask deception server
├── simulation/            # traffic generator
├── utils/                 # logger, constants, helpers
├── tests/
├── .env.example
└── requirements.txt
```

---

## Environment

Copy `.env.example` to `.env`. The only required change for local dev is none — defaults work out of the box.

```env
SYSTEM_PASSKEY=123456        # dashboard passkey
SECRET_KEY=change-me         # JWT / session signing key
DATABASE_URL=                # leave empty → SQLite auto-created in data/
```

---

## Tech stack

| Layer | Tech |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn, SQLAlchemy, scikit-learn |
| Frontend | React 19, Vite, Tailwind CSS 3, Framer Motion, Axios |
| Database | SQLite (dev) — swap `DATABASE_URL` for PostgreSQL in prod |
| Honeypot | Flask |
| Tests | pytest, pytest-asyncio |

---

## Tests

```powershell
pytest tests/ -v
pytest tests/ --cov=backend --cov-report=term-missing
```
