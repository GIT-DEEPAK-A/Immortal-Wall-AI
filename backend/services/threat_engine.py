# backend/services/threat_engine.py
"""
ThreatEngine — fuses rule-based and ML signals into a single verdict.

Score fusion:
  final_score = 0.40 * rule_score + 0.60 * ml_score

Thresholds:
  >= 0.70  → malicious   (hard block + alert)
  >= 0.40  → suspicious  (alert + soft block if >= 0.60)
  <  0.40  → normal

Response severity:
  malicious    → block_ip (hard) + alert
  suspicious   → alert; rate_limit if score >= 0.60
  normal       → no action
"""

from __future__ import annotations

import time
from datetime import datetime
from typing import Any, Dict

from .rule_engine import evaluate_rules, classify_attack_type
from .ml_engine import AdvancedMLEngine
from .response_engine import ResponseEngine

# Fusion weights
_W_RULE = 0.40
_W_ML   = 0.60

# Decision thresholds
_THR_MALICIOUS  = 0.70
_THR_SUSPICIOUS = 0.40
_THR_RATE_LIMIT = 0.60   # suspicious + score above this → also rate-limit


class ThreatEngine:
    def __init__(self):
        self.ml_engine       = AdvancedMLEngine()
        self.response_engine = ResponseEngine()

    # ── Core pipeline ──────────────────────────────────────────────────────

    def analyze_event(self, event: dict) -> dict:
        """
        Full analysis pipeline.  Returns a structured threat result.

        Input event keys (all optional — engine degrades gracefully):
          ip, username, event_type, status, path, method,
          user_agent, payload, payload_length, session_duration,
          request_rate, failed_logins, distinct_paths, port,
          response_code, timestamp, threat_flags, data
        """
        ts = float(event.get("timestamp") or time.time())
        ip = str(event.get("ip", "unknown"))

        # ── 1. Rule engine ─────────────────────────────────────────────────
        rule_score, rule_flags, rule_reason = evaluate_rules(event)

        # ── 2. ML engine ───────────────────────────────────────────────────
        ml_result = self.ml_engine.predict(event)
        ml_score  = float(ml_result.get("ml_score", 0.0))

        # ── 3. Score fusion ────────────────────────────────────────────────
        final_score = _W_RULE * rule_score + _W_ML * ml_score
        final_score = round(min(final_score, 1.0), 4)

        # ── 4. Decision ────────────────────────────────────────────────────
        if final_score >= _THR_MALICIOUS:
            threat_level = "malicious"
        elif final_score >= _THR_SUSPICIOUS:
            threat_level = "suspicious"
        else:
            threat_level = "normal"

        # ── 5. Attack classification ───────────────────────────────────────
        attack_type = event.get("attack_type") or classify_attack_type(event)
        if attack_type == "unknown" and ml_result.get("ml_level") != "normal":
            # Fall back to ML-suggested label if rules couldn't classify
            attack_type = ml_result.get("ml_level", "unknown")

        # ── 6. Automated response ──────────────────────────────────────────
        response_actions = []
        if threat_level == "malicious":
            block_res = self.response_engine.block_ip(ip, hard=True)
            alert_res = self.response_engine.send_alert(
                ip, threat_level,
                f"[{attack_type.upper()}] {rule_reason} | ML: {ml_result.get('ml_reason', '')}",
            )
            response_actions = [
                {"type": "block_ip",  "result": block_res},
                {"type": "alert",     "result": str(alert_res)},
            ]
        elif threat_level == "suspicious":
            alert_res = self.response_engine.send_alert(
                ip, threat_level,
                f"[{attack_type.upper()}] {rule_reason} | ML: {ml_result.get('ml_reason', '')}",
            )
            response_actions = [{"type": "alert", "result": str(alert_res)}]
            if final_score >= _THR_RATE_LIMIT:
                rl_res = self.response_engine.apply_soft_block(ip, duration=30)
                response_actions.append({"type": "rate_limit", "result": rl_res})

        # ── 7. Build result ────────────────────────────────────────────────
        result: Dict[str, Any] = {
            # Identity
            "ip_address":   ip,
            "timestamp":    datetime.utcfromtimestamp(ts).isoformat() + "Z",

            # Verdict
            "threat_level": threat_level,
            "threat_score": final_score,
            "score":        final_score,           # backward-compat alias
            "attack_type":  attack_type,

            # Sub-scores
            "rule_score":   round(rule_score, 4),
            "ml_score":     round(ml_score,   4),
            "confidence":   ml_result.get("confidence", 0.0),

            # Explanations
            "reason":       f"Rule: {rule_reason} | ML: {ml_result.get('ml_reason', 'n/a')}",
            "rule_reason":  rule_reason,
            "ml_reason":    ml_result.get("ml_reason", ""),

            # Detail
            "rule_flags":   rule_flags,
            "ml_level":     ml_result.get("ml_level", "normal"),
            "ml_result":    ml_result,
            "rule_matches": [t.strip() for t in rule_reason.split("|")] if rule_reason != "normal behavior" else [],

            # Response
            "blocked":           threat_level == "malicious",
            "response_actions":  response_actions,

            # Event metadata (passed through for storage)
            "source":        event.get("source", "agent"),
            "user_agent":    event.get("user_agent", ""),
            "request_data":  event.get("data", {}),
            "description":   f"{attack_type} — score {final_score:.2f}",
        }

        return result

    # ── Public alias used by /api/analyze-threat ───────────────────────────

    def analyze_threat(self, threat_data: dict) -> dict:
        """
        REST endpoint entry point.  Normalises the incoming payload
        then delegates to analyze_event.
        """
        # Allow callers to send ip_address instead of ip
        if "ip_address" in threat_data and "ip" not in threat_data:
            threat_data["ip"] = threat_data["ip_address"]

        result = self.analyze_event(threat_data)

        # Enrich with any extra keys the caller passed in
        result.setdefault("threat_type",  threat_data.get("threat_type", result["attack_type"]))
        result.setdefault("request_data", threat_data.get("request_data", {}))

        return result
