---
name: estimate
description: Use when a PRD or feature brief must be turned into a defensible engineering estimate — orchestrates work breakdown, per-discipline estimation, dimension factors and a challenger pass, then reports a machine-checked total
argument-hint: "[path to a PRD markdown file]"
allowed-tools:
  - Read
  - Write
  - Bash
  - Skill
---

# /estimate — orchestrator

You coordinate other skills. You do not estimate anything yourself, and you never do arithmetic.

## The one rule that makes this worth running

**Every number in the final report is computed by `scripts/aggregate.py`, never by you.**

You may write per-item three-point numbers into a JSON bundle because sub-skills produced them.
You may not add, average, multiply or "sanity check" a total. If you find yourself typing a sum,
you have broken the only property that distinguishes this from guessing — a total you wrote is
indistinguishable from a total you invented, and no one downstream can tell which it was.

Same for coverage: do not claim requirements are covered. The script decides.

## Procedure

1. **Read the PRD** at the given path. Extract the feature slug (the filename) and every `REQ-NNN`
   id in its Requirements section. Collect the ids literally — do not renumber, invent or skip.

2. **Work breakdown.** Invoke the `wbs` skill with the PRD text. It returns `items[]` (each with
   the `req` ids it implements) and `open_questions[]`. Do not add items of your own; if the
   breakdown looks wrong, run `wbs` again with the objection stated, and keep its output.

3. **Estimate per discipline.** Invoke `aspect-backend`, `aspect-mobile` and `aspect-devops`, each
   once, passing the whole item list. Each returns, per item it touches, `{o, m, p, assumption}` in
   days. Batch deliberately: one call per discipline, not one per item — per-item calls cost roughly
   the item count times as much and produce less consistent numbers, because each call sees less of
   the feature.

   A discipline that does not touch an item returns nothing for it. Zero is a claim; silence is not.

4. **Dimension factors.** Invoke `dimensions` once for the whole item list. Returns per item
   `{complexity, risk, unknowns}` — two multipliers and a number of days for what is not yet known.

5. **Assemble the bundle** at `.estimates/<feature>/bundle.json`:

   ```json
   {
     "prd": { "feature": "...", "reqs": ["REQ-001"] },
     "items": [{ "id": "W-001", "title": "...", "req": ["REQ-001"] }],
     "estimates": { "backend": [{ "item": "W-001", "o": 1, "m": 2, "p": 4, "assumption": "..." }] },
     "dimensions": [{ "item": "W-001", "complexity": 1.0, "risk": 1.0, "unknowns": 0.0 }],
     "open_questions": []
   }
   ```

6. **Aggregate.** Run `python3 scripts/aggregate.py .estimates/<feature>/bundle.json`. Read the
   checks. **Do not proceed past a `FAIL`** — fix the cause and re-run:
   - `requirement_coverage` failing means the breakdown dropped a requirement. Back to step 2.
   - `no_invented_reqs` means a sub-skill made up an id. Re-run that skill.
   - `assumptions_present` means an estimate arrived unjustified. Re-run that discipline.

7. **Challenge.** Invoke the `challenger` skill with the bundle and the aggregate output. It attacks
   the estimate: work nobody planned, items priced below what the assumption implies, dimension
   factors that do not match the described risk. It returns `challenge.deltas[]` (revised `o/m/p`
   with a `why`) and `challenge.missed_items[]`.

8. **Re-aggregate once.** Add the `challenge` block to the bundle and run the script again. The
   script now reports before, after and the delta.

   **Stop after one challenge round.** If the challenger still objects, record the objection in the
   report as an unresolved concern. An unbounded argue-loop is how this runs out of clock, and the
   second round almost never moves the number as much as the first.

9. **Report.** Show the rendered table from the script verbatim, then:
   - the **delta** — what the challenge changed, and which objection caused it. This is the most
     honest line in the report; lead with it, not with the total.
   - **open questions**, each with the requirement it blocks. A question here outranks the number.
   - the **verdict** line from the script, unedited.

## When the PRD does not support an estimate

If requirements name no concrete decision — a reward with no value, "must not be abusable" with no
fraud rules, an integration with no named provider — the correct output is the open question, not a
padded number. Say plainly which requirements cannot be priced and why.

A confident estimate over an unanswered question is the failure mode this whole skill exists to
prevent. Producing one is worse than producing nothing, because it will be believed.
