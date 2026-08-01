---
name: wbs
description: Use when a PRD or feature description must be broken down into a work breakdown structure before it can be estimated
---

Break the PRD into work items. Do not estimate anything here — that is a separate skill.

Rules:

- One item per deliverable unit of work, not per sentence of the PRD.
- Every item carries the `req` ids it implements. An item that implements nothing is not work.
- Every requirement in the PRD must appear in at least one item. Omission is the most common way an estimate lies.
- If the PRD does not say enough to place an item, record it as an open question instead of guessing silently.

Return only JSON:

```json
{
  "items": [
    { "id": "W-001", "title": "short imperative phrase", "req": ["REQ-001"] }
  ],
  "open_questions": ["what the PRD does not answer"]
}
```
