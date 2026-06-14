---
name: documentation
description: Update project documentation after code changes. Use when user updates PLAN.md, README.md, AGENTS.md, or any docs/ files. Triggers on "update docs", "update documentation", "update README", "update PLAN", "update AGENTS".
---

# Documentation Updates

## Philosophy

Documentation should reflect the current state of the code. When code changes, docs must change too.

## Files to Update

| File | When to Update |
|------|----------------|
| `PLAN.md` | Phase completion, architecture changes, new design decisions |
| `README.md` | New features, architecture changes, env vars, module table |
| `AGENTS.md` | Conventions, tech stack, project structure changes |
| `CONTRIBUTING.md` | Workflow changes, new setup steps |

## Workflow

1. Identify what changed in code
2. Determine which docs are affected
3. Update docs to match code state
4. Run lint to verify no issues

## Prism Conventions

- Use checkboxes for phases: `- [x] completed`, `- [ ] remaining`
- Architecture diagrams use ASCII art with `┌─┐│└─┘` boxes
- Module tables use `| module | purpose |` format
- Environment variables in `| Variable | Default | Description |` format
- Keep descriptions concise (one line per item)

## Checklist

Before committing documentation changes:

```bash
ruff check . && ruff format --check .
```

## What NOT to Document

- Implementation details (code is source of truth)
- Temporary states or workarounds
- Obvious behaviors
- Things that will change soon
