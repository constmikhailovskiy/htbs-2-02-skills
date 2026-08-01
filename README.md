# estimator

Engineering team simulator as a set of Claude Code skills. A PRD goes in; a **confirmed**
estimate comes out.

The point is the word *confirmed*. A model will emit a confident number for any PRD and none of
it is true. So each skill here is allowed to produce only per-item numbers and objections —
every total, multiplier and coverage figure is arithmetic done outside the model, and a
challenger skill attacks the result before it is reported.

## Skills

In graph order — see [ORCHESTRATION.md](ORCHESTRATION.md) for how they are wired.

| Skill | Does | Status |
|---|---|---|
| `estimate-orchestrator` | brief → which sides the feature actually needs | placeholder |
| `brief-prd-input` | raw brief/PRD text → clean brief | placeholder |
| `story-planner` | brief → implementable stories per `contracts/story.v1.md` | placeholder |
| `be-estimate` | backend effort per story | placeholder |
| `frontend-estimate` | frontend effort per story: optimistic / likely / pessimistic | ✅ |
| `qa-estimate` | QA effort per story | placeholder |
| `devops-estimate` | DevOps / infrastructure effort per story | placeholder |
| `estimate-summary` | side totals, grand total, and the one risk buffer | placeholder |

Not in the graph:

| Skill | Does | Status |
|---|---|---|
| `wbs` | PRD → work items, each tagged with the `req` ids it implements | ✅ |
| `dimensions` | complexity / risk / unknowns per item | planned |
| `challenger` | attacks the estimate: missed work, lowballed items | planned |

`wbs` and `story-planner` both decompose a source document into units of work. They predate each
other and the overlap has not been resolved; the graph currently runs `story-planner`.

Aggregation is **not** model work — it is arithmetic (PERT `(o+4m+p)/6`, multipliers, sums) and
belongs outside the model by construction. `estimate-summary` and `brief-prd-input` have skill
files, but their nodes are deterministic code and those files are never sent to a model. They
document the contract; they do not instruct one.

## Install

```bash
# in Claude Code
/plugin marketplace add constmikhailovskiy/htbs-2-02-skills
/plugin install estimator
```

## Layout

```
.claude-plugin/plugin.json       the plugin manifest
.claude-plugin/marketplace.json  makes the repo installable as a marketplace
ORCHESTRATION.md                 the LangGraph workflow these skills are the prompt layer of
contracts/story.v1.md            the story shape every estimator and the planner reads
skills/<name>/SKILL.md           one skill per file
```

Adding a skill is a new directory with a `SKILL.md`. Nothing else changes.

Skills that consume stories reference `contracts/story.v1.md` rather than restating the shape,
so the contract has one owner and one place to change.
