"""Generate 150 labelled synthetic incidents (50 minor / 50 reportable / 50 borderline) for offline eval harness."""

from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "synthetic_incidents.json"

random.seed(42)

MINOR_TEMPLATES = [
    "Port scan detected on DMZ firewall, no lateral movement, no data access logged. Source IP blocklisted.",
    "Phishing email reported and quarantined before credential entry. No mailbox rules changed.",
    "Mis-scanned dev S3 bucket had public ACL for 2h; bucket held mock data only, no customer PII.",
]

REPORTABLE_TEMPLATES = [
    "Attacker obtained admin creds via spearphish; accessed `customer_db` table with 12k rows containing name+email. Contained within 6h.",
    "Ransomware encrypted file share; backups restored. Forensics found exfiltration of HR CSV with employee national IDs (~4k rows).",
    "API key leaked in GitHub exposed production read access to invoices (business contact PII + amounts) for 48h.",
]

BORDERLINE_TEMPLATES = [
    "Unauthorized access to analytics warehouse; unclear if sampled rows could re-identify users. 900 user events with coarse geo only.",
    "Vendor support account used outside change window to run SELECT on logs DB; unclear if queries returned PII columns.",
    "Malware on laptop of sales rep; possible local cache of customer contacts; encryption status unknown.",
]


def synth(i: int, tier: str) -> dict:
    if tier == "minor":
        text = random.choice(MINOR_TEMPLATES)
        label = {"reportable": False, "expected_authority_hours": None}
    elif tier == "reportable":
        text = random.choice(REPORTABLE_TEMPLATES)
        label = {"reportable": True, "expected_authority_hours": 72}
    else:
        text = random.choice(BORDERLINE_TEMPLATES)
        label = {"reportable": "borderline", "expected_authority_hours": None}

    return {
        "id": f"syn-{tier}-{i:03d}",
        "tier": tier,
        "jurisdiction_hint": random.choice(["EU", "EU", "US-FED"]),
        "narrative": text + f" Case synthetic id syn-{tier}-{i:03d}.",
        "labels": label,
    }


def main() -> None:
    cases: list[dict] = []
    for i in range(50):
        cases.append(synth(i, "minor"))
    for i in range(50):
        cases.append(synth(i, "reportable"))
    for i in range(50):
        cases.append(synth(i, "borderline"))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(cases, indent=2), encoding="utf-8")
    print(f"Wrote {len(cases)} cases to {OUT}")


if __name__ == "__main__":
    main()
