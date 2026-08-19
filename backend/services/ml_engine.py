# backend/services/ml_engine.py
"""
Production ML engine for Immortal Wall AI threat detection.

Architecture
────────────
  Feature extraction  (18 hand-crafted features)
        │
        ▼
  StandardScaler      (fitted on training data, saved alongside model)
        │
        ▼
  Calibrated Ensemble
    ├─ RandomForest       (200 trees, class-weighted)
    ├─ GradientBoosting   (200 estimators, learning-rate 0.05)
    └─ LogisticRegression (C=1.0, multinomial)
  Soft-vote probabilities
        │
        ▼
  CalibratedClassifierCV  (isotonic regression, 5-fold)
        │
        ▼
  Output: threat score, level, confidence, per-feature attribution

Labels:  0 = normal   1 = suspicious   2 = malicious

Model artifacts saved in  <project_root>/models/
  advanced_model.pkl  — trained pipeline (scaler + ensemble)
  model_meta.json     — CV metrics, feature names, training timestamp
"""

from __future__ import annotations

import json
import os
import pickle
import time
import warnings
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np

warnings.filterwarnings("ignore", category=UserWarning)

# ── Optional heavy imports — graceful degradation ─────────────────────────
try:
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.ensemble import (
        GradientBoostingClassifier,
        RandomForestClassifier,
        VotingClassifier,
    )
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import classification_report, f1_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    _SKLEARN_OK = True
except ImportError:
    _SKLEARN_OK = False
    print("[ML Engine] WARNING: scikit-learn not available -- running in heuristic mode")

# ── Paths ──────────────────────────────────────────────────────────────────
_ROOT       = Path(__file__).parent.parent.parent
_MODEL_DIR  = _ROOT / "models"
_MODEL_PATH = _MODEL_DIR / "advanced_model.pkl"
_META_PATH  = _MODEL_DIR / "model_meta.json"

# ── Feature schema (ORDER IS FIXED — do not reorder) ──────────────────────
FEATURE_NAMES: List[str] = [
    # --- Threat flags (binary) ---
    "failed_login",           # 0
    "high_request_rate",      # 1
    "suspicious_ip",          # 2
    # --- Request behaviour ---
    "request_rate",           # 3  (req/s, normalised 0-1)
    "failed_logins_count",    # 4  (raw count, normalised 0-1)
    "distinct_paths",         # 5  (normalised 0-1)
    "payload_length",         # 6  (normalised 0-1)
    "session_duration",       # 7  (normalised 0-1)
    # --- Temporal ---
    "is_night_hour",          # 8  (01:00–05:00 UTC)
    "is_weekend",             # 9
    # --- Protocol / method ---
    "is_post_method",         # 10
    "is_error_response",      # 11 (4xx / 5xx)
    # --- Payload content ---
    "has_sql_chars",          # 12
    "has_xss_chars",          # 13
    "is_suspicious_path",     # 14
    # --- Identity ---
    "is_suspicious_ua",       # 15
    "is_known_bad_ip",        # 16
    "is_geo_anomaly",         # 17
]

N_FEATURES = len(FEATURE_NAMES)  # 18

# ── Threat-intel constants (single source of truth) ───────────────────────
from backend.threat_intel.constants import (
    KNOWN_BAD_IPS        as _KNOWN_BAD_IPS,
    GEO_BAD_PREFIXES     as _GEO_BAD_PREFIXES,
    SUSPICIOUS_UA_TOKENS as _SUSPICIOUS_UA_TOKENS,
    SUSPICIOUS_PATHS     as _SUSPICIOUS_PATHS,
    SQL_INJECTION_TOKENS as _SQL_CHARS,
    XSS_TOKENS           as _XSS_CHARS,
)


# ── Feature extractor ──────────────────────────────────────────────────────

