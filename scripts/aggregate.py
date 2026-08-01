#!/usr/bin/env python3
"""Deterministic half of the estimate. No model may do this arithmetic.

Two stages, because they gate at different costs:

    --stage stories   validate the story decomposition ALONE. Cheap, and runs
                      before any estimate call, so a breakdown that dropped a
                      requirement is caught before four disciplines are paid to
                      estimate it.
    --stage full      (default) aggregate estimates into the summary + verdict.

Every number here is computed: PERT per story per discipline, dimension factors,
totals, and the verdict. The model contributes only per-story three-point
numbers, factors, assumptions and challenger deltas.

Usage:
    python3 scripts/aggregate.py --stage stories bundle.json
    python3 scripts/aggregate.py bundle.json
"""

from __future__ import annotations

import json
import sys

ASPECTS = ("backend", "frontend", "qa", "devops")
LABEL = {"backend": "be", "frontend": "fe", "qa": "qa", "devops": "ops"}


def pert(o: float, m: float, p: float) -> float:
    """Three-point estimate. A single number hides the spread that matters."""
    return (o + 4 * m + p) / 6


def _round(x: float) -> float:
    return round(x + 1e-9, 2)


def _check(name: str, ok: bool, detail: str) -> dict:
    return {"check": name, "ok": ok, "detail": detail}


# --------------------------------------------------------------- stage: stories


def validate_stories(bundle: dict) -> list[dict]:
    """The gate after story decomposition. Runs before anything is estimated."""
    declared = set(bundle.get("prd", {}).get("reqs", []))
    stories = bundle.get("stories", [])
    covered = {r for s in stories for r in s.get("req", [])}

    missing = sorted(declared - covered)
    orphans = sorted(covered - declared)
    ids = [s.get("id", "") for s in stories]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    untagged = [s.get("id", "?") for s in stories if not s.get("req")]
    unnamed = [s.get("id", "?") for s in stories if not str(s.get("title", "")).strip()]

    return [
        _check("stories_present", bool(stories), f"{len(stories)} story/stories"),
        _check(
            "requirement_coverage",
            bool(declared) and not missing,
            f"{len(covered & declared)}/{len(declared)} covered" + (f"; missing {missing}" if missing else ""),
        ),
        _check("no_invented_reqs", not orphans, f"unknown ids {orphans}" if orphans else "all ids exist in the PRD"),
        _check("story_ids_unique", not dupes, f"duplicated {dupes}" if dupes else "all distinct"),
        _check(
            "every_story_traced",
            not untagged,
            f"untagged {untagged}" if untagged else "every story names the reqs it implements",
        ),
        _check("every_story_named", not unnamed, f"empty title {unnamed}" if unnamed else "all titled"),
    ]


# ------------------------------------------------------------------ stage: full


def aggregate(bundle: dict) -> dict:
    stories = bundle["stories"]
    estimates = bundle.get("estimates", {})
    deltas = {(d["story"], d["aspect"]): d for d in bundle.get("challenge", {}).get("deltas", [])}

    def build(apply_challenge: bool) -> tuple[list[dict], float]:
        rows, grand = [], 0.0
        for story in stories:
            row: dict = {
                "id": story["id"],
                "title": story["title"],
                "req": story.get("req", []),
                "aspects": {},
            }
            total = 0.0
            for aspect in ASPECTS:
                e = next((x for x in estimates.get(aspect, []) if x["story"] == story["id"]), None)
                if e is None:
                    continue  # a discipline that does not touch a story says nothing
                o, m, p = float(e["o"]), float(e["m"]), float(e["p"])
                if apply_challenge and (d := deltas.get((story["id"], aspect))):
                    o, m, p = float(d.get("o", o)), float(d.get("m", m)), float(d.get("p", p))
                # Factors are per discipline per story: backend risk on a story is
                # not frontend risk on the same story.
                days = pert(o, m, p) * float(e.get("complexity", 1.0)) * float(e.get("risk", 1.0))
                days += float(e.get("unknowns", 0.0))
                row["aspects"][aspect] = _round(days)
                total += days
            row["total_days"] = _round(total)
            rows.append(row)
            grand += total
        return rows, _round(grand)

    before_rows, before_total = build(apply_challenge=False)
    after_rows, after_total = build(apply_challenge=True)

    return {
        "feature": bundle.get("prd", {}).get("feature", "unknown"),
        "before": {"stories": before_rows, "total_days": before_total},
        "after": {"stories": after_rows, "total_days": after_total},
        "delta_days": _round(after_total - before_total),
        "by_aspect": {
            a: _round(sum(r["aspects"].get(a, 0.0) for r in after_rows))
            for a in ASPECTS
            if any(a in r["aspects"] for r in after_rows)
        },
        "checks": validate_stories(bundle) + validate_estimates(bundle, after_rows),
    }


