# Story contract v1

The unit of work every estimator and the planner reads. One story object per story.

**This file is the single source of truth for the shape.** Skills reference it; they do not
restate it. If the shape changes, it changes here and the version goes to `story.v2.md` —
skills naming `story.v1.md` keep reading v1 until they are moved deliberately.

Producers emit `{ "stories": [ <story>, ... ] }`. A bare story object is also valid input and
is treated as a batch of one.

```json
{
  "story_id": "US-001",
  "title": "Користувач входить за email і паролем",
  "user_story": "Як зареєстрований користувач, я хочу увійти...",
  "business_value": "Отримання доступу до персонального кабінету",
  "source_refs": ["PRD-3.1", "PRD-3.2"],
  "acceptance_criteria": [
    {
      "id": "AC-001",
      "given": "користувач має активний акаунт",
      "when": "вводить валідні дані",
      "then": "система відкриває персональний кабінет"
    }
  ],
  "business_rules": [],
  "edge_cases": [],
  "non_functional_requirements": [],
  "dependencies": [],
  "domain_impact": {
    "frontend": true,
    "backend": true,
    "qa": true,
    "devops": false
  },
  "assumptions": [],
  "open_questions": [],
  "out_of_scope": [],
  "readiness": "ready | needs_clarification | blocked"
}
```

## Fields

| Field | Meaning |
|---|---|
| `story_id` | Stable id. Every consumer echoes it back; it is how coverage is checked. |
| `title`, `user_story`, `business_value` | Human framing. Not sizing input on their own. |
| `source_refs` | Ids in the source PRD. Carried through so a number can be traced back. |
| `acceptance_criteria` | Given/when/then, each with its own `id`. The testable surface of the story. |
| `business_rules` | Constraints the implementation must honour that no AC states outright. |
| `edge_cases` | Known non-happy paths. |
| `non_functional_requirements` | a11y, i18n, performance, responsive, security, and similar. |
| `dependencies` | Other `story_id`s or external systems this story needs first. |
| `domain_impact` | Which disciplines the story touches. Each estimator reads only its own flag. |
| `assumptions` | What the producer assumed while writing the story. |
| `open_questions` | What the source did not answer. |
| `out_of_scope` | Explicitly excluded — must not be estimated. |
| `readiness` | One of `ready`, `needs_clarification`, `blocked`. |

## Notes for consumers

- `readiness` carries exactly one of the three literals. The union string
  `"ready | needs_clarification | blocked"` is a template artifact, not a value — treat
  anything unrecognised as `needs_clarification` and say so.
- An empty array means *nothing was written down*, which is not the same as *nothing exists*.
  Consumers must not read `"edge_cases": []` as "this story has no edge cases".
