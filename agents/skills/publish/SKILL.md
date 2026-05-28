---
name: publish
description: Cut releases (UAT, prod). Detects whether the project uses tag-based deploys or the legacy release-branch + two-MR flow. Use when preparing a deploy.
---

<announcement>
"I'm using the publish skill to prepare a release."
</announcement>

<detect_flow>
Before doing anything, inspect `.gitlab-ci.yml` (and any included files under `.gitlab/`) to detect which flow this project uses.

**Tag-based flow** (current MCAD, DPS v2): the workflow rules gate prod and UAT on tags matching `v\d+\.\d+\.\d+` and `v\d+\.\d+\.\d+-rc\d*`. There are no long-lived `release/*` branches. `main` is read-only and auto-mirrored by a `sync:main` CI job after prod deploy. Recent tags on origin exist (`git ls-remote --tags origin`) and recent commits on main are CI-only.

**Legacy two-MR flow**: no tag rules in CI. Releases are cut via `develop → release/<date> → main` merges. Recent commits on main are merge commits like `Merge branch 'release/...' into 'main'`. Release branches like `release/<date-stamped>` appear in `git branch -r`.

If you can't tell, ask the user before proceeding.
</detect_flow>

<tag_based_flow>
Use this section if `detect_flow` identified tag-based deploys.

**Tag patterns:**
- UAT: `v<major>.<minor>.<patch>-rc<N>` (e.g. `v1.2.0-rc1`)
- Prod: `v<major>.<minor>.<patch>` no suffix (e.g. `v1.2.0`)

**Source commit:**
- RC tag: tag `develop` HEAD (or the specific develop commit being released)
- Prod tag: tag the **same commit** as the RC that was UAT-validated. Do not retag a later commit unless explicitly told to — that bypasses UAT validation

**Steps:**
1. Decide the version. Read the existing tags (`git ls-remote --tags origin`) to determine the next semver bump. Features → minor; fixes only → patch; breaking changes → major. Ask the user when uncertain — version choice is not derivable from code
2. Confirm with the user before pushing any tag — the tag IS the deploy trigger
3. `git tag -a vX.Y.Z[-rcN] <commit> -m "..."` with an annotated message that lists the scope
4. `git push origin vX.Y.Z[-rcN]`
5. The CI pipeline will pause at the GitLab protected env approval gate (uat or prod). A Maintainer must approve before the infra deploy runs
6. After successful prod deploy, the `sync:main` job auto-pushes the tagged commit to `main` via `CI_JOB_TOKEN`. Never push to `main` manually

**Tag message format:** one-line summary, blank line, bullet list of tickets/scope, blank line, manual post-deploy steps if any (lambda redeploys, SQL migrations, AWS notification configs, env updates).

**Source identification when commits are confusing:** if a release branch was used historically (transitional project), the most recent UAT-validated commit may live on a `release/*` branch rather than develop. The commit currently tagged `v<X>.<Y>.<Z>-rc<N>` is authoritative — tag prod from that same SHA.
</tag_based_flow>

<legacy_two_mr_flow>
Use this section if `detect_flow` identified the legacy flow.

Two MRs per release: 1) `develop` → `release/<date-stamped>` titled per the project's prior convention — merging triggers the UAT pipelines; 2) after UAT sign-off, `release/<date-stamped>` → `main` titled per the project's "merge to production" convention. Inspect the most recent merged release MRs in the repo before authoring to copy the exact title format and branch naming (date order, separator, prod vs uat prefix vary by project). Use a git worktree for the release branch so the active feature checkout stays untouched.

<base_selection_trap>
The release branch's base commit determines whether the resulting MR shows the actual release content or an inflated diff of everything since branches diverged. If prior release MRs were squash-merged into main (single-parent commits named like "Release UAT ..." in main's history), develop's actual commits are orphaned from main's lineage and `git merge-base develop main` falls back to init; branching off main produces hundreds of commits and files in the MR even when the real delta is small. The same trap applies when prior release branches squash-merge develop in turn, because the synthetic squash commit is not on develop's ancestry. Fix: walk `git log --merges --first-parent develop` from HEAD until you find the merge commit on develop just before this release's new tickets — that commit is the base. Verify with `git log base..develop` and `git diff --name-only base..develop`; commit and file counts should match the new tickets, not the full divergence. If the numbers still look inflated, the base is wrong — keep walking.

A related trap appears when the repo was migrated between hosts (e.g. a `Merge git.coates.io develop` commit grafts old history). In that case commit counts will be inflated regardless of base — use `git diff --shortstat` (file/line delta) and the list of `feat:`/`fix:` commits to gauge real scope instead.
</base_selection_trap>
</legacy_two_mr_flow>

<reviewers_default>
Do not mark reviewers on release MRs unless explicitly told to. The team picks reviewers during sign-off, not at MR creation.
</reviewers_default>

<description_format>
List the tickets in scope with one-line summaries. Call out manual steps required on merge that the pipeline does not cover: lambda redeploys, SQL migrations applied live, AWS notification configs, env-specific config updates. Link the source-of-truth Jira tickets; do not copy ticket descriptions into the MR body. Same format applies to annotated tag messages in the tag-based flow.
</description_format>
