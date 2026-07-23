# reports

Generated reports for this dotfiles repo. The agent-eval baseline dashboard and the bash
test-coverage report are built in CI and published as static artifacts to a public Google Cloud
Storage bucket. The atrium reports app (`@platform/reports`) reads those artifacts at runtime and
frames them under its own chrome, so the hub landing page and the quality writeup now live natively
in atrium rather than being generated here.

## Published artifacts

Three artifacts are published, each under its own prefix in the bucket:

- `reports/baseline/` — agent-eval pass-rate dashboard, rendered by
  `agents/evals/render_baseline_dashboard.py` from the git history of `agents/evals/baseline.json`.
- `reports/coverage/` — kcov line coverage for the shell suite, produced by
  `__tests__/cover/bash-coverage.sh --ci`.
- `reports/quality/metrics.json` — the live counts the atrium quality writeup renders, derived by
  `agents/evals/render_quality_metrics.py` straight from the repo: static-eval suite size and pass
  rate, integration and e2e scenario counts, `core.md` line and rule-block counts, and the wired
  hook events. The narrative on that page is hand-written; every number in it comes from this file,
  so the page cannot drift from the repo the way the hand-maintained copy did.

Bucket: `gs://zg-url-shortener-2026-dotfiles-usage-snapshots` (public-read with CORS, defined in
`infra/gcp/usage_snapshots_bucket.tf`). The public object base URL the atrium SPA iframes is
`https://storage.googleapis.com/zg-url-shortener-2026-dotfiles-usage-snapshots/reports/`, so atrium
loads `reports/baseline/index.html` and `reports/coverage/index.html` directly.

The published artifacts are framed chrome-less inside atrium: the baseline dashboard no longer
carries its own top nav, and its remaining cross-links point at absolute atrium routes with
`target="_top"` so they escape the iframe.

## Deploy

`.github/workflows/reports-deploy.yml` runs on push to `main`. It builds the coverage report,
renders the baseline dashboard, assembles `apps/reports/site/`, then `gcloud storage rsync`s
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
nix shell nixpkgs#kcov nixpkgs#bats nixpkgs#bc --command ./__tests__/cover/bash-coverage.sh --ci
mkdir -p apps/reports/site/quality
cp -r __tests__/coverage apps/reports/site/coverage
python3 agents/evals/render_baseline_dashboard.py apps/reports/site/baseline
cp .github/pages/style.css apps/reports/site/baseline/style.css
python3 agents/evals/render_quality_metrics.py apps/reports/site/quality/metrics.json
```
