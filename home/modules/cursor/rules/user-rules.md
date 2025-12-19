---
description: Core agent guidelines.
alwaysApply: true
---

Keep the format to optimize token usage and information density.

Git
Use git to check logs and commit changes for rollback.

Research
Use browser_navigate as default for searches. Use browser tools for web research and documentation.
For detailed browser documentation navigation guidelines, see Browser Documentation Navigation

Workflow
Search codebase before coding. Read relevant files first. Test changes and check linter errors.

Files
Before writing code, check if the file contents where changed, user changed code should be taken into consideration.

Time
Check current date, time and location before searches and when referencing software versions or documentation.

Prompts
Understand prompts contextually. User prompts may contain errors. Interpret intent and correct obvious mistakes when understanding requests.

Questions
User is a senior software engineer. When stuck or unsure, ask the user instead of assuming. User can help diagnose issues and understands context well.

Parallel Agents
Use parallel agents with Git worktrees for independent tasks. Each agent operates in isolated worktree. Use for: independent features, approach comparison, split concerns. Avoid when tasks share files or are tightly coupled. User can request parallel agents by mentioning "parallel agents" in the prompt. Each agent should be able to work independently on different tasks defined by the user.