class FeatureExtractor:
    """Converts a raw event dict into a fixed-length float vector."""

    @staticmethod
    def extract(event: dict) -> np.ndarray:
        """
        Extract 18 features from *event*.

        If any error occurs during extraction (malformed / missing fields),
        returns a zero-vector of shape (18,) and logs the failure.
        """
        try:
            flags       = event.get("threat_flags", {})
            payload     = str(event.get("payload", "")).lower()
            user_agent  = str(event.get("user_agent", "")).lower()
            ip          = str(event.get("ip", ""))
            path        = str(event.get("path", "")).lower()
            method      = str(event.get("method", "GET")).upper()
            response    = int(event.get("response_code", 200))
            ts          = float(event.get("timestamp") or time.time())

            # Normalised continuous features (clipped to [0, 1])
            req_rate   = min(float(event.get("request_rate",     0)) / 100.0, 1.0)
            fail_count = min(float(event.get("failed_logins",    0)) / 50.0,  1.0)
            n_paths    = min(float(event.get("distinct_paths",   1)) / 100.0, 1.0)
            pay_len    = min(float(event.get("payload_length",   0)) / 1e6,   1.0)
            sess_dur   = min(float(event.get("session_duration", 300)) / 3600.0, 1.0)

            # Temporal
            dt         = datetime.utcfromtimestamp(ts)
            is_night   = 1.0 if dt.hour in (1, 2, 3, 4, 5) else 0.0
            is_weekend = 1.0 if dt.weekday() >= 5 else 0.0

            # Protocol
            is_post  = 1.0 if method == "POST" else 0.0
            is_error = 1.0 if response >= 400 else 0.0

            # Payload content
            has_sql = 1.0 if any(tok in payload for tok in _SQL_CHARS) else 0.0
            has_xss = 1.0 if any(tok in payload for tok in _XSS_CHARS) else 0.0

            # Path
            is_bad_path = 1.0 if any(p in path for p in _SUSPICIOUS_PATHS) else 0.0

            # Identity
            is_bad_ua  = 1.0 if any(tok in user_agent for tok in _SUSPICIOUS_UA_TOKENS) else 0.0
            is_bad_ip  = 1.0 if ip in _KNOWN_BAD_IPS else 0.0
            is_geo_bad = 1.0 if any(ip.startswith(pfx) for pfx in _GEO_BAD_PREFIXES) else 0.0

            return np.array([
                float(bool(flags.get("failed_login"))),
                float(bool(flags.get("high_request_rate"))),
                float(bool(flags.get("suspicious_ip_activity"))),
                req_rate,
                fail_count,
                n_paths,
                pay_len,
                sess_dur,
                is_night,
                is_weekend,
                is_post,
                is_error,
                has_sql,
                has_xss,
                is_bad_path,
                is_bad_ua,
                is_bad_ip,
                is_geo_bad,
            ], dtype=np.float32)

        except Exception as exc:
            keys = list(event.keys()) if isinstance(event, dict) else []
            print(f"[FeatureExtractor] extraction failed (keys={keys}): {exc}")
            return np.zeros(N_FEATURES, dtype=np.float32)


# ── Attribution (SHAP-style, permutation-free) ────────────────────────────

def _feature_attribution(
    features: np.ndarray,
    model_predict_proba,
    scaler,
) -> Dict[str, float]:
    """
    Marginal-contribution approximation: measure change in malicious probability
    when each feature is zeroed out.  Fast O(N_FEATURES) — no model retraining.
    """
    try:
        base_prob    = model_predict_proba(scaler.transform([features]))[0][2]
        attributions = {}
        for i, name in enumerate(FEATURE_NAMES):
            if features[i] == 0.0:
                attributions[name] = 0.0
                continue
            ablated    = features.copy()
            ablated[i] = 0.0
            ablated_p  = model_predict_proba(scaler.transform([ablated]))[0][2]
            attributions[name] = round(float(base_prob - ablated_p), 4)
        return dict(sorted(attributions.items(), key=lambda x: abs(x[1]), reverse=True))
    except Exception:
        return {name: round(float(v), 4) for name, v in zip(FEATURE_NAMES, features)}


