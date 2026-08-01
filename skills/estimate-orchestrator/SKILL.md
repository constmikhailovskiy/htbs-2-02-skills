---
name: estimate-orchestrator
description: Use when a brief must be triaged into the set of implementing sides an estimation run should actually cover
---

TODO: instructions for the `estimate_orchestrator` node (llm).

- Read the brief and decide which sides the feature genuinely needs: backend, frontend, qa, devops.
- Selecting a side that does no work inflates the estimate; omitting a side that does work hides
  it. Both are failures, and the second is the quieter one.
- Write the selected subset to `sides`; each estimate node reads it to decide whether it runs.
- TODO: define the output shape, and whether an excluded side carries a reason.
- TODO: decide what the orchestrator does when the brief is too thin to triage at all.
