# Story plan output contract (autonomous)

Use this contract for both conversational and orchestrated runs. The JSON Schema is authoritative for field shapes; this document defines semantics. The skill runs to completion without human approval gates: it decides, records its reasoning, and emits a terminal result.

## Terminal states

```text
READY_FOR_ESTIMATION   plan is complete and passes every quality check
BLOCKED                a genuine contradiction or missing fact prevents decomposition
```

There are no intermediate or awaiting-human states. The skill never pauses for approval; it resolves ambiguity by adopting a labeled assumption, and only returns `BLOCKED` when no defensible assumption can unblock decomposition.

## Top-level fields

- `schema_version`: Use `1.0`.
- `plan_id`: Use a stable identifier supplied by the orchestrator or a locally unique identifier.
- `status`: Use one of the terminal states.
- `prd`: Identify the PRD without copying its full contents.
- `requirements`: Maintain the traceability registry.
- `stories`: Maintain independently estimable vertical slices.
- `open_questions`: Expose residual ambiguity and its estimation impact.
- `assumptions`: Record every assumption the skill adopted to proceed.
- `cross_cutting_concerns`: Identify concerns shared across stories without duplicating scope.
- `coverage`: Report included, covered, uncovered, and excluded requirements.
- `quality_checks`: Report deterministic and semantic checks.

## Requirement semantics

Use `evidence_type` as follows:

- `explicit`: stated directly in the PRD;
- `derived`: logically necessary to satisfy an explicit statement;
- `assumption`: introduced by the skill to proceed, and backed by a recorded entry in `assumptions`.

Use `coverage_status` as follows:

- `covered`: linked to one or more stories;
- `uncovered`: in scope but not yet represented;
- `excluded`: intentionally out of scope with a reason.

Do not use `excluded` to hide difficult or ambiguous work.

## Story semantics

Keep identifiers stable across revisions. Do not renumber unaffected stories.

Use `domain_impact` only as routing metadata:

- `fe`: client UI, client state, accessibility, or client behavior;
- `be`: business logic, API behavior, data, permissions, or integration behavior;
- `qa`: acceptance, integration, regression, performance, security, or exploratory testing;
- `devops`: environments, deployment, secrets, observability, networking, migrations, or managed services.

Do not add estimates, technical designs, implementation subtasks, or staffing recommendations.

Use `readiness`:

- `ready`: fully decomposed and estimable as-is;
- `blocked`: cannot be estimated because a blocking question could not be resolved by assumption. A plan with any `blocked` story is `BLOCKED`.

## Ambiguity handling (no human in the loop)

When the PRD is silent or ambiguous, the skill does not ask — it decides:

1. Adopt the most defensible interpretation as an entry in `assumptions`, with a `statement`, a `rationale`, and `affected_story_ids`.
2. If the ambiguity was surfaced as a question, keep it in `open_questions` with `status: resolved_by_assumption` and a `resolution` naming the adopting assumption.
3. Any requirement decomposed under an assumption sets that requirement's `evidence_type` to `assumption`.

Return `BLOCKED` only when the ambiguity is a true contradiction or a missing fact for which no interpretation is defensible. Record it as an `open_questions` entry with `blocking: true` and `status: open`, and describe the exact decision needed to resume.

## Readiness invariants

Require all of these for `READY_FOR_ESTIMATION`:

1. Include at least one story.
2. Mark every story `ready`.
3. Set `qa: true` for every story.
4. Leave no `open_questions` entry with `blocking: true` and `status: open` (such a plan must be `BLOCKED`).
5. Cover every included requirement.
6. Pass every quality check.
7. Include no estimation or implementation-design fields.

## Downstream handoff

Each estimator must receive:

- stories routed to its domain;
- acceptance criteria and linked requirements;
- relevant dependencies and non-functional requirements;
- adopted assumptions and residual non-blocking questions;
- cross-cutting concerns relevant to its domain.

Do not ask downstream estimators to reconstruct scope from the original PRD.
