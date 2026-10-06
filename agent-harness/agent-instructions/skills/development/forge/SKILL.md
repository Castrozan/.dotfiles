---
name: forge
description: Manage pull requests, merge requests, reviews and hosted CI using the repository's Git hosting provider.
---

### Repository context

Run `git-forge` to resolve the effective upstream before a hosting operation; read its help for explicit targets. Git
URL rewrites and the branch's upstream decide the host; a configured default CLI host can point at another account. Use
the resolved repository URL explicitly for native commands. An unsupported host or authentication error is unresolved
access, never an empty result.

### Native operations

Use the provider's native CLI and its API command for missing operations. Read installed command help before choosing
flags. Load provider-specific plugins only for a repository on that provider; take branch conventions, request templates
and required checks from the consuming workspace. GitHub calls a proposal a pull request; GitLab calls it a merge
request.

### Review conversations

Reply within the existing review discussion and verify the complete published text. Preserve the workspace's approval
and merge gates regardless of the hosting provider. Authentication already supplied by the environment or machine
configuration needs no new login flow.

### Continuous integration

Use the [CI watcher](../ci-watcher/SKILL.md) for hosted verdicts and retained job evidence. A successful local build,
missing pipeline, CLI error or unfinished run does not establish remote success.
