---
name: estimate
description: Use when a PRD or feature brief must be turned into a defensible engineering estimate end to end, unattended — drives side triage, story planning, deterministic validation, the four side estimators and the summary, with no human approval step
argument-hint: "[path to a PRD or brief file]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Skill
---

# /estimate — autonomous orchestrator

You drive the estimation graph in `ORCHESTRATION.md` from a file path to a reported total, without
stopping for a human. You estimate nothing yourself and you never do arithmetic.

```
read PRD
  └─ estimate-orchestrator ──> sides
  └─ story-planner ──────────> story plan (story-plan.schema.json)
        └─ ✋ validate_story_plan.py --autonomous     deterministic gate, no reviewer
        └─ normalize_stories.py                      plan shape -> contracts/story.v1.md
              ┌──────────────┬──────────────┬──────────────┐
         be-estimate  frontend-estimate  qa-estimate  devops-estimate   (selected sides only)
              └──────────────┴──────────────┴──────────────┘
        └─ summarize.py ─────> side totals, grand total, one risk buffer
        └─ report
```

## Three rules

**1. Every number is computed by `scripts/summarize.py`, never by you.** You may copy per-story
numbers a side skill produced into the run file. You may not add, average, reduce three-point to one
number, or apply the buffer. A total you wrote is indistinguishable from one you invented.

**2. You gate before you spend.** The story plan is validated before any side estimates it. Four
sides estimating a plan that dropped a requirement produce four consistent, wrong numbers, and
finding out afterwards costs four calls instead of one.

**3. Autonomous is not approved.** `--autonomous` waives the two human gates because there is no
reviewer present. It waives nothing else. The validator emits a warning saying the plan is
machine-validated rather than human-approved, and **that warning must reach your final report**.
Never write a `decision_log` entry describing an approval that did not happen — a forged approval is
worse than a missing one, because it cannot be detected downstream.

## Procedure

### 1. Read the input

Read the file at the given path. It is the raw brief. Do not summarise or rewrite it before planning;
normalisation that drops a requirement silently removes work from the estimate.

Set `unit` to `hours` unless the invocation says otherwise, and never convert units afterwards.

### 2. Triage the sides — `estimate-orchestrator`

Invoke `estimate-orchestrator` with the brief. It returns the subset of `backend`, `frontend`, `qa`,
`devops` the feature genuinely needs.

Selecting a side that does no work inflates the estimate; omitting a side that does work hides it.
The second failure is the quieter one, so when the brief is ambiguous about a side, **include it** —
an included side that finds nothing reports zero and says so, which is visible; an omitted side is
indistinguishable from work nobody found.

### 3. Plan the stories — `story-planner`

Invoke `story-planner` (**not** `story-planner-hitl`, which is specified to stop for approval and
will refuse to finish unattended).

Write its output to `.estimates/<feature>/story-plan.json`, conforming to
`skills/story-planner-hitl/references/story-plan.schema.json` — that schema is the shared format, and
the validator below enforces it exactly.

### 4. ✋ Gate the plan — you own this

```bash
python3 skills/story-planner-hitl/scripts/validate_story_plan.py \
        --autonomous .estimates/<feature>/story-plan.json
```

**Do not continue while the result is `INVALID`.** Re-run `story-planner` with the errors quoted
verbatim; they name the exact field and id. Common causes:

| Error | Means |
|---|---|
| `coverage.*` must equal N | the plan's own coverage counts disagree with its requirement list |
| `requires zero uncovered requirements` | a requirement reached no story — work is missing |
| `references unknown requirements` | a story cites a `REQ` id that does not exist |
| `traceability mismatch` | a requirement links a story that does not link back |
| `has non-ready stories` | a story is `needs_clarification` or `blocked` |
| `story dependency cycle` | the plan cannot be sequenced |

Allow at most **two** re-plans. If the third attempt still fails, stop and report the validator
output as the finding. A plan that cannot be made to cover the brief is a fact about the brief; it is
not a reason to estimate anyway.

Carry every `WARNING` forward — especially unapproved assumptions and the autonomous-mode waiver.

### 5. Normalize to the story contract

```bash
python3 scripts/normalize_stories.py .estimates/<feature>/story-plan.json \
        > .estimates/<feature>/stories.json
```

This is not cosmetic. The plan schema writes `domain_impact.{fe,be,qa,devops}`; the side estimators
read `contracts/story.v1.md`, which uses `{frontend,backend,qa,devops}`. Handing raw plan output to
`frontend-estimate` makes every `domain_impact.frontend` lookup falsy, so the side returns
`estimable: "none"` for every story and the estimate comes back **zero, cheaply and confidently**.
Skipping this step is the single easiest way to produce a wrong total that looks fine.

### 6. Estimate — selected sides, one call each

Invoke `be-estimate`, `frontend-estimate`, `qa-estimate`, `devops-estimate` — **only** those in
`sides`, each **once**, passing the whole `stories.json` batch and the `unit`.

Batch deliberately: one call per side, not one per story. Per-story calls cost roughly the story
count times as much and produce less consistent numbers, because each call sees less of the feature
and cannot price reuse across stories.

Every side returns one entry per `story_id` it was given, in input order. A side that skips a story
is reporting zero work for it, which is a claim it did not make on purpose — if entries are missing,
re-run that side.

Assemble `.estimates/<feature>/run.json`:

```json
{
  "unit": "hours",
  "sides": ["backend", "frontend", "qa"],
  "stories": [{ "story_id": "US-001" }],
  "estimates": { "frontend": { "unit": "hours", "estimates": [] } }
}
```

### 7. Summarize

```bash
python3 scripts/summarize.py .estimates/<feature>/run.json
```

Three-point entries are reduced with PERT and expected-only entries taken as given, side totals
summed, then the buffer applied once from `ESTIMATION_RISK_BUFFER_PCT` (default 15). On FAIL:

| Check | Means |
|---|---|
| `all_selected_sides_reported` | a selected side never wrote its key — re-run it |
| `every_story_covered_per_side` | a side skipped stories — re-run that side |
| `one_estimate_shape` | three-point and expected-only mixed; totals are not comparable between runs |
| `no_blocked_stories` | a story is unestimable; it must be reported, not priced |

### 8. Report

Show the rendered table verbatim, then, in this order:

1. **The autonomous-mode warning**, stated plainly: this estimate was machine-validated, not
   human-approved. First, not in a footnote.
2. **Unapproved assumptions** — in an unattended run nobody approved them, and the total rests on
   every one.
3. **Open questions and blocked stories**, each with the requirement it blocks. These outrank the
   number.
4. **Unbuffered and buffered totals**, both, with the buffer percentage named. A single number hides
   whether the buffer was applied.
5. **The verdict line**, unedited. If it reads `NOT CONFIRMED`, lead with that and do not present the
   total as if it were confirmed.

## When the brief does not support an estimate

If requirements name no concrete decision — a reward with no value, "must not be abusable" with no
fraud rules, an integration with no named provider — report the open question, not a padded number.
Say which requirements cannot be priced and why, and let the rest stand.

Running unattended makes this stricter, not looser: there is no reviewer to catch a confident number
built on a guess. A confident estimate over an unanswered question is the failure this skill exists
to prevent, and unattended it is the failure nobody is watching for.
