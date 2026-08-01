---
name: story-planner-hitl
description: Convert a product requirements document (PRD), feature brief, or requirements specification into traceable, estimate-ready user stories with acceptance criteria, domain routing for FE, BE, QA, and DevOps, coverage checks, explicit assumptions, and mandatory human-in-the-loop approval gates. Use when preparing work for downstream estimation agents or a deterministic workflow, reviewing story decomposition, identifying PRD gaps or contradictions, or revising a story plan after stakeholder feedback. Do not use to estimate effort, select architecture, or create implementation tasks.
---

# Story Planner (HITL)

Transform a PRD into vertical, independently estimable user stories. Preserve traceability, expose uncertainty, and stop for human approval before marking the plan ready for FE, BE, QA, and DevOps estimators.

Paths below (`references/…`, `scripts/…`) are relative to this skill's directory.

## Enforce boundaries

- Plan stories; never estimate hours, days, story points, effort, or complexity.
- Describe observable product behavior; never invent APIs, tables, components, cloud services, frameworks, or architecture.
- Treat PRD statements as facts only when traceable to the supplied source.
- Label derived requirements, assumptions, questions, contradictions, and missing information explicitly.
- Keep technical implementation tasks out of the story list. Let downstream domain nodes derive them.
- Preserve the PRD language unless the user requests another language.
- Never set `READY_FOR_ESTIMATION` without recorded human approval at both gates.

## Read the output contract

Read [references/output-contract.md](references/output-contract.md) before planning. When emitting JSON for orchestration, conform to [references/story-plan.schema.json](references/story-plan.schema.json). Validate saved JSON with `scripts/validate_story_plan.py`.

## Execute the workflow

### 1. Establish the input boundary

Collect the PRD and any supplied project context:

- product type and supported platforms;
- existing versus greenfield system;
- known constraints and integrations;
- Definition of Ready and Definition of Done;
- explicit in-scope, out-of-scope, and already-built capabilities.

Do not block merely because optional context is absent. Record missing context only when it changes decomposition or estimability.

### 2. Build a requirement registry

Extract every functional, non-functional, business-rule, data, integration, role/permission, compliance, migration, analytics, and operational requirement.

For each requirement:

1. Assign a stable `REQ-###` identifier.
2. Preserve a precise `source_ref`, using a heading, section, paragraph, or page locator.
3. Record a concise requirement statement without broadening it.
4. Classify its evidence as `explicit`, `derived`, or `assumption`.
5. Mark contradictions and missing information instead of resolving them silently.

If the source has no stable numbering, create deterministic locators such as `Authentication > paragraph 2`; do not fabricate PRD section numbers.

### 3. Decompose into vertical stories

Create stories that deliver one user or business outcome and can be accepted independently. Prefer user-visible vertical slices over technical layers.

Split a story when it mixes:

- multiple user goals or materially different roles;
- independent workflows or integrations;
- platform-specific behavior with substantially different acceptance;
- administration, migration, analytics, and primary product behavior;
- acceptance criteria too broad to review or estimate as one unit.

Do not split solely into UI, API, database, testing, or deployment stories. Represent those concerns with `domain_impact` for downstream routing.

For each story:

- assign a stable `US-###` identifier;
- write `As a / I want / So that` behavior, using a business actor;
- state the business value;
- link one or more requirement IDs;
- add observable Given/When/Then acceptance criteria;
- capture business rules, edge cases, dependencies, and relevant non-functional requirements;
- route potential impact to `fe`, `be`, `qa`, and `devops` without estimating the work;
- mark readiness as `ready`, `needs_clarification`, or `blocked`.

Set `qa: true` for every estimate-ready story. Set `devops: true` only for a story with a specific operational, environment, secret, observability, migration, deployment, networking, or managed-service impact.

### 4. Run a completeness and quality pass

Verify that:

- every requirement is covered by at least one story or explicitly excluded;
- every story traces to at least one requirement;
- no requirement or story is duplicated;
- all actors, permissions, negative paths, and critical edge cases are represented;
- non-functional and cross-cutting requirements remain visible;
- dependencies reference existing stories and contain no obvious cycle;
- acceptance criteria are observable and testable;
- assumptions are not presented as PRD facts;
- no estimate or invented implementation detail appears.

Calculate coverage from the requirement registry. Do not claim 100% coverage when requirements remain uncovered or excluded without a recorded reason.

### 5. Pause at HITL Gate 1: scope and decomposition

Set status to `DRAFT_AWAITING_SCOPE_REVIEW` and current gate to `scope_review`. Present:

- a compact story list;
- covered, uncovered, and excluded requirement counts;
- proposed assumptions;
- contradictions and blocking questions;
- decomposition choices that materially affect scope.

Ask the human to approve the scope/decomposition or provide revisions. State explicitly that the skill requires this pause. Do not continue to the readiness gate until the response is recorded in `decision_log`.

If operating as a deterministic workflow node, return the structured payload and stop execution. Resume only with an explicit human decision event.

### 6. Apply human decisions

Apply only the decisions the reviewer made. Record the reviewer label, decision, timestamp when available, and notes. Never infer approval from silence.

When the reviewer requests changes, set `REVISION_REQUIRED`, revise the registry and stories, rerun quality checks, and return to Gate 1 if scope changed materially.

When blocking questions remain, set `DRAFT_AWAITING_CLARIFICATION`. Batch related questions, explain their estimation impact, and avoid asking for preferences that do not affect story boundaries or acceptance.

### 7. Pause at HITL Gate 2: estimation readiness

After scope approval and revision, set status to `DRAFT_AWAITING_READINESS_APPROVAL` and current gate to `readiness_approval`. Present:

- final story count and routing counts by domain;
- stories still marked `needs_clarification` or `blocked`;
- open assumptions and non-blocking questions;
- coverage and quality-check results;
- the exact downstream handoff boundary.

Ask the human to approve readiness or request revisions. State explicitly that the skill requires this pause. Never treat approval of Gate 1 as approval of Gate 2.

### 8. Finalize the handoff

Set `READY_FOR_ESTIMATION` only when:

- both HITL gates have explicit approvals in `decision_log`;
- all stories are `ready`;
- no blocking question remains open or deferred;
- every included requirement is covered;
- all deterministic validation errors are resolved.

Return the complete structured plan. Downstream nodes must estimate only their routed domain impact and must not reinterpret the entire PRD unless the handoff explicitly identifies missing context.

Set `BLOCKED` when a contradiction or missing decision prevents meaningful decomposition after the human has been asked. Describe the exact decision needed to resume.

## Handle compact human commands

Interpret human responses conservatively:

- `approve scope` approves Gate 1 only.
- `approve readiness` approves Gate 2 only.
- `approve all` approves both gates only when the complete Gate 2 package is visible in the same interaction.
- `revise ...` records a revision request and invalidates later approvals affected by the change.
- An answer to a question resolves that question but does not imply gate approval.
- Silence, acknowledgement, or “looks interesting” never counts as approval.

## Validate orchestration output

Save the structured result as JSON when the workflow requires machine-readable output, then run:

```bash
python3 scripts/validate_story_plan.py path/to/story-plan.json
```

Treat validator errors as blocking. Treat warnings as items to disclose at the next HITL gate.