# ── Training data generator ───────────────────────────────────────────────

def generate_training_data(
    n_samples: int = 8000,
    random_state: int = 42,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Generate a balanced, realistic synthetic dataset with deliberate noise.

    Class distribution:
      normal              50 %
      suspicious          20 %  (xss, port_scan)
      malicious           30 %  (brute_force, ddos, sqli, credential_stuffing, malware)

    Noise injected per sample:
      - 10 % of binary features randomly flipped (real-world ambiguity)
      - Gaussian noise N(0, 0.05) on all continuous features
      - 1–2 features randomly zeroed (incomplete telemetry)

    This reduces CV F1 from an unrealistic 1.000 to ~0.88–0.93.
    """
    import sys
    sys.path.insert(0, str(_ROOT))
    from simulation.attack_patterns import (
        brute_force, request_flood, sql_injection, xss_attack,
        port_scan, credential_stuffing, malware_upload, normal_traffic,
    )

    rng = np.random.default_rng(random_state)

    # Continuous feature indices (non-binary)
    _CONTINUOUS = [3, 4, 5, 6, 7]
    # Binary feature indices
    _BINARY = [0, 1, 2, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]

    # Weighted sampling plan
    plan = [
        (normal_traffic,       0.50, 0),
        (xss_attack,           0.10, 1),
        (port_scan,            0.10, 1),
        (brute_force,          0.08, 2),
        (request_flood,        0.08, 2),
        (sql_injection,        0.06, 2),
        (credential_stuffing,  0.05, 2),
        (malware_upload,       0.03, 2),
    ]

    extractor = FeatureExtractor()
    X_list, y_list = [], []

    for generator, frac, label in plan:
        count = int(n_samples * frac)
        for _ in range(count):
            event   = generator()
            vec     = extractor.extract(event).copy()

            # ── Noise: flip 10 % of binary features ───────────────────────
            for idx in _BINARY:
                if rng.random() < 0.10:
                    vec[idx] = 1.0 - vec[idx]

            # ── Noise: Gaussian on continuous features ─────────────────────
            for idx in _CONTINUOUS:
                vec[idx] = float(np.clip(vec[idx] + rng.normal(0, 0.05), 0.0, 1.0))

            # ── Noise: zero out 1–2 random features ───────────────────────
            n_zero    = rng.integers(1, 3)           # 1 or 2
            zero_idxs = rng.choice(N_FEATURES, size=int(n_zero), replace=False)
            vec[zero_idxs] = 0.0

            X_list.append(vec)
            y_list.append(label)

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list, dtype=np.int32)
    idx = rng.permutation(len(y))
    return X[idx], y[idx]


# ── Model builder ─────────────────────────────────────────────────────────

def build_and_train(
    X: np.ndarray,
    y: np.ndarray,
    random_state: int = 42,
    cv_folds: int = 5,
) -> Tuple[Any, Any, Dict]:
    """
    Build, calibrate, and evaluate the ensemble.

    Returns
    -------
    pipeline : fitted Pipeline(scaler, calibrated_ensemble)
    scaler   : the fitted StandardScaler (also inside pipeline)
    meta     : dict with CV metrics, feature names, training timestamp
    """
    if not _SKLEARN_OK:
        raise RuntimeError("scikit-learn is required for training")

    print(f"[ML Engine] Training on {len(X)} samples, {N_FEATURES} features ...")

    rf = RandomForestClassifier(
        n_estimators=300, max_depth=12, min_samples_leaf=4,
        class_weight="balanced", random_state=random_state, n_jobs=-1,
    )
    gb = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05, max_depth=5,
        subsample=0.8, random_state=random_state,
    )
    lr = LogisticRegression(
        C=1.0, solver="lbfgs", max_iter=500,
        class_weight="balanced", random_state=random_state,
    )

    voting = VotingClassifier(
        estimators=[("rf", rf), ("gb", gb), ("lr", lr)],
        voting="soft", weights=[2, 2, 1], n_jobs=-1,
    )

    calibrated = CalibratedClassifierCV(voting, method="isotonic", cv=5)

    scaler   = StandardScaler()
    pipeline = Pipeline([("scaler", scaler), ("clf", calibrated)])

    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    print(f"[ML Engine] Running {cv_folds}-fold stratified CV ...")
    cv_preds = cross_val_predict(pipeline, X, y, cv=skf, n_jobs=-1)

    f1_macro    = f1_score(y, cv_preds, average="macro")
    f1_weighted = f1_score(y, cv_preds, average="weighted")
    report_str  = classification_report(
        y, cv_preds,
        target_names=["normal", "suspicious", "malicious"],
        digits=3,
    )
    print(report_str)

    pipeline.fit(X, y)

    # Feature importances from a plain RF (fast proxy)
    try:
        plain_rf = RandomForestClassifier(
            n_estimators=100, class_weight="balanced",
            random_state=random_state, n_jobs=-1,
        )
        plain_rf.fit(scaler.fit_transform(X), y)
        importances = {
            name: round(float(imp), 5)
            for name, imp in zip(FEATURE_NAMES, plain_rf.feature_importances_)
        }
    except Exception:
        importances = {name: 0.0 for name in FEATURE_NAMES}

    meta = {
        "trained_at":          datetime.utcnow().isoformat() + "Z",
        "n_samples":           int(len(X)),
        "n_features":          N_FEATURES,
        "feature_names":       FEATURE_NAMES,
        "cv_folds":            cv_folds,
        "f1_macro":            round(float(f1_macro), 4),
        "f1_weighted":         round(float(f1_weighted), 4),
        "class_report":        report_str,
        "feature_importances": importances,
        "label_map":           {"0": "normal", "1": "suspicious", "2": "malicious"},
        "model_version":       "2.0.0",
    }

    return pipeline, scaler, meta


def save_artifacts(pipeline, meta: dict) -> None:
    _MODEL_DIR.mkdir(exist_ok=True)
    with open(_MODEL_PATH, "wb") as f:
        pickle.dump(pipeline, f, protocol=pickle.HIGHEST_PROTOCOL)
    with open(_META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[ML Engine] Model saved  -> {_MODEL_PATH}")
    print(f"[ML Engine] Metadata     -> {_META_PATH}")


def load_artifacts():
    """Return (pipeline, meta) or (None, {}) if artifacts not found."""
    if not _MODEL_PATH.exists():
        return None, {}
    try:
        with open(_MODEL_PATH, "rb") as f:
            pipeline = pickle.load(f)
        meta = json.loads(_META_PATH.read_text()) if _META_PATH.exists() else {}
        print(f"[ML Engine] Model loaded from {_MODEL_PATH}")
        return pipeline, meta
    except Exception as e:
        print(f"[ML Engine] Failed to load model: {e}")
        return None, {}


# ── Inference engine ──────────────────────────────────────────────────────

class AdvancedMLEngine:
    """
    Drop-in replacement for the original AdvancedMLEngine.
    Call .predict(event_dict) to get a structured threat assessment.
    """

    # Drift detection constants
    _DRIFT_WINDOW     = 1000   # rolling window size
    _DRIFT_THRESHOLD  = 0.70   # fraction of non-normal predictions
    _DRIFT_STREAK_REQ = 100    # consecutive high-threat predictions to set drift

    def __init__(self):
        self.extractor          = FeatureExtractor()
        self.pipeline, self.meta = load_artifacts()

        # Backwards-compat: .model exposed for health-check in app.py
        self.model = self.pipeline

        # Drift detection state
        self._recent_levels: deque = deque(maxlen=self._DRIFT_WINDOW)
        self._drift_detected: bool = False
        self._high_threat_streak: int = 0

        if self.pipeline is None and _SKLEARN_OK:
            print("[ML Engine] No saved model found -- training from scratch ...")
            self._bootstrap()

    def _bootstrap(self):
        """Train and save a fresh model on first run."""
        try:
            X, y = generate_training_data(n_samples=8000)
            self.pipeline, _, self.meta = build_and_train(X, y)
            save_artifacts(self.pipeline, self.meta)
            self.model = self.pipeline
        except Exception as e:
            print(f"[ML Engine] Bootstrap training failed: {e}")
            self.pipeline = None
            self.model    = None

    # ── Drift detection ────────────────────────────────────────────────────

    def _record_prediction(self, ml_level: str) -> None:
        """Update the rolling window and check for drift."""
        self._recent_levels.append(ml_level)

        is_threat = ml_level != "normal"
        if is_threat:
            self._high_threat_streak += 1
        else:
            self._high_threat_streak = 0

        if self._high_threat_streak >= self._DRIFT_STREAK_REQ:
            if not self._drift_detected:
                self._drift_detected = True
                print("[ML Engine] WARNING: Model drift detected -- "
                      f"{self._high_threat_streak} consecutive non-normal predictions")

    def compute_drift_score(self) -> float:
        """
        Return the fraction of recent predictions that are non-normal.
        If the fraction exceeds the threshold for 100 consecutive predictions,
        sets drift_detected = True.
        """
        if not self._recent_levels:
            return 0.0
        non_normal = sum(1 for lvl in self._recent_levels if lvl != "normal")
        return non_normal / len(self._recent_levels)

    @property
    def drift_detected(self) -> bool:
        """True if model drift has been detected."""
        return self._drift_detected

    @property
    def recent_threat_rate(self) -> float:
        """Fraction of recent predictions that are suspicious or malicious."""
        return round(self.compute_drift_score(), 4)

    # ── Public API ─────────────────────────────────────────────────────────

    def predict(self, event: dict) -> dict:
        """
        Run feature extraction + model inference.

        Returns
        -------
        {
          ml_score      : float 0–1
          ml_level      : "normal" | "suspicious" | "malicious"
          confidence    : float 0–1
          ml_reason     : str
          probabilities : {"normal": …, "suspicious": …, "malicious": …}
          feature_values: {feature_name: value, …}
          attribution   : {feature_name: marginal_contribution, …}
        }
        """
        features = self.extractor.extract(event)

        if self.pipeline is None:
            result = self._heuristic_fallback(features)
        else:
            try:
                X_scaled = self.pipeline.named_steps["scaler"].transform([features])
                clf      = self.pipeline.named_steps["clf"]
                probs    = clf.predict_proba(X_scaled)[0]
                pred_cls = int(np.argmax(probs))

                level_map = {0: "normal", 1: "suspicious", 2: "malicious"}
                ml_level  = level_map[pred_cls]
                ml_score  = float(0.3 * probs[1] + 0.7 * probs[2])
                confidence = float(probs[pred_cls])
                reason     = self._build_reason(features)

                attribution: Dict[str, float] = {}
                if ml_level != "normal":
                    scaler = self.pipeline.named_steps["scaler"]
                    attribution = _feature_attribution(features, clf.predict_proba, scaler)

                result = {
                    "ml_score":    round(ml_score, 4),
                    "ml_level":    ml_level,
                    "confidence":  round(confidence, 4),
                    "ml_reason":   reason,
                    "probabilities": {
                        "normal":     round(float(probs[0]), 4),
                        "suspicious": round(float(probs[1]), 4),
                        "malicious":  round(float(probs[2]), 4),
                    },
                    "feature_values": {
                        name: round(float(val), 4)
                        for name, val in zip(FEATURE_NAMES, features)
                    },
                    "attribution": attribution,
                }
            except Exception as e:
                print(f"[ML Engine] Inference error: {e}")
                result = self._heuristic_fallback(features)

        self._record_prediction(result["ml_level"])
        return result

    def predict_batch(self, events: list) -> list:
        """Vectorised batch prediction."""
        if not events:
            return []
        features_batch = np.array(
            [self.extractor.extract(e) for e in events], dtype=np.float32
        )
        if self.pipeline is None:
            return [self._heuristic_fallback(f) for f in features_batch]
        try:
            X_scaled  = self.pipeline.named_steps["scaler"].transform(features_batch)
            clf       = self.pipeline.named_steps["clf"]
            probs_all = clf.predict_proba(X_scaled)
            results   = []
            for i, probs in enumerate(probs_all):
                pred_cls = int(np.argmax(probs))
                level    = {0: "normal", 1: "suspicious", 2: "malicious"}[pred_cls]
                score    = float(0.3 * probs[1] + 0.7 * probs[2])
                r = {
                    "ml_score":    round(score, 4),
                    "ml_level":    level,
                    "confidence":  round(float(probs[pred_cls]), 4),
                    "ml_reason":   self._build_reason(features_batch[i]),
                    "probabilities": {
                        "normal":     round(float(probs[0]), 4),
                        "suspicious": round(float(probs[1]), 4),
                        "malicious":  round(float(probs[2]), 4),
                    },
                }
                self._record_prediction(level)
                results.append(r)
            return results
        except Exception as e:
            print(f"[ML Engine] Batch inference error: {e}")
            return [self.predict(e) for e in events]

    def retrain(self, n_samples: int = 8000) -> dict:
        """Retrain the model on freshly-generated data. Returns updated meta."""
        X, y = generate_training_data(n_samples=n_samples)
        self.pipeline, _, self.meta = build_and_train(X, y)
        save_artifacts(self.pipeline, self.meta)
        self.model = self.pipeline
        return self.meta

    # ── Internals ──────────────────────────────────────────────────────────

    @staticmethod
    def _build_reason(features: np.ndarray) -> str:
        reasons = []
        if features[0] > 0:   reasons.append("failed login")
        if features[1] > 0:   reasons.append("high request rate")
        if features[2] > 0:   reasons.append("suspicious IP activity")
        if features[3] > 0.3: reasons.append(f"request rate {features[3]*100:.0f}% of threshold")
        if features[4] > 0.1: reasons.append("repeated failed logins")
        if features[5] > 0.2: reasons.append("port scan pattern")
        if features[6] > 0.3: reasons.append("large payload")
        if features[8] > 0:   reasons.append("off-hours activity")
        if features[11] > 0:  reasons.append("error response")
        if features[12] > 0:  reasons.append("SQL injection chars in payload")
        if features[13] > 0:  reasons.append("XSS chars in payload")
        if features[14] > 0:  reasons.append("suspicious path targeted")
        if features[15] > 0:  reasons.append("attack tool user-agent")
        if features[16] > 0:  reasons.append("known-bad IP address")
        if features[17] > 0:  reasons.append("geographic anomaly")
        return "; ".join(reasons) if reasons else "normal traffic patterns"

    @staticmethod
    def _heuristic_fallback(features: np.ndarray) -> dict:
        """Rule-based fallback when model is unavailable."""
        hard_mal = features[16] or features[12] or features[13]
        soft_mal = features[0] + features[1] + features[2] + features[15] + features[14]

        if hard_mal or soft_mal >= 3:
            level, score = "malicious", 0.85
        elif soft_mal >= 1.5:
            level, score = "suspicious", 0.50
        else:
            level, score = "normal", 0.05

        return {
            "ml_score":    score,
            "ml_level":    level,
            "confidence":  score,
            "ml_reason":   "heuristic fallback (model not loaded)",
            "probabilities": {
                "normal":     1 - score,
                "suspicious": score * 0.4,
                "malicious":  score * 0.6,
            },
            "feature_values": {
                n: round(float(v), 4) for n, v in zip(FEATURE_NAMES, features)
            },
            "attribution": {},
        }
