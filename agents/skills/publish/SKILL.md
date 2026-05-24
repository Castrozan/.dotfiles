---
name: publish
description: Cut release MRs (UAT, prod). Encodes the squash-merge base-selection trap that produces inflated diffs. Use when preparing a release branch or deploy MR.
---

<announcement>
"I'm using the publish skill to prepare a release."
</announcement>

<flow>
Two MRs per release: 1) `develop` → `release/<date-stamped>` titled per the project's prior convention — merging triggers the UAT pipelines; 2) after UAT sign-off, `release/<date-stamped>` → `main` titled per the project's "merge to production" convention. Inspect the most recent merged release MRs in the repo before authoring to copy the exact title format and branch naming (date order, separator, prod vs uat prefix vary by project). Use a git worktree for the release branch so the active feature checkout stays untouched.
</flow>

<base_selection_trap>
The release branch's base commit determines whether the resulting MR shows the actual release content or an inflated diff of everything since branches diverged. If prior release MRs were squash-merged into main (single-parent commits named like "Release UAT ..." in main's history), develop's actual commits are orphaned from main's lineage and `git merge-base develop main` falls back to init; branching off main produces hundreds of commits and files in the MR even when the real delta is small. The same trap applies when prior release branches squash-merge develop in turn, because the synthetic squash commit is not on develop's ancestry. Fix: walk `git log --merges --first-parent develop` from HEAD until you find the merge commit on develop just before this release's new tickets — that commit is the base. Verify with `git log base..develop` and `git diff --name-only base..develop`; commit and file counts should match the new tickets, not the full divergence. If the numbers still look inflated, the base is wrong — keep walking.
</base_selection_trap>

<reviewers_default>
Do not mark reviewers on release MRs unless explicitly told to. The team picks reviewers during sign-off, not at MR creation.
</reviewers_default>

<description_format>
List the tickets in scope with one-line summaries. Call out manual steps required on merge that the pipeline does not cover: lambda redeploys, SQL migrations applied live, AWS notification configs, env-specific config updates. Link the source-of-truth Jira tickets; do not copy ticket descriptions into the MR body.
</description_format>
