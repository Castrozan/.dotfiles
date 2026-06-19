# GCP infrastructure for the dotfiles usage dashboard

Terraform for hosting the dotfiles reports on Google Cloud (project `zg-url-shortener-2026`,
region `southamerica-east1`), mirroring the deploy pattern of the `zg-url-shortener` app.

## What this provisions

- `google_storage_bucket.usage_snapshots` — public-read, CORS-enabled bucket holding the
  anonymized per-machine usage snapshot JSONs that the frontend reads live.
- `google_service_account.usage_snapshot_uploader` — the identity each machine uses to push
  its snapshot to the bucket (`roles/storage.objectAdmin` scoped to the bucket only).
- `google_artifact_registry_repository.dotfiles_apps` — Docker images for Cloud Run.

## State

Remote state lives in `gs://zg-url-shortener-2026-terraform-state` (prefix
`dotfiles-usage-dashboard`). The bucket is bootstrapped once out of band:

```
gcloud storage buckets create gs://zg-url-shortener-2026-terraform-state \
  --project zg-url-shortener-2026 --location southamerica-east1 --uniform-bucket-level-access
```

## Applying

Run from a host authenticated to the project (chise). Provider auth is the existing user
credential, surfaced to Terraform as a short-lived OAuth access token:

```
export GOOGLE_OAUTH_ACCESS_TOKEN=$(gcloud auth print-access-token)
export GOOGLE_PROJECT=zg-url-shortener-2026
terraform init -input=false
terraform plan -input=false
terraform apply -input=false
```

On chise gcloud is reachable via `nix shell nixpkgs#google-cloud-sdk`; Terraform is on PATH.
