#!/usr/bin/env python3
"""Story-plan JSON -> the `contracts/story.v1.md` batch the estimators read.

These two shapes do not match, and the mismatch is silent. `story-plan.schema.json`
emits `domain_impact.{fe,be,qa,devops}`; `contracts/story.v1.md` — which
`frontend-estimate` actually reads — expects `{frontend,backend,qa,devops}`. A
missing `domain_impact.frontend` key reads as falsy, so the finished estimator
would score every story `estimable: "none"` and the whole side would come back
zero. That is the worst class of bug available here: a confident, wrong, cheap zero.

Also reconciled:
    criterion_id            -> id
    source_requirement_ids  -> source_refs (resolved to their PRD locators)
    top-level assumptions   -> per-story assumptions (by affected_story_ids)
    top-level open_questions -> per-story open_questions (by affected_story_ids)

Usage:
    python3 scripts/normalize_stories.py story-plan.json > stories.json
"""

from __future__ import annotations

import json
import sys

DOMAIN = {"fe": "frontend", "be": "backend", "qa": "qa", "devops": "devops"}


def normalize(plan: dict) -> dict:
    locator = {
        r["requirement_id"]: r.get("source_ref", r["requirement_id"])
        for r in plan.get("requirements", [])
        if isinstance(r, dict) and r.get("requirement_id")
    }

    def owned(collection: str, story_id: str, field: str) -> list[str]:
        return [
            item[field]
            for item in plan.get(collection, [])
            if isinstance(item, dict) and story_id in item.get("affected_story_ids", [])
        ]

    stories = []
    for s in plan.get("stories", []):
        impact = s.get("domain_impact", {})
        stories.append(
            {
                "story_id": s["story_id"],
                "title": s.get("title", ""),
                "user_story": s.get("user_story", ""),
                "business_value": s.get("business_value", ""),
                # dict.fromkeys keeps first-seen order while de-duplicating
                "source_refs": list(
                    dict.fromkeys(locator.get(r, r) for r in s.get("source_requirement_ids", []))
                ),
                "acceptance_criteria": [
                    {
                        "id": ac.get("criterion_id"),
                        "given": ac.get("given", ""),
                        "when": ac.get("when", ""),
                        "then": ac.get("then", ""),
                    }
                    for ac in s.get("acceptance_criteria", [])
                ],
                "business_rules": s.get("business_rules", []),
                "edge_cases": s.get("edge_cases", []),
                "non_functional_requirements": s.get("non_functional_requirements", []),
                "dependencies": s.get("dependencies", []),
                "domain_impact": {v: bool(impact.get(k, False)) for k, v in DOMAIN.items()},
                "assumptions": owned("assumptions", s["story_id"], "statement"),
                "open_questions": owned("open_questions", s["story_id"], "question"),
                # The plan schema has no per-story out_of_scope. Per the contract, an
                # empty array means "nothing was written down", not "nothing exists".
                "out_of_scope": [],
                # readiness is ready|blocked since the HITL gates were dropped. Default
                # to blocked, not ready: a story whose readiness went missing must not
                # be silently priced as though someone had cleared it.
                "readiness": s.get("readiness", "blocked"),
            }
        )

    cross = [
        c["concern"]
        for c in plan.get("cross_cutting_concerns", [])
        if isinstance(c, dict) and c.get("concern")
    ]
    return {"stories": stories, "cross_cutting_concerns": cross}


def main() -> int:
    raw = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
    plan = json.loads(raw)
    out = normalize(plan)

    bad = [s["story_id"] for s in out["stories"] if not any(s["domain_impact"].values())]
    if bad:
        print(f"ERROR: stories route to no domain: {bad}", file=sys.stderr)
        return 1
    missing_ac = [s["story_id"] for s in out["stories"] if not s["acceptance_criteria"]]
    if missing_ac:
        print(f"ERROR: stories with no acceptance criteria: {missing_ac}", file=sys.stderr)
        return 1

    print(json.dumps(out, indent=2, ensure_ascii=False))
    counts = {d: sum(1 for s in out["stories"] if s["domain_impact"][d]) for d in DOMAIN.values()}
    print(f"normalized {len(out['stories'])} story/stories; routing {counts}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
