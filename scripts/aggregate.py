#!/usr/bin/env python3
"""Deterministic half of the estimate. No model may do this arithmetic.

Reads one JSON bundle on stdin or as argv[1], writes the report to stdout as JSON.
Every number here is computed: PERT per item per aspect, dimension multipliers,
totals, and the coverage verdict. The model's only contribution to the input is
per-item three-point numbers, dimension factors, and challenger deltas.

Usage:
    python3 scripts/aggregate.py bundle.json
    cat bundle.json | python3 scripts/aggregate.py
"""

from __future__ import annotations

import json
import sys

ASPECTS = ("backend", "mobile", "devops")


def pert(o: float, m: float, p: float) -> float:
    """Three-point estimate. A single number hides the spread that matters."""
    return (o + 4 * m + p) / 6


def _round(x: float) -> float:
    return round(x + 1e-9, 2)


def aggregate(bundle: dict) -> dict:
    items = bundle["items"]
    estimates = bundle.get("estimates", {})
    dims = {d["item"]: d for d in bundle.get("dimensions", [])}
    deltas = {(d["item"], d["aspect"]): d for d in bundle.get("challenge", {}).get("deltas", [])}

    def build(apply_challenge: bool) -> tuple[list[dict], float]:
        rows, grand = [], 0.0
        for item in items:
            row: dict = {"id": item["id"], "title": item["title"], "req": item.get("req", []), "aspects": {}}
            base = 0.0
            for aspect in ASPECTS:
                entry = next((e for e in estimates.get(aspect, []) if e["item"] == item["id"]), None)
                if entry is None:
                    continue
                o, m, p = float(entry["o"]), float(entry["m"]), float(entry["p"])
                if apply_challenge:
                    delta = deltas.get((item["id"], aspect))
                    if delta:
                        o, m, p = (float(delta.get(k, v)) for k, v in (("o", o), ("m", m), ("p", p)))
                days = pert(o, m, p)
                row["aspects"][aspect] = _round(days)
                base += days
            d = dims.get(item["id"], {})
            complexity, risk = float(d.get("complexity", 1.0)), float(d.get("risk", 1.0))
            unknowns = float(d.get("unknowns", 0.0))
            total = base * complexity * risk + unknowns
            row |= {
                "base_days": _round(base),
                "complexity": complexity,
                "risk": risk,
                "unknowns_days": unknowns,
                "total_days": _round(total),
            }
            rows.append(row)
            grand += total
        return rows, _round(grand)

    before_rows, before_total = build(apply_challenge=False)
    after_rows, after_total = build(apply_challenge=True)

    return {
        "feature": bundle.get("prd", {}).get("feature", "unknown"),
        "before": {"items": before_rows, "total_days": before_total},
        "after": {"items": after_rows, "total_days": after_total},
        "delta_days": _round(after_total - before_total),
        "checks": validate(bundle, before_rows),
    }


def validate(bundle: dict, rows: list[dict]) -> list[dict]:
    """Machine-checked confirmation. A failing check invalidates the estimate."""
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail})

    declared = set(bundle.get("prd", {}).get("reqs", []))
    covered = {r for row in rows for r in row["req"]}
    missing = sorted(declared - covered)
    add(
        "requirement_coverage",
        not missing and bool(declared),
        f"{len(covered & declared)}/{len(declared)} covered" + (f"; missing {missing}" if missing else ""),
    )

    orphans = sorted(covered - declared)
    add("no_invented_reqs", not orphans, f"unknown ids {orphans}" if orphans else "all ids exist in the PRD")

    unestimated = [row["id"] for row in rows if not row["aspects"]]
    add(
        "every_item_estimated",
        not unestimated,
        f"{len(rows) - len(unestimated)}/{len(rows)} items have at least one aspect"
        + (f"; bare {unestimated}" if unestimated else ""),
    )

    total_entries = sum(len(v) for v in bundle.get("estimates", {}).values())
    with_assumption = sum(
        1 for v in bundle.get("estimates", {}).values() for e in v if str(e.get("assumption", "")).strip()
    )
    add("assumptions_present", total_entries == with_assumption, f"{with_assumption}/{total_entries} estimates justified")

    open_q = bundle.get("open_questions", [])
    add(
        "blockers_surfaced",
        True,
        f"{len(open_q)} open question(s) — an estimate over an unanswered question is a guess"
        if open_q
        else "none reported",
    )

    missed = bundle.get("challenge", {}).get("missed_items", [])
    add("challenger_ran", "challenge" in bundle, f"{len(missed)} missed item(s) raised" if missed else "no omissions found")

    return checks


def render(report: dict) -> str:
    out = [f"feature: {report['feature']}", ""]
    hdr = f"{'item':<8}{'title':<42}{'be':>6}{'mob':>6}{'ops':>6}{'base':>7}{'x':>7}{'total':>8}"
    out += [hdr, "-" * len(hdr)]
    for row in report["after"]["items"]:
        a = row["aspects"]
        mult = f"{row['complexity'] * row['risk']:.2f}"
        out.append(
            f"{row['id']:<8}{row['title'][:41]:<42}"
            f"{a.get('backend', 0):>6}{a.get('mobile', 0):>6}{a.get('devops', 0):>6}"
            f"{row['base_days']:>7}{mult:>7}{row['total_days']:>8}"
        )
    out += [
        "-" * len(hdr),
        f"{'before challenge':<70}{report['before']['total_days']:>8}",
        f"{'after challenge':<70}{report['after']['total_days']:>8}",
        f"{'delta':<70}{report['delta_days']:>8}",
        "",
        "checks",
    ]
    for c in report["checks"]:
        out.append(f"  {'PASS' if c['ok'] else 'FAIL'}  {c['check']:<24}{c['detail']}")
    verdict = "CONFIRMED" if all(c["ok"] for c in report["checks"]) else "NOT CONFIRMED"
    out += ["", f"verdict: {verdict}"]
    return "\n".join(out)


def main() -> int:
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    report = aggregate(json.loads(raw))
    print(render(report))
    print()
    print(json.dumps(report, indent=2))
    return 0 if all(c["ok"] for c in report["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
