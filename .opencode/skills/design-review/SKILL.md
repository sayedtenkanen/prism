---
name: design-review
description: Interview the user about a plan or design until reaching shared understanding. Use when user wants to stress-test a plan, get grilled on their design, or mentions "design review". Stop when user says "done" or all branches resolved.
---

# Design Review

## Flow

1. Read the plan/design the user provides
2. Identify decision branches (tech choices, tradeoffs, edge cases)
3. Ask ONE question at a time with recommended answer
4. After each answer, summarize what was resolved
5. When all branches resolved, output final summary

## Output

End with:
- List of resolved decisions
- Recommended approach for each
- Open questions (if any)

## Integration

After design-review completes, suggest running relevant skills (tdd, code-review, etc.)
