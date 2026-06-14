---
name: git
description: Git workflow, branches, commits, and PR patterns. Use when user mentions "git", "commit", "branch", "pr", "merge". Triggers on Git questions.
---

# Git Conventions

## Branch Workflow

```
main (protected)
├── feature/phase-X
├── fix/issue-123
└── chore/update-deps
```

## Commit Messages

```
type(scope): description

feat(sia): add memory store
fix(dataset): validate indices
test(feedback): add edge cases
docs(readme): update architecture
chore(deps): update dspy to 3.2
```

## Types

- `feat` - New feature
- `fix` - Bug fix
- `test` - Adding tests
- `docs` - Documentation
- `chore` - Maintenance
- `refactor` - Code restructuring

## Branch Protection

- Direct push to `main` blocked
- All changes via PRs
- CodeQL must pass before merge

## Checklist Before Push

```bash
git status
git diff --staged
git log --oneline -5
```

## PR Template

```markdown
## Changes
- What changed and why

## Tests
- [ ] All tests pass
- [ ] Lint passes
- [ ] Type check passes

## Related
- Closes #123
```
