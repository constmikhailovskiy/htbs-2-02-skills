---
name: devops-estimate
description: Use when the DevOps and infrastructure slice of each story needs estimating, infrastructure work only
---

TODO: instructions for the `devops_estimate` node (llm).

Estimate ONLY DevOps and infrastructure work. Application code belongs to the backend and
frontend nodes; counting it here double-counts the feature.

- TODO: list the sizing factors — pipeline and CI changes, infrastructure as code, new
  environments, secrets and configuration, observability and alerting, scaling and capacity,
  rollout and rollback.
- TODO: decide how shared infrastructure is handled — sized once in the story that first needs
  it, not re-sized per story that uses it.
- Estimate in the unit carried in state (`unit`, default hours). Never convert units.
- Expected effort only. Do NOT add a risk or contingency buffer; it is applied once, later, at
  `estimate_summary`.
- A story with no infrastructure impact scores 0 with a one-line note. Never drop a story.
