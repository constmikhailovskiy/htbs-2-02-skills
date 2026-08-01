# Orchestration

The skills in this repo are the prompt layer of a LangGraph **estimation** workflow. A feature
brief goes in; per-side effort in a configurable `unit` comes out, with one risk buffer applied
at the end.

## Graph

```
__start__
   -> estimate_orchestrator          picks which sides the feature needs
   -> brief_prd_input                normalizes raw text into a clean brief
   -> story_planner                  brief -> stories
   -> [ be_estimate | frontend_estimate | qa_estimate | devops_estimate ]   (parallel)
   -> estimate_summary               side totals, grand total, risk buffer
   -> __end__
```

## Nodes

| Node | Kind | Skill file | Does |
|---|---|---|---|
| `estimate_orchestrator` | llm | `skills/estimate-orchestrator/SKILL.md` | Reads the brief; selects which sides the feature actually needs. |
| `brief_prd_input` | transform | `skills/brief-prd-input/SKILL.md` | Normalizes the raw brief/PRD text into a clean brief. |
| `story_planner` | llm | `skills/story-planner/SKILL.md` | Decomposes the brief into implementable stories. |
| `be_estimate` | llm | `skills/be-estimate/SKILL.md` | Backend effort per story. |
| `frontend_estimate` | llm | `skills/frontend-estimate/SKILL.md` | Frontend effort per story. |
| `qa_estimate` | llm | `skills/qa-estimate/SKILL.md` | QA effort per story. |
| `devops_estimate` | llm | `skills/devops-estimate/SKILL.md` | DevOps/infrastructure effort per story. |
| `estimate_summary` | transform | `skills/estimate-summary/SKILL.md` | Side totals, grand total, one risk buffer. |

LLM nodes append their skill file to the node prompt. The two **transform nodes**
(`brief_prd_input`, `estimate_summary`) are deterministic code — their skill files exist as
documentation of the contract and are never sent to a model. That split is deliberate: every
total and multiplier is arithmetic outside the model by construction.

Skills live at `skills/<name>/SKILL.md` rather than as flat files, so the same directory is
installable as a Claude Code plugin. A LangGraph loader globs `skills/*/SKILL.md` and keys on the
frontmatter `name`.

## Fan-out and fan-in

`story_planner` fans out to the four estimate nodes. LangGraph schedules all four in the same
superstep, runs them concurrently, and waits for every one to finish before `estimate_summary`
starts — the fan-in is a barrier, not a race.

Each estimate node checks `sides` first. A node whose side the orchestrator did not select
writes `{included: false, hours: 0, breakdown: []}` for its own key and does no model work. It
still writes: a side that returns nothing is indistinguishable from a side that was never run,
and both read as zero.

## State

| Field | Type | Reducer | Notes |
|---|---|---|---|
| `input` | str | last write wins | The raw brief or PRD text. |
| `unit` | str | last write wins | Default `"hours"`. Never converted mid-graph. |
| `sides` | list[str] | last write wins | Subset of `backend`, `frontend`, `qa`, `devops`, chosen by the orchestrator. |
| `brief` | dict | last write wins | Clean brief from `brief_prd_input`. |
| `stories` | list[dict] | last write wins | Stories from `story_planner`; see `contracts/story.v1.md`. |
| `estimates` | dict | **shallow merge** | `side -> {hours, included, breakdown}`. |
| `summary` | dict | last write wins | Side totals, grand total, buffered total. |
| `log` | list[str] | **append** | Per-node trace; every node appends, nothing overwrites. |

Two reducers matter:

- **`estimates` shallow-merges.** The four estimate nodes run concurrently and each writes one
  key — `be_estimate` writes `estimates["backend"]`, and so on. Without a merge reducer, four
  writes to the same channel in one superstep raise `InvalidUpdateError`; with it, each side
  lands independently and no node can clobber another's result.
- **`log` appends.** Concurrent nodes each contribute their own lines instead of the last writer
  winning.

## Config

- **`unit`** — overridable via graph input, default `"hours"`. Nodes estimate in whatever unit
  state carries and never convert; a mixed-unit sum is the failure this rule exists to prevent.
- **`ESTIMATION_RISK_BUFFER_PCT`** — env var, default `15`. Read and applied **once**, at
  `estimate_summary`. No estimate node adds a buffer of its own; that is why applying it a single
  time at the end is correct rather than an approximation.

## Open threads

The placeholder skills carry their own TODOs. Two cut across the graph:

- `frontend-estimate` emits three-point optimistic/likely/pessimistic; the other three
  placeholders are specified as expected-effort-only. `estimate_summary` cannot sum both shapes —
  the sides need one agreed output shape.
- `story_planner` promises `{id, title, acceptance_criteria}` while the estimators read the fuller
  `contracts/story.v1.md` shape, including `domain_impact` and `readiness`.
