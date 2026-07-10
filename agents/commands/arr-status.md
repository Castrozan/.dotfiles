---
description: Show request and download status for media on the arr-stack, one line per request
argument-hint: [optional title substring, e.g. "slime"]
---

Report media request status with the `arr-status` CLI. Run `arr-status` for every request, or `arr-status <title>` to filter by a case-insensitive substring of the title. Carry out: $ARGUMENTS

<output>
One line per request as `title (year) <tab> type <tab> requested-by <tab> stage`. The stage is the Jellyseerr lifecycle: `pending-approval`, `declined`, `processing`, `partial`, or `available`. When Radarr or Sonarr has an active grab for that title, the stage is annotated with live progress, e.g. `partial | downloading 33% ETA 00:09:58`, with the ETA taken from the slowest record in the queue. Summarize the lines for the user, leading with anything still downloading or awaiting approval.
</output>

<architecture>
The request lifecycle comes from Jellyseerr on 127.0.0.1:5055 (apiKey from its settings.json). Live download progress comes from Radarr (7878) and Sonarr (8989), whose API keys are read from each app's config.xml and whose base URL is built from the tailnet `ARR_BIND_ADDR` in `~/arr-stack/.env` at runtime, so no tailnet address is hardcoded. A request is matched to a queue item by resolving its Jellyseerr tmdbId to a Radarr movieId, or its tvdbId to a Sonarr seriesId, then summing size across that id's queue records. Movies come from Radarr, everything TV from Sonarr.
</architecture>

<traps>
The on-demand supervisor stops Radarr, Sonarr, and qBittorrent when the download chain is idle, so their queues are unreachable between jobs. That is not an error: `arr-status` still prints every request from Jellyseerr, and a `processing` item with the chain down reads `processing (download chain idle)` rather than failing. Only Jellyseerr being unreachable is a hard error (exit 1). A `partial` stage means some but not all episodes have landed, common for a still-airing season, and it may or may not have an active grab depending on whether new episodes are out.
</traps>
