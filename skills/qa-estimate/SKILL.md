---
name: qa-estimate
description: Use when the QA slice of each story needs estimating, QA work only
---

TODO: instructions for the `qa_estimate` node (llm).

Estimate ONLY QA work. The implementing sides already size the tests they write themselves;
re-counting those here double-counts them.

- TODO: list the sizing factors — test design from acceptance criteria, manual passes,
  automation, regression scope, test data and environments, exploratory testing, bug triage
  and retest cycles.
- TODO: draw the line against developer-written tests, which belong to the implementing side.
- Estimate in the unit carried in state (`unit`, default hours). Never convert units.
- Expected effort only. Do NOT add a risk or contingency buffer; it is applied once, later, at
  `estimate_summary`.
- A story with no QA impact scores 0 with a one-line note. Never drop a story.
