---
name: estimate
description: Use when a PRD or feature brief must be turned into a defensible engineering estimate — orchestrates story decomposition, four discipline estimates and an adversarial challenge, gating on machine-checked validation at each step
argument-hint: "[path to a PRD markdown file]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Skill
---

# /estimate — orchestrator

You coordinate other skills and you own validation. You estimate nothing yourself, and you never do
arithmetic.

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

## Two rules that make this worth running

**1. Every number in the report is computed by `scripts/aggregate.py`, never by you.** You may copy
per-story numbers into a JSON bundle because a discipline skill produced them. You may not add,
average, multiply or "sanity check" a total. A total you wrote is indistinguishable from a total you
invented, and nobody downstream can tell which it was.

**2. You gate before you spend.** The decomposition is validated *before* any discipline estimates
it. Four skills estimating a breakdown that dropped a requirement produces four consistent, wrong
numbers — and the cost of finding out later is four calls, not one.

## Procedure

### 1. Read the PRD

Read the file at the given path. Take the feature slug from the filename and collect every `REQ-NNN`
id in its Requirements section, literally. Do not renumber, invent or skip.

### 2. Decompose — `story-planner`

Invoke `story-planner` with the PRD text. It returns `stories[]` (each with the `req` ids it
implements) and `open_questions[]`.

Write `.estimates/<feature>/bundle.json`:

```json
{
  "prd": { "feature": "workout-reminders", "reqs": ["REQ-001"] },
  "stories": [{ "id": "S-001", "title": "...", "req": ["REQ-001"] }],
  "open_questions": []
}
```

### 3. ✋ Gate the decomposition — you own this

```bash
python3 scripts/aggregate.py --stage stories .estimates/<feature>/bundle.json
```

**Do not continue while any check reads FAIL.** Fix the cause and re-run the gate:

| Check | Means | Do |
|---|---|---|
| `requirement_coverage` | the breakdown dropped a requirement | re-run `story-planner`, naming the missing ids |
| `no_invented_reqs` | a story cites an id the PRD does not contain | re-run `story-planner`, naming the bad ids |
| `story_ids_unique` | duplicate story ids | re-run `story-planner` |
| `every_story_traced` | a story implements no requirement | re-run `story-planner`, naming that story |

Re-running one cheap skill beats discovering this after four expensive ones. If two attempts do not
pass, stop and report the gate output — a decomposition that cannot be made to cover the PRD is a
finding about the PRD, not a reason to estimate anyway.

### 4. Estimate — four disciplines, one call each

Invoke `estimate-backend`, `estimate-frontend`, `estimate-qa` and `estimate-devops`, each **once**,
passing the whole story list.

Batch deliberately: one call per discipline, not one per story. Per-story calls cost roughly the story
count times as much and produce *less* consistent numbers, because each call sees less of the feature.

Each returns per story it touches `{o, m, p, complexity, risk, unknowns, assumption}`. A discipline
that does not touch a story returns nothing for it — silence means "not mine", `0` would be a claim.

Merge into the bundle under `estimates`, keyed by `backend` / `frontend` / `qa` / `devops`.

### 5. Aggregate

```bash
python3 scripts/aggregate.py .estimates/<feature>/bundle.json
```

Read the checks. On FAIL, re-run only the discipline responsible:

| Check | Means |
|---|---|
| `every_story_estimated` | a story no discipline claimed — ask whether it is real work |
| `three_point_ordered` | `o <= m <= p` violated; that discipline's numbers are malformed |
| `assumptions_present` | an estimate arrived unjustified — the challenger has nothing to attack |
| `no_open_blockers` | `story-planner` raised unanswered questions; see step 8 |

### 6. Challenge — `challenger`

Invoke `challenger` with the stories, all estimates with their assumptions, and the aggregate output.
It returns `deltas[]` (revised `o/m/p` with a `why`), `missed_items[]` and `unresolved[]`.

### 7. Re-aggregate once

Add the `challenge` block to the bundle and run the script again. It now reports before, after and
the delta.

**Stop after one challenge round.** If the challenger still objects, report the objection as an
unresolved concern. An unbounded argue-loop is how this runs out of clock, and the second round almost
never moves the number as much as the first.

### 8. Report

Show the script's rendered table verbatim, then, in this order:

1. **The delta** — what the challenge changed and which objection caused it. Lead with this, not with
   the total. It is the most honest line in the report: it shows what the first pass missed.
2. **`missed_items`** — work the challenger found that nobody priced. Not folded into the number;
   listed, so someone decides.
3. **Open questions**, each with the requirement it blocks. These outrank the number.
4. **The verdict line**, unedited. If it reads `NOT CONFIRMED`, say so first and do not present the
   total as if it were confirmed.

## When the PRD does not support an estimate

If requirements name no concrete decision — a reward with no value, "must not be abusable" with no
fraud rules, an integration with no named provider — the correct output is the open question, not a
padded number. State plainly which requirements cannot be priced and why, and let the rest of the
estimate stand on its own.

A confident estimate over an unanswered question is the failure mode this skill exists to prevent.
Producing one is worse than producing nothing, because it will be believed.
