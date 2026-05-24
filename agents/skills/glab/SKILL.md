---
name: glab
description: Manage GitLab merge requests, pipelines, and code review. Use when user asks to create/update/merge MRs, read MR comments, check CI status, review code, or interact with GitLab.
---

<announcement>
"I'm using the glab skill to interact with GitLab."
</announcement>

<harness>
Use only "python3 <this skill's scripts/glab-harness.py>" for all GitLab operations. No glab CLI, no curl, no direct API calls. Run '--help' for commands, '<subcommand> --flag --help' for flags. Handles auth, project resolution, host selection, and URL encoding. Descriptions take '--description-file' (file path), not inline strings. Use 'delete-branch' instead of 'git push --delete' (protected branches reject silently).
</harness>

<hosts>
The harness derives the GitLab host from the current repo's 'origin' remote. Two hosts are supported side by side during the in-progress migration from 'git.coates.io' to 'gitlab.com': 1) 'git.coates.io', legacy Coates self-hosted (ca3, dps v2, mcdca-workspace, etc), token from '~/.secrets/glab-token' or 'GITLAB_TOKEN' env var; 2) 'gitlab.com', new home of 'coates/mcd-ca/*' (shell, archiver, dps v1, more migrating), token from '~/.secrets/gitlab-com-token' or 'GITLAB_COM_TOKEN' env var. Run from inside the target repo, the harness picks the right host and token automatically.
</hosts>

<user_events>
`user-events` is the one subcommand that runs outside a git repo; it queries `/events` for the authenticated user and returns a JSON map keyed by host. Use it for cross-repo activity pictures (daily report, blocker triage, sprint review).
</user_events>
