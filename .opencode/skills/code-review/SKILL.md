---
name: code-review
description: Address code review comments systematically. Use when user has review comments to address, mentions "code review", "review comments", "address comments", "fix review feedback". Triggers on review workflow.
---

# Code Review Workflow

## Philosophy

Address review comments one at a time using TDD. Each comment is a separate cycle: understand → test → fix → verify.

## Workflow

### 1. Parse Comments

Read all review comments. Categorize:
- **Bug risks** → Must fix (silently skipping, missing validation)
- **Suggestions** → Should fix (encoding, explicit labels)
- **Testing gaps** → Add tests for uncovered behavior

### 2. Prioritize

Order by severity:
1. Bug risks (silent failures, data corruption)
2. Missing validation (error handling)
3. Consistency issues (dict shapes, encoding)
4. Test coverage gaps

### 3. TDD Cycle Per Comment

For each comment:

```
RED:   Write test for the behavior the comment describes
GREEN: Write minimal code to pass
VERIFY: Run test suite + lint
```

**One comment at a time.** Don't batch fixes.

### 4. Verify

After all comments addressed:

```bash
ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short --cov=app --cov-report=term --cov-fail-under=90
```

## Prism-Specific Patterns

### MemoryStore
- Separate indices for different lookup keys (repo vs pr_id)
- Rebuild indices on delete/evict

### FeedbackCollector
- Skip empty reviewer strings in aggregation
- Add count fields for unnamed entries

### DatasetBuilder
- Validate indices before accessing lists
- Always return consistent dict shapes
- Skip entries with empty expected findings

### JSON Export/Import
- Always specify `encoding="utf-8"`

## Checklist Per Comment

```
[ ] Understand what the comment is asking
[ ] Write test that demonstrates the behavior
[ ] Verify test fails (RED)
[ ] Write minimal fix (GREEN)
[ ] Run: ruff check . && ruff format --check . && mypy app/ && pytest tests/ -v --tb=short
[ ] Move to next comment
```
