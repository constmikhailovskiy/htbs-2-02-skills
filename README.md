# estimator

Engineering team simulator as a set of Claude Code skills. A PRD goes in; a **confirmed**
estimate comes out.

The point is the word *confirmed*. A model will emit a confident number for any PRD and none of
it is true. So each skill here is allowed to produce only per-item numbers and objections —
every total, multiplier and coverage figure is arithmetic done outside the model, and a
challenger skill attacks the result before it is reported.

## Skills

| Skill | Does | Status |
|---|---|---|
| `estimate` | **orchestrator** — `/estimate <prd.md>`; drives everything below, computes nothing | ✅ |
| `wbs` | PRD → work items, each tagged with the `req` ids it implements | ✅ |
| `aspect-backend` | days per item: optimistic / likely / pessimistic | planned |
| `aspect-mobile` | same, mobile slice | planned |
| `aspect-devops` | same, infra slice | planned |
| `dimensions` | complexity / risk / unknowns per item | planned |
| `challenger` | attacks the estimate: missed work, lowballed items | planned |

Aggregation is **not** a skill — it is arithmetic (PERT `(o+4m+p)/6`, multipliers, sums) and belongs
outside the model by construction. It lives in `scripts/aggregate.py`, which also owns every
validator and the `CONFIRMED / NOT CONFIRMED` verdict.

```bash
python3 scripts/aggregate.py scripts/fixtures/workout-reminders.json
```

That fixture runs the whole deterministic half with **no model call and no cost** — the reason the
arithmetic is a script and not skill prose. Exit code is 0 only when every check passes.

## Install

```bash
# in Claude Code
/plugin marketplace add constmikhailovskiy/htbs-2-02-skills
/plugin install estimator
```

## Layout

```
.claude-plugin/plugin.json       the plugin manifest
.claude-plugin/marketplace.json  makes the repo installable as a marketplace
skills/<name>/SKILL.md           one skill per file
```

Adding a skill is a new directory with a `SKILL.md`. Nothing else changes.
