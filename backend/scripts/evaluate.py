"""Offline evaluation harness metrics over synthetic_incidents.json (requires live pipeline + API keys for full runs)."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

_BACK_END = Path(__file__).resolve().parents[1]
_CAPSTONE = _BACK_END.parent
for _path in (_CAPSTONE, _BACK_END):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


async def score_case(case: dict, pipeline_fn) -> dict:
    """Invoke pipeline if available; stub returns placeholder."""
    narrative = case["narrative"]
    try:
        result = await pipeline_fn(
            incident_id=f"eval-{case['id']}",
            raw_input=narrative,
            jurisdictions=case.get("jurisdictions"),
            jurisdiction_hint=case.get("jurisdiction_hint", "EU"),
        )
        pipe = result.get("pipeline", {})
        log = pipe.get("log_intelligence", {})
        obl = pipe.get("obligations", {})
        pred_reportable = bool(obl.get("authority_notification_required"))
        return {
            "id": case["id"],
            "pred_reportable": pred_reportable,
            "pipeline_ok": True,
            "log_intel": log,
        }
    except Exception as exc:
        return {"id": case["id"], "pipeline_ok": False, "error": str(exc)}


async def run_live(path: Path) -> None:
    from backend.compliance_agents.pipeline import run_incident_pipeline

    cases = json.loads(path.read_text(encoding="utf-8"))
    results = []
    for c in cases[:5]:
        results.append(await score_case(c, run_incident_pipeline))
    print(json.dumps(results, indent=2))


def run_heuristic_stub(path: Path) -> None:
    """Without API keys: compute coarse label agreement using keyword heuristics only."""
    cases = json.loads(path.read_text(encoding="utf-8"))
    tp = fp = tn = fn = 0
    for c in cases:
        tier = c["tier"]
        text = c["narrative"].lower()
        heuristic_reportable = any(
            k in text for k in ("pii", "personal", "national id", "customer_db", "invoice", "exfiltration")
        )
        gold = c["labels"]["reportable"]
        if gold == "borderline":
            continue
        if gold and heuristic_reportable:
            tp += 1
        elif gold and not heuristic_reportable:
            fn += 1
        elif not gold and heuristic_reportable:
            fp += 1
        else:
            tn += 1
    print(
        {
            "note": "Stub heuristic only — full metrics require run_live with OPENAI_API_KEY",
            "confusion_partial": {"tp": tp, "fp": fp, "tn": tn, "fn": fn},
        }
    )


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--dataset",
        type=Path,
        default=_BACK_END / "data" / "synthetic_incidents.json",
    )
    p.add_argument("--live", action="store_true", help="Run first 5 incidents through real pipeline")
    args = p.parse_args()
    if not args.dataset.exists():
        raise SystemExit(
            f"Missing {args.dataset} — run backend/scripts/generate_synthetic_dataset.py"
        )
    if args.live:
        asyncio.run(run_live(args.dataset))
    else:
        run_heuristic_stub(args.dataset)


if __name__ == "__main__":
    main()
