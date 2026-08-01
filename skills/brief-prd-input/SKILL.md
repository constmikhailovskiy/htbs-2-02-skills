---
name: brief-prd-input
description: Use when raw brief or PRD text must be normalized into the clean brief the estimation graph consumes
---

TODO: instructions for the `brief_prd_input` node (transform).

- This node is deterministic. The file exists as documentation of the contract; nothing here is
  attached to a prompt.
- Normalize formatting noise out of the raw input while keeping every requirement intact —
  normalization that drops a requirement silently removes work from the estimate.
- TODO: define the clean-brief shape written to `brief`.
- TODO: decide whether requirement ids are assigned here or by `story_planner`.
- TODO: decide the behaviour when the input is empty or too thin to estimate.
