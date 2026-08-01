# Story plan output contract

Use this contract for both conversational and orchestrated runs. The JSON Schema is authoritative for field shapes; this document defines semantics and state transitions.

## State machine

```text
DRAFT_AWAITING_SCOPE_REVIEW
  -> REVISION_REQUIRED -> DRAFT_AWAITING_SCOPE_REVIEW
  -> DRAFT_AWAITING_CLARIFICATION -> DRAFT_AWAITING_SCOPE_REVIEW
  -> DRAFT_AWAITING_READINESS_APPROVAL
       -> REVISION_REQUIRED
       -> DRAFT_AWAITING_CLARIFICATION
       -> READY_FOR_ESTIMATION

Any draft state -> BLOCKED when a required human decision prevents progress.
```

Never transition to `READY_FOR_ESTIMATION` without separate `scope_review` and `readiness_approval` approvals.

## Top-level fields

- `schema_version`: Use `1.0`.
- `plan_id`: Use a stable identifier supplied by the orchestrator or a locally unique identifier.
- `status`: Use one of the state-machine values.
- `prd`: Identify the PRD without copying its full contents.
- `requirements`: Maintain the traceability registry.
- `stories`: Maintain independently estimable vertical slices.
- `open_questions`: Expose ambiguity and its estimation impact.
- `assumptions`: Record assumptions separately from requirements.
- `cross_cutting_concerns`: Identify concerns shared across stories without duplicating scope.
- `coverage`: Report included, covered, uncovered, and excluded requirements.
- `quality_checks`: Report deterministic and semantic checks.
- `human_review`: Store the active gate, requested decisions, and immutable decision history.

## Requirement semantics

Use `evidence_type` as follows:

- `explicit`: stated directly in the PRD;
- `derived`: logically necessary to satisfy an explicit statement;
- `assumption`: temporarily introduced and awaiting human confirmation.

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

## HITL event contract

Each decision-log entry must identify one gate:

- `scope_review`
- `readiness_approval`
- `clarification`
- `revision`

Use `decision` values:

- `approved`
- `changes_requested`
- `answered`
- `rejected`

For an orchestrator, resume the workflow with an event containing at minimum:

```json
{
  "plan_id": "PLAN-001",
  "gate": "scope_review",
  "decision": "approved",
  "reviewer": "product-owner",
  "notes": "Scope and split accepted"
}
```

Never overwrite older decisions. Append a new event. When a revision changes previously approved scope, append a new `changes_requested` event and require fresh affected approvals.

## Readiness invariants

Require all of these for `READY_FOR_ESTIMATION`:

1. Include at least one story.
2. Mark every story `ready`.
3. Set `qa: true` for every story.
4. Resolve every blocking question.
5. Cover every included requirement.
6. Record approval for both HITL gates.
7. Pass every quality check.
8. Include no estimation or implementation-design fields.

## Downstream handoff

Each estimator must receive:

- stories routed to its domain;
- acceptance criteria and linked requirements;
- relevant dependencies and non-functional requirements;
- approved assumptions and remaining non-blocking questions;
- cross-cutting concerns relevant to its domain.

Do not ask downstream estimators to reconstruct scope from the original PRD.
