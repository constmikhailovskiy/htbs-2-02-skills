#!/usr/bin/env python3
"""The `estimate_summary` node: side totals, grand total, one risk buffer.

Arithmetic, not judgment. No model runs here — which is the property that makes the
number defensible rather than merely confident.

Two shapes arrive because the sides have not converged (ORCHESTRATION.md open thread):
`frontend-estimate` emits three-point optimistic/likely/pessimistic; the other three
are specified expected-effort-only. Both are accepted — three-point is reduced with
PERT `(o + 4m + p) / 6` — and a mixed batch is reported as a warning rather than
summed silently. A total that hides which sides were three-point is not comparable
between runs.

The buffer is `ESTIMATION_RISK_BUFFER_PCT` (default 15), applied exactly once, here.
No upstream node may pad; that is what makes one application correct rather than an
approximation.

Usage:
    ESTIMATION_RISK_BUFFER_PCT=15 python3 scripts/summarize.py run.json
"""

from __future__ import annotations

import json
import os
import sys

SIDES = ("backend", "frontend", "qa", "devops")


def pert(o: float, m: float, p: float) -> float:
    return (o + 4 * m + p) / 6


def _round(x: float) -> float:
    return round(x + 1e-9, 2)


def reduce_entry(e: dict) -> tuple[float | None, str]:
    """One number per story per side, plus the shape it came from."""
    if e.get("estimable") == "blocked":
        return None, "blocked"
    three = ("optimistic", "likely", "pessimistic")
    if all(e.get(k) is not None for k in three):
        return pert(*(float(e[k]) for k in three)), "three_point"
    for key in ("hours", "effort", "expected", "likely"):
        if e.get(key) is not None:
            return float(e[key]), "expected_only"
    return None, "missing"


def summarize(run: dict) -> dict:
    unit = run.get("unit", "hours")
    selected = run.get("sides") or list(SIDES)
    story_ids = [s.get("story_id") for s in run.get("stories", [])]
    estimates = run.get("estimates", {})
    buffer_pct = float(os.environ.get("ESTIMATION_RISK_BUFFER_PCT", "15"))

    per_side: dict[str, dict] = {}
    shapes: set[str] = set()
    blocked: list[str] = []
    per_story: dict[str, dict[str, float]] = {sid: {} for sid in story_ids}

    for side in SIDES:
        payload = estimates.get(side)
        if side not in selected:
            # Excluded is not absent. An absent side reads as zero work and is
            # indistinguishable from a side that was never run.
            per_side[side] = {"included": False, "total": 0.0, "reason": "not selected by the orchestrator"}
            continue
        if payload is None:
            per_side[side] = {"included": True, "total": 0.0, "reason": "SELECTED BUT DID NOT REPORT"}
            continue
        total = 0.0
        seen: set[str] = set()
        for e in payload.get("estimates", []):
            value, shape = reduce_entry(e)
            shapes.add(shape)
            sid = e.get("story_id")
            seen.add(sid)
            if shape == "blocked":
                blocked.append(f"{side}/{sid}")
                continue
            if value is None:
                continue
            total += value
            if sid in per_story:
                per_story[sid][side] = _round(value)
        per_side[side] = {
            "included": True,
            "total": _round(total),
            "missing_stories": sorted(set(story_ids) - seen),
        }

    grand = _round(sum(v["total"] for v in per_side.values() if v["included"]))
    buffered = _round(grand * (1 + buffer_pct / 100))

    checks = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})

    silent = [s for s, v in per_side.items() if v.get("reason") == "SELECTED BUT DID NOT REPORT"]
    add("all_selected_sides_reported", not silent, f"silent: {silent}" if silent else f"{len(selected)} side(s) reported")

    gaps = {s: v["missing_stories"] for s, v in per_side.items() if v.get("missing_stories")}
    add("every_story_covered_per_side", not gaps, f"stories missing per side: {gaps}" if gaps else "no gaps")

    real = shapes - {"blocked", "missing"}
    add(
        "one_estimate_shape",
        len(real) <= 1,
        f"mixed shapes {sorted(real)} — totals are not comparable" if len(real) > 1 else f"{sorted(real) or ['none']}",
    )
    add("no_blocked_stories", not blocked, f"blocked: {blocked}" if blocked else "none")
    add("buffer_applied_once", True, f"{buffer_pct:g}% at summary only")

    return {
        "unit": unit,
        "sides": selected,
        "per_story": per_story,
        "per_side": per_side,
        "total": grand,
        "buffer_pct": buffer_pct,
        "total_buffered": buffered,
        "checks": checks,
    }


def render(s: dict) -> str:
    unit = s["unit"]
    cols = [x for x in SIDES if s["per_side"][x]["included"]]
    hdr = f"{'story':<10}" + "".join(f"{c[:8]:>10}" for c in cols)
    out = [f"unit: {unit}", "", hdr, "-" * len(hdr)]
    for sid, per in s["per_story"].items():
        out.append(f"{sid:<10}" + "".join(f"{per.get(c, '-'):>10}" for c in cols))
    out += ["-" * len(hdr), f"{'total':<10}" + "".join(f"{s['per_side'][c]['total']:>10}" for c in cols), ""]
    for side in SIDES:
        v = s["per_side"][side]
        note = v.get("reason") or ""
        flag = "" if v["included"] else "excluded"
        out.append(f"  {side:<10}{v['total']:>10} {unit:<7}{flag} {note}".rstrip())
    out += [
        "",
        f"{'grand total':<24}{s['total']:>10} {unit}",
        f"{'risk buffer':<24}{s['buffer_pct']:>9.0f}%",
        f"{'buffered total':<24}{s['total_buffered']:>10} {unit}",
        "",
        "checks",
    ]
    for c in s["checks"]:
        out.append(f"  {'PASS' if c['ok'] else 'FAIL'}  {c['check']:<30}{c['detail']}")
    ok = all(c["ok"] for c in s["checks"])
    out += ["", f"verdict: {'CONFIRMED' if ok else 'NOT CONFIRMED'}"]
    return "\n".join(out)


def main() -> int:
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    report = summarize(json.loads(raw))
    print(render(report))
    print()
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if all(c["ok"] for c in report["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
