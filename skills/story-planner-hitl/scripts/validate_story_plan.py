#!/usr/bin/env python3
"""Validate Story Planner HITL JSON without third-party dependencies."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any


ALLOWED_STATUSES = {
    "DRAFT_AWAITING_SCOPE_REVIEW": "scope_review",
    "DRAFT_AWAITING_CLARIFICATION": "clarification",
    "DRAFT_AWAITING_READINESS_APPROVAL": "readiness_approval",
    "REVISION_REQUIRED": "revision",
    "READY_FOR_ESTIMATION": "complete",
    "BLOCKED": "blocked",
}

REQUIRED_TOP_LEVEL = {
    "schema_version",
    "plan_id",
    "status",
    "prd",
    "requirements",
    "stories",
    "open_questions",
    "assumptions",
    "cross_cutting_concerns",
    "coverage",
    "quality_checks",
    "human_review",
}

FORBIDDEN_ESTIMATE_KEYS = {
    "estimate",
    "estimates",
    "estimated_hours",
    "estimated_days",
    "story_points",
    "effort",
    "complexity_score",
    "t_shirt_size",
    "cost_estimate",
}

REQUIRED_QUALITY_CHECKS = {
    "requirements_traceable",
    "stories_testable",
    "no_duplicate_scope",
    "no_estimates",
    "no_invented_implementation",
    "dependencies_valid",
}

REQUIREMENT_KEYS = {
    "requirement_id",
    "source_ref",
    "statement",
    "category",
    "evidence_type",
    "coverage_status",
    "story_ids",
}
STORY_KEYS = {
    "story_id",
    "title",
    "user_story",
    "business_value",
    "source_requirement_ids",
    "acceptance_criteria",
    "business_rules",
    "edge_cases",
    "non_functional_requirements",
    "dependencies",
    "domain_impact",
    "readiness",
}
REQUIREMENT_CATEGORIES = {
    "functional",
    "non_functional",
    "business_rule",
    "data",
    "integration",
    "role_permission",
    "compliance",
    "migration",
    "analytics",
    "operational",
}


def duplicate_values(values: list[Any]) -> set[Any]:
    seen: set[Any] = set()
    duplicates: set[Any] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return duplicates


def collect_forbidden_keys(value: Any, path: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key.lower() in FORBIDDEN_ESTIMATE_KEYS:
                findings.append(child_path)
            findings.extend(collect_forbidden_keys(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(collect_forbidden_keys(child, f"{path}[{index}]"))
    return findings


def require_string(item: dict[str, Any], key: str, path: str, errors: list[str]) -> None:
    if not isinstance(item.get(key), str) or not item[key].strip():
        errors.append(f"{path}.{key} must be a non-empty string")


def validate_object_keys(
    item: dict[str, Any],
    required: set[str],
    optional: set[str],
    path: str,
    errors: list[str],
) -> None:
    missing = sorted(required - item.keys())
    unexpected = sorted(item.keys() - required - optional)
    if missing:
        errors.append(f"{path} is missing fields: {', '.join(missing)}")
    if unexpected:
        errors.append(f"{path} has unexpected fields: {', '.join(unexpected)}")


def find_dependency_cycle(stories: list[Any]) -> list[str] | None:
    graph = {
        item.get("story_id"): item.get("dependencies", [])
        for item in stories
        if isinstance(item, dict) and isinstance(item.get("story_id"), str)
    }
    visiting: set[str] = set()
    visited: set[str] = set()
    path: list[str] = []

    def visit(node: str) -> list[str] | None:
        if node in visiting:
            start = path.index(node)
            return path[start:] + [node]
        if node in visited:
            return None
        visiting.add(node)
        path.append(node)
        for dependency in graph.get(node, []):
            if dependency in graph:
                cycle = visit(dependency)
                if cycle:
                    return cycle
        path.pop()
        visiting.remove(node)
        visited.add(node)
        return None

    for story_id in graph:
        cycle = visit(story_id)
        if cycle:
            return cycle
    return None


def validate(data: Any) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(data, dict):
        return ["$ must be a JSON object"], warnings

    missing_top = sorted(REQUIRED_TOP_LEVEL - data.keys())
    if missing_top:
        errors.append(f"$ is missing fields: {', '.join(missing_top)}")
    unexpected_top = sorted(data.keys() - REQUIRED_TOP_LEVEL)
    if unexpected_top:
        errors.append(f"$ has unexpected fields: {', '.join(unexpected_top)}")

    if data.get("schema_version") != "1.0":
        errors.append("$.schema_version must equal '1.0'")

    status = data.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(f"$.status must be one of: {', '.join(sorted(ALLOWED_STATUSES))}")

    require_string(data, "plan_id", "$", errors)

    forbidden = collect_forbidden_keys(data)
    if forbidden:
        errors.append("forbidden estimation fields found at: " + ", ".join(forbidden))

    prd = data.get("prd")
    if not isinstance(prd, dict):
        errors.append("$.prd must be an object")
    else:
        validate_object_keys(prd, {"title", "source_id"}, {"version", "language"}, "$.prd", errors)
        require_string(prd, "title", "$.prd", errors)
        require_string(prd, "source_id", "$.prd", errors)

    requirements = data.get("requirements", [])
    stories = data.get("stories", [])
    questions = data.get("open_questions", [])
    assumptions = data.get("assumptions", [])

    for field_name, value in (
        ("requirements", requirements),
        ("stories", stories),
        ("open_questions", questions),
        ("assumptions", assumptions),
    ):
        if not isinstance(value, list):
            errors.append(f"$.{field_name} must be an array")

    if errors and not all(isinstance(value, list) for value in (requirements, stories, questions, assumptions)):
        return errors, warnings

    requirement_ids = [item.get("requirement_id") for item in requirements if isinstance(item, dict)]
    story_ids = [item.get("story_id") for item in stories if isinstance(item, dict)]
    question_ids = [item.get("question_id") for item in questions if isinstance(item, dict)]
    assumption_ids = [item.get("assumption_id") for item in assumptions if isinstance(item, dict)]

    for label, identifiers in (
        ("requirement", requirement_ids),
        ("story", story_ids),
        ("question", question_ids),
        ("assumption", assumption_ids),
    ):
        duplicates = duplicate_values(identifiers)
        if duplicates:
            errors.append(f"duplicate {label} IDs: {', '.join(map(str, sorted(duplicates)))}")

    requirement_id_set = set(requirement_ids)
    story_id_set = set(story_ids)

    for index, requirement in enumerate(requirements):
        path = f"$.requirements[{index}]"
        if not isinstance(requirement, dict):
            errors.append(f"{path} must be an object")
            continue
        validate_object_keys(requirement, REQUIREMENT_KEYS, {"exclusion_reason"}, path, errors)
        for key in ("requirement_id", "source_ref", "statement"):
            require_string(requirement, key, path, errors)
        if requirement.get("category") not in REQUIREMENT_CATEGORIES:
            errors.append(f"{path}.category is invalid")
        if requirement.get("evidence_type") not in {"explicit", "derived", "assumption"}:
            errors.append(f"{path}.evidence_type is invalid")
        coverage_status = requirement.get("coverage_status")
        if coverage_status not in {"covered", "uncovered", "excluded"}:
            errors.append(f"{path}.coverage_status is invalid")
        linked_stories = requirement.get("story_ids")
        if not isinstance(linked_stories, list):
            errors.append(f"{path}.story_ids must be an array")
            continue
        unknown_stories = sorted(set(linked_stories) - story_id_set)
        if unknown_stories:
            errors.append(f"{path}.story_ids references unknown stories: {', '.join(unknown_stories)}")
        if coverage_status == "covered" and not linked_stories:
            errors.append(f"{path} is covered but has no linked story")
        if coverage_status == "uncovered" and linked_stories:
            errors.append(f"{path} is uncovered but links stories")
        if coverage_status == "excluded" and not requirement.get("exclusion_reason"):
            errors.append(f"{path} is excluded but has no exclusion_reason")

    all_acceptance_ids: list[Any] = []
    for index, story in enumerate(stories):
        path = f"$.stories[{index}]"
        if not isinstance(story, dict):
            errors.append(f"{path} must be an object")
            continue
        validate_object_keys(story, STORY_KEYS, set(), path, errors)
        for key in ("story_id", "title", "user_story", "business_value"):
            require_string(story, key, path, errors)
        if story.get("readiness") not in {"ready", "needs_clarification", "blocked"}:
            errors.append(f"{path}.readiness is invalid")
        for array_key in ("business_rules", "edge_cases", "non_functional_requirements"):
            value = story.get(array_key)
            if not isinstance(value, list) or not all(isinstance(entry, str) and entry.strip() for entry in value):
                errors.append(f"{path}.{array_key} must be an array of non-empty strings")
        source_ids = story.get("source_requirement_ids")
        if not isinstance(source_ids, list) or not source_ids:
            errors.append(f"{path}.source_requirement_ids must be a non-empty array")
        else:
            unknown_requirements = sorted(set(source_ids) - requirement_id_set)
            if unknown_requirements:
                errors.append(
                    f"{path}.source_requirement_ids references unknown requirements: "
                    + ", ".join(unknown_requirements)
                )
        criteria = story.get("acceptance_criteria")
        if not isinstance(criteria, list) or not criteria:
            errors.append(f"{path}.acceptance_criteria must be a non-empty array")
        else:
            for criterion_index, criterion in enumerate(criteria):
                criterion_path = f"{path}.acceptance_criteria[{criterion_index}]"
                if not isinstance(criterion, dict):
                    errors.append(f"{criterion_path} must be an object")
                    continue
                validate_object_keys(
                    criterion,
                    {"criterion_id", "given", "when", "then"},
                    set(),
                    criterion_path,
                    errors,
                )
                all_acceptance_ids.append(criterion.get("criterion_id"))
                for key in ("criterion_id", "given", "when", "then"):
                    require_string(criterion, key, criterion_path, errors)
        dependencies = story.get("dependencies")
        if not isinstance(dependencies, list):
            errors.append(f"{path}.dependencies must be an array")
        else:
            unknown_dependencies = sorted(set(dependencies) - story_id_set)
            if unknown_dependencies:
                errors.append(f"{path}.dependencies references unknown stories: {', '.join(unknown_dependencies)}")
            if story.get("story_id") in dependencies:
                errors.append(f"{path}.dependencies contains a self-dependency")
        domains = story.get("domain_impact")
        if not isinstance(domains, dict):
            errors.append(f"{path}.domain_impact must be an object")
        else:
            if set(domains) != {"fe", "be", "qa", "devops"}:
                errors.append(f"{path}.domain_impact must contain only fe, be, qa, and devops")
            if not all(isinstance(value, bool) for value in domains.values()):
                errors.append(f"{path}.domain_impact values must be booleans")
            if not any(domains.values()):
                errors.append(f"{path}.domain_impact must route to at least one domain")
            if story.get("readiness") == "ready" and domains.get("qa") is not True:
                errors.append(f"{path} is ready but qa routing is false")

    duplicate_acceptance_ids = duplicate_values(all_acceptance_ids)
    if duplicate_acceptance_ids:
        errors.append("duplicate acceptance criterion IDs: " + ", ".join(map(str, sorted(duplicate_acceptance_ids))))

    cycle = find_dependency_cycle(stories)
    if cycle:
        errors.append("story dependency cycle: " + " -> ".join(cycle))

    for requirement in requirements:
        if not isinstance(requirement, dict):
            continue
        requirement_id = requirement.get("requirement_id")
        for story_id in requirement.get("story_ids", []):
            story = next(
                (item for item in stories if isinstance(item, dict) and item.get("story_id") == story_id),
                None,
            )
            if story and requirement_id not in story.get("source_requirement_ids", []):
                errors.append(f"traceability mismatch: {requirement_id} links {story_id}, but the story does not link back")

    for index, question in enumerate(questions):
        path = f"$.open_questions[{index}]"
        if not isinstance(question, dict):
            errors.append(f"{path} must be an object")
            continue
        validate_object_keys(
            question,
            {"question_id", "question", "impact", "blocking", "status", "affected_story_ids"},
            {"answer"},
            path,
            errors,
        )
        for key in ("question_id", "question", "impact"):
            require_string(question, key, path, errors)
        if not isinstance(question.get("blocking"), bool):
            errors.append(f"{path}.blocking must be boolean")
        if question.get("status") not in {"open", "resolved", "deferred"}:
            errors.append(f"{path}.status is invalid")
        affected = question.get("affected_story_ids", [])
        if not isinstance(affected, list):
            errors.append(f"{path}.affected_story_ids must be an array")
        else:
            unknown = sorted(set(affected) - story_id_set)
            if unknown:
                errors.append(f"{path}.affected_story_ids references unknown stories: {', '.join(unknown)}")
        if question.get("status") == "resolved" and not question.get("answer"):
            errors.append(f"{path} is resolved but has no answer")

    for index, assumption in enumerate(assumptions):
        path = f"$.assumptions[{index}]"
        if not isinstance(assumption, dict):
            errors.append(f"{path} must be an object")
            continue
        validate_object_keys(
            assumption,
            {"assumption_id", "statement", "status", "affected_story_ids"},
            set(),
            path,
            errors,
        )
        for key in ("assumption_id", "statement"):
            require_string(assumption, key, path, errors)
        if assumption.get("status") not in {"proposed", "approved", "rejected"}:
            errors.append(f"{path}.status is invalid")
        affected = assumption.get("affected_story_ids", [])
        if not isinstance(affected, list):
            errors.append(f"{path}.affected_story_ids must be an array")
        else:
            unknown = sorted(set(affected) - story_id_set)
            if unknown:
                errors.append(f"{path}.affected_story_ids references unknown stories: {', '.join(unknown)}")

    concerns = data.get("cross_cutting_concerns")
    if not isinstance(concerns, list):
        errors.append("$.cross_cutting_concerns must be an array")
    else:
        for index, concern in enumerate(concerns):
            path = f"$.cross_cutting_concerns[{index}]"
            if not isinstance(concern, dict):
                errors.append(f"{path} must be an object")
                continue
            validate_object_keys(
                concern,
                {"concern", "affected_story_ids", "affected_domains"},
                set(),
                path,
                errors,
            )
            require_string(concern, "concern", path, errors)
            affected_story_ids = concern.get("affected_story_ids")
            if not isinstance(affected_story_ids, list):
                errors.append(f"{path}.affected_story_ids must be an array")
            else:
                unknown = sorted(set(affected_story_ids) - story_id_set)
                if unknown:
                    errors.append(f"{path}.affected_story_ids references unknown stories: {', '.join(unknown)}")
            affected_domains = concern.get("affected_domains")
            if not isinstance(affected_domains, list) or not set(affected_domains).issubset({"fe", "be", "qa", "devops"}):
                errors.append(f"{path}.affected_domains must contain only fe, be, qa, and devops")

    coverage = data.get("coverage")
    if not isinstance(coverage, dict):
        errors.append("$.coverage must be an object")
    else:
        validate_object_keys(
            coverage,
            {"total", "included", "covered", "uncovered", "excluded", "percent"},
            set(),
            "$.coverage",
            errors,
        )
        expected_total = len(requirements)
        excluded = sum(1 for item in requirements if isinstance(item, dict) and item.get("coverage_status") == "excluded")
        covered = sum(1 for item in requirements if isinstance(item, dict) and item.get("coverage_status") == "covered")
        uncovered = sum(1 for item in requirements if isinstance(item, dict) and item.get("coverage_status") == "uncovered")
        included = expected_total - excluded
        percent = 100.0 if included == 0 else round(covered * 100.0 / included, 2)
        expected = {
            "total": expected_total,
            "included": included,
            "covered": covered,
            "uncovered": uncovered,
            "excluded": excluded,
        }
        for key, expected_value in expected.items():
            if coverage.get(key) != expected_value:
                errors.append(f"$.coverage.{key} must equal {expected_value}")
        actual_percent = coverage.get("percent")
        if not isinstance(actual_percent, (int, float)) or not math.isclose(float(actual_percent), percent, abs_tol=0.01):
            errors.append(f"$.coverage.percent must equal {percent}")

    quality = data.get("quality_checks")
    if not isinstance(quality, dict):
        errors.append("$.quality_checks must be an object")
    else:
        validate_object_keys(quality, REQUIRED_QUALITY_CHECKS, {"warnings"}, "$.quality_checks", errors)
        missing_checks = sorted(REQUIRED_QUALITY_CHECKS - quality.keys())
        if missing_checks:
            errors.append("$.quality_checks is missing: " + ", ".join(missing_checks))
        for check in REQUIRED_QUALITY_CHECKS:
            if check in quality and not isinstance(quality[check], bool):
                errors.append(f"$.quality_checks.{check} must be boolean")

    human_review = data.get("human_review")
    if not isinstance(human_review, dict):
        errors.append("$.human_review must be an object")
        decision_log: list[Any] = []
    else:
        validate_object_keys(
            human_review,
            {"current_gate", "requested_decisions", "decision_log"},
            set(),
            "$.human_review",
            errors,
        )
        if human_review.get("current_gate") not in {
            "scope_review",
            "clarification",
            "readiness_approval",
            "revision",
            "complete",
            "blocked",
        }:
            errors.append("$.human_review.current_gate is invalid")
        requested_decisions = human_review.get("requested_decisions")
        if not isinstance(requested_decisions, list) or not all(
            isinstance(item, str) and item.strip() for item in requested_decisions
        ):
            errors.append("$.human_review.requested_decisions must be an array of non-empty strings")
        decision_log = human_review.get("decision_log", [])
        if not isinstance(decision_log, list):
            errors.append("$.human_review.decision_log must be an array")
            decision_log = []
        for index, decision in enumerate(decision_log):
            path = f"$.human_review.decision_log[{index}]"
            if not isinstance(decision, dict):
                errors.append(f"{path} must be an object")
                continue
            validate_object_keys(
                decision,
                {"gate", "decision", "reviewer", "notes"},
                {"timestamp"},
                path,
                errors,
            )
            if decision.get("gate") not in {"scope_review", "readiness_approval", "clarification", "revision"}:
                errors.append(f"{path}.gate is invalid")
            if decision.get("decision") not in {"approved", "changes_requested", "answered", "rejected"}:
                errors.append(f"{path}.decision is invalid")
            require_string(decision, "reviewer", path, errors)
            if not isinstance(decision.get("notes"), str):
                errors.append(f"{path}.notes must be a string")
        expected_gate = ALLOWED_STATUSES.get(status)
        if expected_gate and human_review.get("current_gate") != expected_gate:
            errors.append(f"$.human_review.current_gate must be '{expected_gate}' for status '{status}'")

    if status == "READY_FOR_ESTIMATION":
        if not stories:
            errors.append("READY_FOR_ESTIMATION requires at least one story")
        not_ready = [item.get("story_id") for item in stories if isinstance(item, dict) and item.get("readiness") != "ready"]
        if not_ready:
            errors.append("READY_FOR_ESTIMATION has non-ready stories: " + ", ".join(map(str, not_ready)))
        blocking_open = [
            item.get("question_id")
            for item in questions
            if isinstance(item, dict) and item.get("blocking") is True and item.get("status") != "resolved"
        ]
        if blocking_open:
            errors.append("READY_FOR_ESTIMATION has unresolved blocking questions: " + ", ".join(map(str, blocking_open)))
        proposed_assumptions = [
            item.get("assumption_id")
            for item in assumptions
            if isinstance(item, dict) and item.get("status") == "proposed"
        ]
        if proposed_assumptions:
            errors.append("READY_FOR_ESTIMATION has unapproved assumptions: " + ", ".join(map(str, proposed_assumptions)))
        if isinstance(coverage, dict) and coverage.get("uncovered") != 0:
            errors.append("READY_FOR_ESTIMATION requires zero uncovered requirements")
        if isinstance(quality, dict):
            failed_checks = [key for key in REQUIRED_QUALITY_CHECKS if quality.get(key) is not True]
            if failed_checks:
                errors.append("READY_FOR_ESTIMATION has failed quality checks: " + ", ".join(sorted(failed_checks)))
        latest_revision = max(
            (
                index
                for index, item in enumerate(decision_log)
                if isinstance(item, dict)
                and item.get("decision") in {"changes_requested", "rejected"}
                and item.get("gate") in {"scope_review", "readiness_approval", "revision"}
            ),
            default=-1,
        )
        latest_scope = max(
            (
                index
                for index, item in enumerate(decision_log)
                if isinstance(item, dict)
                and item.get("gate") == "scope_review"
                and item.get("decision") == "approved"
            ),
            default=-1,
        )
        latest_readiness = max(
            (
                index
                for index, item in enumerate(decision_log)
                if isinstance(item, dict)
                and item.get("gate") == "readiness_approval"
                and item.get("decision") == "approved"
            ),
            default=-1,
        )
        missing_approvals: set[str] = set()
        if latest_scope <= latest_revision:
            missing_approvals.add("scope_review")
        if latest_readiness <= max(latest_revision, latest_scope):
            missing_approvals.add("readiness_approval")
        if missing_approvals:
            errors.append("READY_FOR_ESTIMATION lacks approvals for: " + ", ".join(sorted(missing_approvals)))

    if status == "DRAFT_AWAITING_READINESS_APPROVAL":
        latest_scope = max(
            (
                index
                for index, item in enumerate(decision_log)
                if isinstance(item, dict)
                and item.get("gate") == "scope_review"
                and item.get("decision") == "approved"
            ),
            default=-1,
        )
        latest_revision = max(
            (
                index
                for index, item in enumerate(decision_log)
                if isinstance(item, dict)
                and item.get("decision") in {"changes_requested", "rejected"}
                and item.get("gate") in {"scope_review", "revision"}
            ),
            default=-1,
        )
        scope_approved = latest_scope > latest_revision
        if not scope_approved:
            errors.append("DRAFT_AWAITING_READINESS_APPROVAL requires scope_review approval")

    if not stories:
        warnings.append("plan contains no stories")
    if not requirements:
        warnings.append("plan contains no extracted requirements")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("story_plan", type=Path, help="Path to the story-plan JSON file")
    parser.add_argument("--json", action="store_true", help="Emit the validation result as JSON")
    args = parser.parse_args()

    try:
        data = json.loads(args.story_plan.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"ERROR: file not found: {args.story_plan}", file=sys.stderr)
        return 2
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read valid JSON: {exc}", file=sys.stderr)
        return 2

    errors, warnings = validate(data)
    result = {"valid": not errors, "errors": errors, "warnings": warnings}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")
        print("VALID" if not errors else "INVALID")

    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
