# reports

Static reports hub for this dotfiles repo, served by nginx on Cloud Run. It serves the landing hub,
the agent-eval baseline dashboard, the bash test-coverage report, and the quality writeup. Those
pages are also published to the GitHub Pages site that this service is migrating off of; the live
token-usage view has its own Angular app (`apps/usage-dashboard`) that the hub links out to.

## What it serves

- `/` — the reports hub (`.github/pages/index.html`).
- `/baseline/` — agent-eval pass-rate dashboard (`agents/evals/render_baseline_dashboard.py`).
- `/coverage/` — kcov line coverage for the shell suite (`tests/cover/bash-coverage.sh --ci`).
- `/quality/` — how agent quality is measured (`.github/pages/quality.html`).

The `site/` directory is generated at deploy time by `.github/workflows/reports-deploy.yml`, baked
into the nginx image, and pushed to Cloud Run. It is build output and is not committed.

## Container

`Dockerfile` copies the generated `site/` into nginx. The listen port is templated as `${PORT}`
and rendered by `docker-entrypoint.sh` at start so Cloud Run can inject it. `/health` returns 200.

## Generate the site locally

```
nix shell nixpkgs#kcov nixpkgs#bats nixpkgs#bc --command ./tests/cover/bash-coverage.sh --ci
mkdir -p apps/reports/site/quality
cp .github/pages/style.css apps/reports/site/style.css
cp .github/pages/index.html apps/reports/site/index.html
cp .github/pages/quality.html apps/reports/site/quality/index.html
cp -r tests/coverage apps/reports/site/coverage
python3 agents/evals/render_baseline_dashboard.py apps/reports/site/baseline
```
