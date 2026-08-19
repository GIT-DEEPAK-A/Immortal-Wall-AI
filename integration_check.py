"""Quick integration test for the full ML pipeline."""
import sys
sys.path.insert(0, ".")

from backend.services.threat_engine import ThreatEngine
from simulation.attack_patterns import (
    brute_force, sql_injection, xss_attack,
    port_scan, request_flood, normal_traffic, malware_upload,
)

engine = ThreatEngine()

cases = [
    ("brute_force",   brute_force(),    "malicious"),
    ("sql_injection", sql_injection(),  "malicious"),
    ("xss",           xss_attack(),     "suspicious"),
    ("port_scan",     port_scan(),      "suspicious"),
    ("ddos",          request_flood(),  "malicious"),
    ("malware",       malware_upload(), "malicious"),
    ("normal",        normal_traffic(), "normal"),
]

failures = 0
header = "  {:<16} {:<12} {:<12} {:>7}  {:<24}  {}"
print(header.format("case", "expected", "got", "score", "attack_type", "status"))
print("  " + "-" * 82)

for name, event, expected in cases:
    r     = engine.analyze_event(event)
    got   = r["threat_level"]
    score = r["threat_score"]
    atype = r["attack_type"]
    ok    = got == expected
    if not ok:
        failures += 1
    mark  = "PASS" if ok else "FAIL"
    print(header.format(name, expected, got, round(score, 4), atype, mark))

print()
total = len(cases)
print("Result: {}/{} passed".format(total - failures, total))
sys.exit(0 if failures == 0 else 1)
