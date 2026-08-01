# estimator

Engineering team simulator as a set of Claude Code skills. A PRD goes in; a **confirmed**
estimate comes out.

The point is the word *confirmed*. A model will emit a confident number for any PRD and none of
it is true. So each skill here is allowed to produce only per-item numbers and objections —
every total, multiplier and coverage figure is arithmetic done outside the model, and a
challenger skill attacks the result before it is reported.

## Skills

```
Start
  └─ read PRD ──> story-planner ──> ✋ GATE: --stage stories
                                        │ FAIL -> back to story-planner
                                        │ PASS
                    ┌───────────────────┴───────────────────┐
              estimate-backend  estimate-frontend  estimate-qa  estimate-devops
                    └───────────────────┬───────────────────┘
                                  aggregate ──> challenger ──> aggregate once more
                                                                    │
                                                              report + verdict
```

| Skill | Does | Status |
|---|---|---|
| `estimate` | **orchestrator** — `/estimate <prd.md>`; drives everything below, computes nothing | ✅ |
| `story-planner` | PRD → stories, each tagged with the `req` ids it implements | ✅ |
| `estimate-backend` | `o/m/p` + complexity/risk/unknowns per story | planned |
| `estimate-frontend` | same, client slice | planned |
| `estimate-qa` | same, testing slice | planned |
| `estimate-devops` | same, platform slice | planned |
| `challenger` | attacks the estimate: missed work, lowballed stories, assumptions that fail | planned |

Aggregation is **not** a skill — it is arithmetic (PERT `(o+4m+p)/6`, factors, sums) and belongs
outside the model by construction. It lives in `scripts/aggregate.py`, which also owns every
validator and the verdict.

## The gate is the point

The decomposition is validated **before** any discipline estimates it:

```bash
python3 scripts/aggregate.py --stage stories scripts/fixtures/workout-reminders.json
python3 scripts/aggregate.py               scripts/fixtures/workout-reminders.json
```

Four skills estimating a breakdown that dropped a requirement produce four consistent, wrong numbers.
Gating first costs one cheap re-run instead of four expensive ones.

The fixture stands in for the discipline skills, so both stages run with **no model call and no cost**.
Exit code is 0 only when every check passes — and the checks do fail when they should:

```
FAIL  requirement_coverage   6/7 covered; missing ['REQ-005']
FAIL  no_invented_reqs       unknown ids ['REQ-999']
FAIL  story_ids_unique       duplicated ['S-001']
verdict: REJECTED — do not estimate this
```

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
