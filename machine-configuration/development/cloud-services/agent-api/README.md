# Private agent capability API

`agent-api` extends the media APIs with one discover/inspect/run interface. The CLI and optional HTTP transport share a
Python service, JSON Schemas and durable operation store. Provider credentials and subprocesses stay inside adapters.
It runs on demand on NixOS and Darwin; installation starts no daemon and adds no per-agent MCP process.

```sh
agent-api providers
agent-api discover transcribe
agent-api discover --provider monid
agent-api inspect audio.transcribe
agent-api run web.extract --input '{"url":"https://example.com"}'
agent-api run web.search --input '{"query":"Crawl4AI documentation","limit":3}'
agent-api run audio.transcribe --input-file transcription.json
agent-api operation OPERATION_UUID
```

Discovery returns compact descriptions; inspect returns the selected input schema. Neither executes providers or creates
operation state. `media.providers` reads existing media model catalogs, and `movie.schema` reads the scene contract.
Image, speech, movie and native video operations call the existing public CLIs with the gateway's UUID as their child
operation ID. Existing direct consumers keep their interfaces and state.

Local extraction uses Trafilatura, downloads use yt-dlp or HTTP, audio/video inspection and conversion use FFmpeg,
transcription uses whisper.cpp, and document conversion uses Pandoc. These local paths have no provider fee; hardware,
network and electricity still cost resources. Trafilatura does not execute JavaScript. Pandoc's supported readers are
listed in the capability schema; PDF conversion is not included. yt-dlp's site support changes upstream; some sites
require authentication or a JavaScript runtime. This API does not import browser cookies or install model weights.

For transcription, supply absolute `path` and `model_path` values and optionally `language`. An English-only `.en.`
Whisper model requires `language: "en"`; other models can use `auto`. Output includes retained WAV, JSON, text and SRT.
Input files must be owned regular files with canonical absolute paths, at most 512 MiB. Their checksums participate in
operation identity, so replacing a file at the same path conflicts with successful replay.

Firecrawl provides cloud search and rendered-page extraction. Its documentation describes limited unauthenticated
access; actual availability and rate limits remain upstream conditions. An optional `FIRECRAWL_API_KEY` or
`~/.secrets/firecrawl-api-key` uses your account and requires explicit payment permission.

Monid is an established provider gateway. Its discovery and inspection APIs supply live endpoint schemas, documentation
and prices; this API wraps those rather than implementing another connector engine. Use `monid.discover`, then
`monid.inspect`, then `monid.run` with the returned provider, endpoint and input. Credentials come from `MONID_API_KEY`
or `~/.secrets/monid-api-key`. Discovery and inspection are free upstream; execution is priced by endpoint.
See [Monid documentation](https://docs.monid.ai/) and [its connector engine](https://github.com/monid-ai/monid).

fal offers image, video, audio and 3D models through a durable queue. `fal.run` accepts a documented model endpoint and
its provider-specific input object. It returns the provider result, including hosted asset URLs. Model schemas and
pricing remain in the [fal queue documentation](https://fal.ai/docs/documentation/model-apis/inference/queue).
Use `web.download` to retain a
hosted artifact separately. Credentials come from `FAL_KEY` or `~/.secrets/fal-api-key`. Hosted result URLs can expire.

Account-billed operations require `--allow-paid` or HTTP `allow_paid: true`. This grants account use, not a price
reservation or dollar cap. The gateway does not create accounts, provision keys, buy credits or switch providers after
failure. API credentials and billing remain separate from agent harness subscriptions.

## Durable operations and limits

State defaults to `$XDG_STATE_HOME/agent-api`, or `~/.local/state/agent-api`. Its directory requires mode 0700. Each
canonical UUID claims one operation transactionally in SQLite. Successful identical requests replay without a worker
or provider preflight, after checking retained artifact checksums. Changed requests conflict. Running, failed and
interrupted UUIDs cannot submit again. Deadlines and payment permission are part of request identity.

The API permits two active jobs per state directory, 1–600 seconds per job, 64 KiB of request JSON, 4 MiB of result JSON
and 512 MiB of retained artifacts per operation. Workers run in separate process groups; deadline cleanup interrupts
them, then kills an unresponsive group after five seconds. Expired leases release concurrency slots and mark operations
interrupted without resubmitting them. Retention is persistent; this interface does not delete old jobs.

Provider submission IDs are recorded before polling; media child IDs are recorded before dispatch. A local timeout
does not cancel a cloud job or establish that it was free. Inspect the failed operation, then use `monid.result` or
`fal.result` to retrieve its existing remote result. These reads never submit generation again. fal itself can retry
work inside its queue; the gateway never retries submission. Monid's completed run status is checked separately from
the underlying provider HTTP status.

## Private HTTP transport

```sh
agent-api serve
curl --unix-socket "$HOME/.local/state/agent-api/api.sock" http://localhost/v1/capabilities
curl --unix-socket "$HOME/.local/state/agent-api/api.sock" http://localhost/openapi.json
```

The server binds only a Unix socket inside a private directory. Access grants the same file and provider capabilities
as the CLI; it is intended for processes owned by the same user. It has no TCP listener. Invoke the CLI through existing
SSH access for another machine. No socket replacement, service installation or network exposure happens implicitly.
A stopped server can leave its socket path; remove that stale socket before starting it again.

Use `PUT /v1/operations/{uuid}` with `capability`, `input`, optional `timeout_seconds` and optional `allow_paid`.
`GET /v1/operations/{uuid}` returns state and receipts. Successful retained files are available at
`GET /v1/operations/{uuid}/artifacts/{filename}`. `/docs` and `/openapi.json` expose the transport contract.
