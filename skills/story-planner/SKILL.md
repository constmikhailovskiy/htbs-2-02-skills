---
name: story-planner
description: Use when a PRD or brief must be decomposed into user stories before it can be estimated by engineering disciplines
---

# story-planner

Decompose the PRD into stories. **Estimate nothing** — four discipline skills do that afterwards, and
a story that arrives pre-estimated biases every one of them.

## Rules

- One story per slice of user-visible value, not one per sentence of the PRD. "Reminder schedule API"
  and "reminder picker screen" belong together if the user gets nothing until both exist.
- Every story lists the `req` ids it implements. A story implementing no requirement is not work
  anyone asked for — find its requirement or drop it.
- Every requirement in the PRD must appear in at least one story. Omission is the most common way an
  estimate lies, and it is machine-checked the moment you finish, so a gap here halts the flow.
- Never invent a `REQ` id. If work is needed that no requirement covers, raise it in
  `open_questions` — a story tagged with a made-up id passes coverage and hides the problem.
- Prefer 5–12 stories. Fewer, and the disciplines estimate blind; more, and the practice spends its
  time reading a spreadsheet.

## Underspecified requirements

If a requirement names no concrete decision — a reward with no value, "must not be abusable" with no
fraud rules, an integration with no named provider — do **not** invent a story for it. Record it in
`open_questions`, naming the requirement it blocks.

A story built on a guess is worse than a missing story: it will be estimated, and the number will be
believed.

## Output

Return only JSON:

```json
{
  "stories": [
    { "id": "S-001", "title": "short imperative phrase", "req": ["REQ-001", "REQ-004"] }
  ],
  "open_questions": [
    { "req": "REQ-003", "question": "what the PRD does not decide" }
  ]
}
```
