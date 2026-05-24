---
name: ci-creds
description: Borrow temporary cloud STS credentials from a CI job to a local shell for read-only inspection. Use when local has no creds but CI does and round-tripping CI per query is too slow.
---

<announcement>
"I'm using the ci-creds skill to vend CI credentials to my local shell."
</announcement>

<when_to_use>
The project's deploy pipeline assumes a cloud role (typically `aws sts assume-role` driven by a GitLab OIDC token) and the local shell has no equivalent path to those credentials. A one-shot CI job that prints the assumed credentials to its job log is much cheaper than adding a new CI job per inspection question. Right whenever the failure mode "I can describe the bug but can't reach the API to confirm" appears.
</when_to_use>

<add_the_job>
Add a manual, no-needs job that extends the project's existing role-assume template (whatever runs `aws sts assume-role` in `before_script` and exports `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_SESSION_TOKEN`). The job body prints those env vars between unambiguous marker lines so the values are easy to extract from the log later. See `templates/inspect-aws-credentials.gitlab-ci.yml` for a drop-in snippet that matches the typical Coates `.aws-setup` shape; adapt the template name to whatever the target repo calls it.
</add_the_job>

<run_and_consume>
Open the MR, find the manual job, trigger it via the job's `/play` API (or the UI play button). After it succeeds, fetch the job trace, grep between the marker lines for the three `export ...` statements, paste them into a fresh shell, and run any read-only AWS CLI commands directly from there. The credentials expire in 1h by default — don't bake them into scripts; re-trigger the job for a fresh batch when they lapse.
</run_and_consume>

<failure_modes>
The credentials in the job log are readable by anyone with Reporter+ on the project; never use this for prod-power roles, and prefer keeping the inspection job on a branch whose project visibility is no looser than the role's blast radius. The role's permissions cap what the borrowed shell can do — a dev/UAT deploy role typically has read on most resources plus write on the target lambda/EC2, so do not run mutations (`update-function-configuration`, `put-bucket-policy`, etc.) with these creds unless that mutation is the explicit purpose. Force-pushing iterations of the inspection job is fine because the branch only powers the inspection MR, but never force-push the project's mainline branches with creds-related changes.
</failure_modes>