def validate_estimates(bundle: dict, rows: list[dict]) -> list[dict]:
    estimates = bundle.get("estimates", {})
    entries = [e for v in estimates.values() for e in v]

    bare = [r["id"] for r in rows if not r["aspects"]]
    unjustified = sum(1 for e in entries if not str(e.get("assumption", "")).strip())
    inverted = [
        f"{a}/{e['story']}"
        for a, v in estimates.items()
        for e in v
        if not (float(e["o"]) <= float(e["m"]) <= float(e["p"]))
    ]
    unknown_story = [
        f"{a}/{e['story']}" for a, v in estimates.items() for e in v if e["story"] not in {r["id"] for r in rows}
    ]
    open_q = bundle.get("open_questions", [])
    challenge = bundle.get("challenge")
    missed = (challenge or {}).get("missed_items", [])

    return [
        _check(
            "every_story_estimated",
            not bare,
            f"{len(rows) - len(bare)}/{len(rows)} have a discipline" + (f"; bare {bare}" if bare else ""),
        ),
        _check("estimates_map_to_stories", not unknown_story, f"unknown {unknown_story}" if unknown_story else "all match"),
        _check(
            "three_point_ordered",
            not inverted,
            f"o<=m<=p violated in {inverted}" if inverted else f"{len(entries)} estimate(s) well-formed",
        ),
        _check("assumptions_present", not unjustified, f"{len(entries) - unjustified}/{len(entries)} justified"),
        _check(
            "no_open_blockers",
            not open_q,
            f"{len(open_q)} unanswered question(s) — the number over them is a guess"
            if open_q
            else "none reported",
        ),
        _check(
            "challenger_ran",
            challenge is not None,
            f"{len(missed)} omission(s) raised" if missed else "ran, no omissions found" if challenge else "NOT RUN",
        ),
    ]


# ---------------------------------------------------------------------- output


def render(report: dict) -> str:
    cols = "".join(f"{LABEL[a]:>7}" for a in ASPECTS)
    hdr = f"{'story':<8}{'title':<40}{cols}{'total':>8}"
    out = [f"feature: {report['feature']}", "", hdr, "-" * len(hdr)]
    for r in report["after"]["stories"]:
        cells = "".join(f"{r['aspects'].get(a, '-'):>7}" for a in ASPECTS)
        out.append(f"{r['id']:<8}{r['title'][:39]:<40}{cells}{r['total_days']:>8}")
    out.append("-" * len(hdr))
    out.append(f"{'by discipline':<48}" + "".join(f"{report['by_aspect'].get(a, '-'):>7}" for a in ASPECTS))
    out += [
        "",
        f"{'before challenge':<56}{report['before']['total_days']:>8}",
        f"{'after challenge':<56}{report['after']['total_days']:>8}",
        f"{'delta':<56}{report['delta_days']:>8}",
        "",
        "checks",
    ]
    for c in report["checks"]:
        out.append(f"  {'PASS' if c['ok'] else 'FAIL'}  {c['check']:<26}{c['detail']}")
    out += ["", f"verdict: {'CONFIRMED' if all(c['ok'] for c in report['checks']) else 'NOT CONFIRMED'}"]
    return "\n".join(out)


def render_checks(checks: list[dict], title: str) -> str:
    out = [title, ""]
    for c in checks:
        out.append(f"  {'PASS' if c['ok'] else 'FAIL'}  {c['check']:<26}{c['detail']}")
    ok = all(c["ok"] for c in checks)
    out += ["", f"verdict: {'DECOMPOSITION OK — safe to estimate' if ok else 'REJECTED — do not estimate this'}"]
    return "\n".join(out)


def main() -> int:
    argv = sys.argv[1:]
    stage = "full"
    if "--stage" in argv:
        i = argv.index("--stage")
        stage = argv[i + 1]
        del argv[i : i + 2]
    raw = open(argv[0]).read() if argv else sys.stdin.read()
    bundle = json.loads(raw)

    if stage == "stories":
        checks = validate_stories(bundle)
        print(render_checks(checks, "story decomposition gate"))
        print()
        print(json.dumps({"checks": checks}, indent=2))
        return 0 if all(c["ok"] for c in checks) else 1

    report = aggregate(bundle)
    print(render(report))
    print()
    print(json.dumps(report, indent=2))
    return 0 if all(c["ok"] for c in report["checks"]) else 1


if __name__ == "__main__":
    sys.exit(main())
