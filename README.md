# estimator

Engineering team simulator as a set of Claude Code skills. A PRD goes in; a **confirmed**
estimate comes out.

The point is the word *confirmed*. A model will emit a confident number for any PRD and none of
it is true. So each skill here is allowed to produce only per-item numbers and objections —
every total, multiplier and coverage figure is arithmetic done outside the model, and a
challenger skill attacks the result before it is reported.

## Skills

In graph order — see [ORCHESTRATION.md](ORCHESTRATION.md) for how they are wired.

| Skill | Does | Status |
|---|---|---|
| `estimate` | **`/estimate <prd>` — drives the whole graph unattended**, owns validation, computes nothing | ✅ |
| `estimate-orchestrator` | brief → which sides the feature actually needs | placeholder |
| `brief-prd-input` | raw brief/PRD text → clean brief | placeholder |
| `story-planner` | brief → implementable stories per `contracts/story.v1.md` | placeholder |
| `be-estimate` | backend effort per story | placeholder |
| `frontend-estimate` | frontend effort per story: optimistic / likely / pessimistic | ✅ |
| `qa-estimate` | QA effort per story | placeholder |
| `devops-estimate` | DevOps / infrastructure effort per story | placeholder |
| `estimate-summary` | side totals, grand total, and the one risk buffer | placeholder |

Not in the graph:

| Skill | Does | Status |
|---|---|---|
| `wbs` | PRD → work items, each tagged with the `req` ids it implements | ✅ |
| `dimensions` | complexity / risk / unknowns per item | planned |
| `challenger` | attacks the estimate: missed work, lowballed items | planned |

`wbs` and `story-planner` both decompose a source document into units of work. They predate each
other and the overlap has not been resolved; the graph currently runs `story-planner`.

Aggregation is **not** model work — it is arithmetic (PERT `(o+4m+p)/6`, multipliers, sums) and
belongs outside the model by construction. `estimate-summary` and `brief-prd-input` have skill
files, but their nodes are deterministic code and those files are never sent to a model. They
document the contract; they do not instruct one.

## Running it unattended

`/estimate` drives the graph with no human in the loop. The deterministic steps it owns:

```bash
# gate the plan — no reviewer present, so the two HITL gates are waived explicitly
python3 skills/story-planner-hitl/scripts/validate_story_plan.py \
        --autonomous scripts/fixtures/story-plan.json

# plan shape -> contracts/story.v1.md  (fe/be -> frontend/backend, criterion_id -> id)
python3 scripts/normalize_stories.py scripts/fixtures/story-plan.json > stories.json

# side totals, grand total, one risk buffer
python3 scripts/summarize.py scripts/fixtures/run.json
```

The fixtures stand in for the model steps, so all three run at **zero cost**.

**`--autonomous` waives the human gates and nothing else.** Coverage, traceability, readiness,
dependency cycles and the quality checks all still block. The waiver is reported, so a
machine-validated plan is never mistaken for an approved one:

```
WARNING: autonomous mode: human approval gates waived — machine-validated, not human-approved
WARNING: READY_FOR_ESTIMATION has unapproved assumptions: ASM-001
VALID
```

Without the flag the same plan is `INVALID` — `lacks approvals for: readiness_approval, scope_review`.
Nothing forges a `decision_log` entry; an unattended run has no reviewer, and saying otherwise would
be undetectable downstream.

### Two format hazards the scripts exist to catch

**`normalize_stories.py` is not cosmetic.** The plan schema writes `domain_impact.{fe,be,...}`; the
estimators read `contracts/story.v1.md`, which uses `{frontend,backend,...}`. Feed raw plan output to
`frontend-estimate` and every `domain_impact.frontend` lookup is falsy — the side returns
`estimable: "none"` for every story and the estimate comes back zero, cheaply and confidently.

**Mixed estimate shapes fail loudly.** `frontend-estimate` emits three-point; the other three
placeholders are specified expected-effort-only. `summarize.py` refuses to present that as one
comparable total:

```
FAIL  one_estimate_shape   mixed shapes ['expected_only', 'three_point'] — totals are not comparable
verdict: NOT CONFIRMED
```

That is the ORCHESTRATION.md open thread, surfaced instead of summed. `scripts/fixtures/run.json`
reproduces it deliberately; when all four sides agree on three-point the same input reads `CONFIRMED`.

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
ORCHESTRATION.md                 the LangGraph workflow these skills are the prompt layer of
contracts/story.v1.md            the story shape every estimator and the planner reads
skills/<name>/SKILL.md           one skill per file
```

Adding a skill is a new directory with a `SKILL.md`. Nothing else changes.

Skills that consume stories reference `contracts/story.v1.md` rather than restating the shape,
so the contract has one owner and one place to change.
