---
name: story-planner-hitl
description: Convert a product requirements document (PRD), feature brief, or requirements specification into traceable, estimate-ready user stories with acceptance criteria, domain routing for FE, BE, QA, and DevOps, coverage checks, and explicitly labeled assumptions — fully autonomously, with no approval gates. Use when preparing work for downstream estimation agents or a deterministic workflow, decomposing a PRD end to end, or identifying PRD gaps and contradictions. Do not use to estimate effort, select architecture, or create implementation tasks.
---

# Story Planner (autonomous)

Transform a PRD into vertical, independently estimable user stories in a single autonomous pass. Preserve traceability, resolve ambiguity by adopting labeled assumptions, and emit a terminal result routed for FE, BE, QA, and DevOps estimators — without pausing for human approval.

Paths below (`references/…`, `scripts/…`) are relative to this skill's directory.

## Enforce boundaries

- Plan stories; never estimate hours, days, story points, effort, or complexity.
- Describe observable product behavior; never invent APIs, tables, components, cloud services, frameworks, or architecture.
- Treat PRD statements as facts only when traceable to the supplied source.
- Label derived requirements, assumptions, residual questions, and contradictions explicitly.
- Keep technical implementation tasks out of the story list. Let downstream domain nodes derive them.
- Preserve the PRD language unless the user requests another language.
- Run to completion without asking for approval. Resolve ambiguity by adopting the most defensible assumption; return `BLOCKED` only for a true contradiction or missing fact that no interpretation can settle.

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
- mark readiness as `ready`, or `blocked` when a blocking question could not be settled by assumption.

Set `qa: true` for every estimate-ready story. Set `devops: true` only for a story with a specific operational, environment, secret, observability, migration, deployment, networking, or managed-service impact.

### 4. Resolve ambiguity autonomously

When the PRD is silent or ambiguous, decide rather than ask:

- adopt the most defensible interpretation as an `assumptions` entry with a `statement`, a `rationale`, and `affected_story_ids`;
- if you surfaced the ambiguity as an `open_questions` entry, set its `status` to `resolved_by_assumption` and name the adopting assumption in `resolution`;
- set `evidence_type: assumption` on any requirement decomposed under an adopted assumption.

Reserve a genuine `blocking` question (`status: open`) only for a contradiction or missing fact that no interpretation can settle — this forces overall status `BLOCKED`.

### 5. Run a completeness and quality pass

Verify that:

- every requirement is covered by at least one story or explicitly excluded;
- every story traces to at least one requirement;
- no requirement or story is duplicated;
- all actors, permissions, negative paths, and critical edge cases are represented;
- non-functional and cross-cutting requirements remain visible;
- dependencies reference existing stories and contain no obvious cycle;
- acceptance criteria are observable and testable;
- assumptions are recorded in `assumptions`, not presented as PRD facts;
- no estimate or invented implementation detail appears.

Calculate coverage from the requirement registry. Do not claim 100% coverage when requirements remain uncovered or excluded without a recorded reason.

### 6. Emit the terminal result

Set `READY_FOR_ESTIMATION` when:

- at least one story exists and all stories are `ready`;
- `qa: true` for every story;
- no `open_questions` entry is both `blocking: true` and `status: open`;
- every included requirement is covered;
- all quality checks pass;
- no estimation or implementation-design field appears.

Return the complete structured plan. Downstream nodes must estimate only their routed domain impact and must not reinterpret the entire PRD unless the handoff explicitly identifies missing context.

Set `BLOCKED` when a contradiction or missing fact prevents meaningful decomposition and no assumption can defensibly resolve it. Record the exact decision needed to resume as an `open_questions` entry with `blocking: true` and `status: open`.

## Validate orchestration output

Save the structured result as JSON when the workflow requires machine-readable output, then run:

```bash
python3 scripts/validate_story_plan.py path/to/story-plan.json
```

Treat validator errors as blocking. Treat warnings as items to disclose in the returned plan.
