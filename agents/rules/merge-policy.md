---
description: Merge strategy policy for main branch
alwaysApply: false
globs:
  - "**/.git/**"
  - "**/PULL_REQUEST*"
  - "**/.github/**"
  - "**/.gitlab/**"
---

<squash_to_main>
Always squash when merging to main. PRs: `gh pr merge --squash`. Local: `git merge --squash branch && git commit`.
</squash_to_main>
