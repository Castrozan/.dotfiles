# Historical Angular usage dashboard

The deployed [usage dashboard](https://github.com/Castrozan/lucaszanoni-web/tree/main/apps/usage-dashboard) lives in the site repository.
It reads private D1-backed snapshots through its own authenticated application mount.

This directory retains the earlier Angular and nginx implementation, not the deployed frontend.
Its public Cloud Storage backend and GCS producer are retired; its storage configuration is not a deployment target.
The retained frontend tests describe the original aggregation behavior.

Metadata collection remains in `../usage-collection`; the managed publisher runtime lives in `../claude-telemetry`.
Make frontend and deployment changes in the site repository.
