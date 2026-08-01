---
name: story-planner
description: Use when a clean brief must be decomposed into implementable stories before any side can estimate them
---

TODO: instructions for the `story_planner` node (llm).

- Decompose the brief into stories: one per implementable unit of work, not one per sentence.
- Every story carries at minimum `{id, title, acceptance_criteria}`.
- TODO: reconcile with `contracts/story.v1.md`. The estimators read the full contract —
  `domain_impact`, `readiness`, `edge_cases`, `non_functional_requirements` — while this node
  currently promises only the three-field shape. One of the two has to move.
- TODO: decide how brief content the source does not answer is recorded. Open questions, not
  silent guesses.
- TODO: decide whether every requirement in the brief must appear in at least one story, and how
  that coverage is checked.
