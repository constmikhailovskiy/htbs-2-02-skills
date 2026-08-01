---
name: estimate-summary
description: Use when per-side estimates must be aggregated into side totals, a grand total, and the one risk buffer
---

TODO: instructions for the `estimate_summary` node (transform).

- This node is arithmetic, not judgment. The file exists as documentation of the contract;
  nothing here is attached to a prompt.
- Sum each included side's per-story breakdown into a side total, then the side totals into a
  grand total, all in `unit`.
- Apply the risk buffer exactly once, here: `ESTIMATION_RISK_BUFFER_PCT`, default 15. No upstream
  node is allowed to pad, which is what makes a single application correct.
- An excluded side reports as excluded with a zero total, not as absent. An absent side reads as
  zero work and looks identical to a side that was never run.
- TODO: decide whether both the unbuffered and buffered totals are reported.
- TODO: define the reduction from three-point estimates to one number, if the sides settle on
  three-point — PERT `(o + 4m + p) / 6` is the obvious candidate and belongs here, outside the
  model.
