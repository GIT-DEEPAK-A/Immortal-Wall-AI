#!/usr/bin/env python
"""
train.py — Standalone model training script for Immortal Wall AI.

Usage
─────
    python train.py                      # default 8 000 samples
    python train.py --samples 20000      # larger dataset
    python train.py --samples 5000 --seed 7

What it does
────────────
  1.  Generates a stratified synthetic dataset via attack_patterns.py
  2.  Trains a calibrated ensemble (RF + GBT + LR) with a StandardScaler
  3.  Runs 5-fold stratified cross-validation and prints the report
  4.  Saves  models/advanced_model.pkl  (pipeline)
             models/model_meta.json     (metrics + feature importances)
  5.  Runs a quick smoke-test on 6 hand-crafted events and prints results

Expected output (approximate)
─────────────────────────────
  [ML Engine] Training on 8000 samples, 18 features …
  [ML Engine] Running 5-fold stratified CV …
                precision    recall  f1-score
     normal       0.96        0.97    0.97
  suspicious      0.89        0.88    0.88
   malicious      0.95        0.94    0.95
  macro avg       0.93        0.93    0.93
  weighted avg    0.94        0.94    0.94
  [ML Engine] Model saved → …
  ── Smoke test ──
  brute_force       → malicious   score=0.87  conf=0.91
  sql_injection     → malicious   score=0.91  conf=0.94
  xss               → suspicious  score=0.53  conf=0.72
  port_scan         → suspicious  score=0.49  conf=0.68
  ddos              → malicious   score=0.82  conf=0.88
  normal            → normal      score=0.04  conf=0.97
"""

import argparse
import json
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description="Train the Immortal Wall AI ML model")
    p.add_argument("--samples", type=int, default=8_000,
                   help="Number of training samples (default 8000)")
    p.add_argument("--seed",    type=int, default=42,
                   help="Random seed for reproducibility (default 42)")
    p.add_argument("--cv",      type=int, default=5,
                   help="Cross-validation folds (default 5)")
    p.add_argument("--no-smoke", action="store_true",
                   help="Skip the smoke test after training")
    return p.parse_args()


def smoke_test(engine) -> None:
    from simulation.attack_patterns import (
        brute_force, sql_injection, xss_attack,
        port_scan, request_flood, normal_traffic,
    )

    cases = [
        ("brute_force",     brute_force()),
        ("sql_injection",   sql_injection()),
        ("xss",             xss_attack()),
        ("port_scan",       port_scan()),
        ("ddos",            request_flood()),
        ("normal",          normal_traffic()),
    ]

    print("\n-- Smoke test --------------------------------------------------------------")
    print(f"  {'case':<22} {'predicted':<12} {'score':>7}  {'conf':>7}  top attribution")
    print("  " + "-" * 70)

    all_pass = True
    expected_levels = {
        "brute_force":   "malicious",
        "sql_injection": "malicious",
        "xss":           "suspicious",
        "port_scan":     "suspicious",
        "ddos":          "malicious",
        "normal":        "normal",
    }

    for name, event in cases:
        r = engine.predict(event)
        top_attr = ""
        if r.get("attribution"):
            top = max(r["attribution"].items(), key=lambda x: abs(x[1]))
            top_attr = f"{top[0]}={top[1]:+.3f}"

        pred  = r["ml_level"]
        score = r["ml_score"]
        conf  = r["confidence"]
        ok    = "OK" if pred == expected_levels.get(name) else "FAIL"
        if ok == "FAIL":
            all_pass = False

        print(f"  {ok:<4} {name:<21} {pred:<12} {score:>7.4f}  {conf:>7.4f}  {top_attr}")

    print()
    if all_pass:
        print("  All smoke tests PASSED")
    else:
        print("  WARNING: some smoke tests failed -- check training data balance")


def main():
    args = parse_args()

    print(textwrap.dedent(f"""
    ======================================================
         Immortal Wall AI -- Model Training
      samples={args.samples:<6}  seed={args.seed:<6}  cv={args.cv}-fold
    ======================================================
    """))

    # ── Imports (after sys.path set) ──────────────────────────────────────
    from backend.services.ml_engine import (
        generate_training_data,
        build_and_train,
        save_artifacts,
        AdvancedMLEngine,
        FEATURE_NAMES,
        N_FEATURES,
    )

    # ── 1. Generate data ──────────────────────────────────────────────────
    print(f"[Train] Generating {args.samples:,} samples ...")
    X, y = generate_training_data(n_samples=args.samples, random_state=args.seed)

    from collections import Counter
    dist = Counter(y.tolist())
    label_map = {0: "normal", 1: "suspicious", 2: "malicious"}
    print("[Train] Class distribution:")
    for cls, name in label_map.items():
        print(f"         {name:<12} {dist[cls]:>5}  ({dist[cls]/len(y)*100:.1f}%)")

    # ── 2. Train ──────────────────────────────────────────────────────────
    pipeline, scaler, meta = build_and_train(X, y, random_state=args.seed, cv_folds=args.cv)

    # ── 3. Save ───────────────────────────────────────────────────────────
    save_artifacts(pipeline, meta)

    # ── 4. Print metrics summary ──────────────────────────────────────────
    print(f"\n[Train] CV results (macro F1 = {meta['f1_macro']:.4f}, weighted F1 = {meta['f1_weighted']:.4f})")
    print("\n[Train] Top 10 feature importances:")
    importances = meta.get("feature_importances", {})
    ranked = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (feat, imp) in enumerate(ranked, 1):
        bar = "#" * int(imp * 400)
        print(f"  {i:>2}. {feat:<28} {imp:.5f}  {bar}")

    # ── 5. Smoke test ─────────────────────────────────────────────────────
    if not args.no_smoke:
        engine = AdvancedMLEngine()
        smoke_test(engine)

    # ── 6. Print usage hint ───────────────────────────────────────────────
    print(textwrap.dedent("""
    ---------------------------------------------------------
    Model saved.  Start the backend to use it:

        uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

    Send a test event:

        curl -X POST http://localhost:8000/api/analyze-threat
          -H "Content-Type: application/json"
          -H "Authorization: Bearer <token>"
          -d '{"ip":"195.154.92.47","event_type":"login","status":"failed",
               "failed_logins":15,"request_rate":25,"user_agent":"sqlmap/1.7"}'
    ---------------------------------------------------------
    """))


if __name__ == "__main__":
    main()
