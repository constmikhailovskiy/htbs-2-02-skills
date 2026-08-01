---
name: be-estimate
description: Use when the backend slice of each story needs estimating, backend work only
---

TODO: instructions for the `be_estimate` node (llm).

Estimate ONLY backend work. Frontend, QA, and DevOps have their own nodes; counting their effort
here double-counts the feature.

- TODO: list the sizing factors — data model and migrations, endpoints and contracts, business
  logic, third-party integrations, authn/authz, background jobs, backend tests.
- Estimate in the unit carried in state (`unit`, default hours). Never convert units.
- Expected effort only. Do NOT add a risk or contingency buffer; it is applied once, later, at
  `estimate_summary`. Padding here double-counts it.
- A story with no backend impact scores 0 with a one-line note. Never drop a story — a missing
  story reads as zero work downstream.
- TODO: settle the output shape against `frontend-estimate`, which emits three-point
  optimistic/likely/pessimistic. All sides must agree before `estimate_summary` can sum them.
