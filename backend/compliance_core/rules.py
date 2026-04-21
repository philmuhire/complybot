"""Deterministic regulatory windows (illustrative — replace with counsel-approved matrix)."""

from typing import Any

# Hours to notify supervisory authority for personal-data breaches (EU GDPR-style illustration)
GDPR_STYLE_AUTHORITY_HOURS = 72

# US sector-style examples (illustrative only)
DEADLINE_RULES: dict[tuple[str, str], dict[str, Any]] = {
    ("EU", "personal_data_breach"): {
        "authority_hours": 72,
        "user_notification_if_high_risk": True,
        "notes": "GDPR Art. 33–34 style 72h supervisory notification where feasible.",
    },
    ("EU", "unauthorized_access"): {
        "authority_hours": 72,
        "user_notification_if_high_risk": True,
        "notes": "Assess whether personal data affected; if yes, breach timelines apply.",
    },
    ("US-FED", "personal_data_breach"): {
        "authority_hours": None,
        "user_notification_if_high_risk": True,
        "notes": "Sector/state rules vary (HIPAA 60d to individuals example only—verify counsel).",
    },
}


def resolve_deadline_rule(jurisdiction: str, incident_type: str) -> dict[str, Any]:
    key = (jurisdiction.upper(), incident_type.lower())
    if key in DEADLINE_RULES:
        return DEADLINE_RULES[key]
    # Default conservative EU-style if unknown jurisdiction requested as EU
    if jurisdiction.upper() in {"EU", "EEA"}:
        return {
            "authority_hours": GDPR_STYLE_AUTHORITY_HOURS,
            "user_notification_if_high_risk": True,
            "notes": "Default EU-style illustrative window; validate with counsel.",
        }
    return {
        "authority_hours": None,
        "user_notification_if_high_risk": True,
        "notes": "No deterministic rule in demo matrix — escalate to counsel for jurisdiction-specific duty.",
    }


def risk_formula(
    *,
    severity_hint: str,
    records_exposed: int,
    personal_data: bool,
    regulatory_clauses_hit: int,
) -> dict[str, float]:
    base = {"low": 15.0, "medium": 45.0, "high": 75.0, "critical": 92.0}.get(
        severity_hint.lower(), 40.0
    )
    volume = min(25.0, (records_exposed**0.5) / 50.0 * 25.0)
    pii = 15.0 if personal_data else 0.0
    reg = min(20.0, regulatory_clauses_hit * 5.0)
    severity_score = min(100.0, base + volume * 0.4 + pii + reg)
    regulatory_exposure = min(100.0, reg + (25.0 if personal_data else 5.0))
    operational_impact = min(100.0, volume + base * 0.3)
    confidence = max(
        0.35,
        min(
            0.95,
            0.75 - 0.02 * max(0, regulatory_clauses_hit - 3) + (0.05 if personal_data else -0.05),
        ),
    )
    return {
        "severity_score": round(severity_score, 2),
        "regulatory_exposure_score": round(regulatory_exposure, 2),
        "operational_impact_score": round(operational_impact, 2),
        "confidence_level": round(confidence, 3),
    }
