# reports

Generated reports for this dotfiles repo. The agent-evals report and the bash
test-coverage report are built in CI and published as static artifacts to a public Google Cloud
Storage bucket. The atrium reports app (`@platform/reports`) reads those artifacts at runtime and
frames them under its own chrome, so the hub landing page and the quality writeup now live natively
in atrium rather than being generated here.

## Published artifacts

Two artifacts are published, each under its own prefix in the bucket:

- `reports/baseline/` — the `agent-evals` report (`index.html`, `report.json`, `badge.svg`), copied from the
  committed `agent-harness/quality/evaluations/resultado/` files that `agent-evals relatorio` writes. It is
  published only when those files are present.
- `reports/coverage/` — kcov line coverage for the shell suite, produced by
  `repository/verification/cover/bash-coverage.sh --ci`.

Bucket: `gs://zg-url-shortener-2026-dotfiles-usage-snapshots` (public-read with CORS, defined in
`agent-harness/measurement-and-reporting/infrastructure/usage_snapshots_bucket.tf`). The public object base URL the atrium SPA iframes is
`https://storage.googleapis.com/zg-url-shortener-2026-dotfiles-usage-snapshots/reports/`, so atrium
loads `reports/baseline/index.html` and `reports/coverage/index.html` directly.

The published artifacts are framed chrome-less inside atrium.

## Deploy

`.github/workflows/reports-deploy.yml` runs on push to `main`. It builds the coverage report,
copies the committed `agent-evals` report, assembles `agent-harness/measurement-and-reporting/reports/site/`, then `gcloud storage rsync`s
`site/baseline` and `site/coverage` into the bucket. It does not build a container or deploy to
Cloud Run; the retired nginx-on-Cloud-Run stack was removed.

## Owner actions

The publish step is gated on a GitHub repo Variable and is skipped by default:

```
if: ${{ vars.REPORTS_STATIC_GCS_PUBLISH == 'true' }}
```

Set the repo Variable `REPORTS_STATIC_GCS_PUBLISH` to `true` to enable the GCS publish. This is
owner-only and cannot be set in code. Until it is set, the workflow assembles the site but uploads
nothing, and the atrium baseline and coverage iframes 404 against the bucket.

## Generate the artifacts locally

```
nix shell nixpkgs#kcov nixpkgs#bats nixpkgs#bc --command ./repository/verification/cover/bash-coverage.sh --ci
cp -r repository/verification/coverage agent-harness/measurement-and-reporting/reports/site/coverage
mkdir -p agent-harness/measurement-and-reporting/reports/site/baseline
cp agent-harness/quality/evaluations/resultado/relatorio.html agent-harness/measurement-and-reporting/reports/site/baseline/index.html
cp agent-harness/quality/evaluations/resultado/relatorio.json agent-harness/measurement-and-reporting/reports/site/baseline/report.json
cp agent-harness/quality/evaluations/resultado/badge.svg agent-harness/measurement-and-reporting/reports/site/baseline/badge.svg
```
