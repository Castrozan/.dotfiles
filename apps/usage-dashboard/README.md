# usage-dashboard

Live front end for the dotfiles token-usage reports. Angular 21 (zoneless, standalone,
signals) styled with Tailwind v4, served by nginx on Cloud Run, mirroring the deploy pattern
of the `zg-url-shortener` app.

## What it does

The browser lists the anonymized per-machine snapshot objects in the public Cloud Storage
bucket (`zg-url-shortener-2026-dotfiles-usage-snapshots`, prefix `snapshots/`), fetches each
one, and aggregates them client-side into the per-account view, daily-token chart, OpenTelemetry
token-stream panel and per-account table. It re-fetches on a fixed interval so the page is live
rather than a frozen build-time snapshot.

The aggregation is a faithful port of the Python aggregation in
`agents/usage/usage_otel_metrics_aggregation.py`; the unit tests pin that contract. This Angular
app is now the usage front end, replacing the retired GitHub Pages report.

## Structure

- `src/app/models` — snapshot JSON and aggregated view-model types.
- `src/app/services/usage-aggregation` — the pure aggregation port, split by concern.
- `src/app/services/usage-snapshot-client.service.ts` — lists and fetches snapshots from GCS.
- `src/app/shared/token-formatting.ts` — token/percent formatting helpers.
- `src/app/components` — presentational components plus the live dashboard container.

## Develop

```
npm install
npm start            # ng serve, http://localhost:4200
npm test             # vitest unit tests
npx ng build --configuration=production
```

## Container

`Dockerfile` builds the app and serves `dist/usage-dashboard/browser` from nginx. The listen
port is templated as `${PORT}` and rendered by `docker-entrypoint.sh` at start so Cloud Run can
inject it. `/health` returns 200.
