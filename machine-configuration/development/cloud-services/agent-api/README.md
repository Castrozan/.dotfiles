# Private agent capability API

`agent-api` extends the media APIs with one discover/inspect/run interface. The CLI and optional HTTP transport share a
Python service, JSON Schemas and durable operation store. Provider credentials and subprocesses stay inside adapters. It
runs on demand on NixOS and Darwin; installation starts no daemon and adds no per-agent MCP process.

```sh
agent-api providers
agent-api discover transcribe
agent-api discover --provider media
agent-api inspect audio.transcribe
agent-api run web.extract --input '{"url":"https://example.com"}'
agent-api run web.search --input '{"query":"Crawl4AI documentation","limit":3}'
agent-api run audio.transcribe --input-file transcription.json
agent-api operation OPERATION_UUID
agent-api directives
agent-api direct compute.placement local
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
access; actual availability and rate limits remain upstream conditions. This adapter uses anonymous access only and does
not read account credentials. Rate limits and failures never trigger an account-billed fallback.

Account-billed operations require `--allow-paid` or HTTP `allow_paid: true`. This grants account use, not a price
reservation or dollar cap. The gateway does not create accounts, provision keys, buy credits or switch providers after
failure. API credentials and billing remain separate from agent harness subscriptions.

## Programmatic crawling

`web.crawl` runs Scrapy over HTTP without opening or connecting to a browser. It follows links only within the starting
URL's exact origin, including scheme and port. Supply the final HTTPS URL when a site redirects from HTTP. It respects
robots.txt, disables cookies, proxies and retries, and downloads one response at a time with a 250 ms delay.

```sh
agent-api run web.crawl --input '{"url":"https://docs.scrapy.org/en/2.13/","max_pages":5,"max_depth":1}'
```

The default is ten distinct page targets and two link levels below the starting page. `max_pages` accepts 1 through 50;
`max_depth` accepts 0 through 5. Failed or robots-excluded targets consume page slots. Robots and redirects can add HTTP
requests; redirects are limited to five hops and cannot leave the origin. Each response is limited to 1 MiB, and the
operation uses the gateway's existing deadline. JavaScript is not executed.

Optional `extraction` defines a CSS `item_selector` and named CSS expressions in `fields`:

```json
{
  "url": "https://example.com/catalogue",
  "max_pages": 1,
  "extraction": {
    "item_selector": "article.product",
    "fields": { "title": "h2::text", "link": "a::attr(href)" }
  }
}
```

Each field returns its first match as a string, or null when absent. Relative links remain relative to that page's URL.
Extraction accepts at most 20 fields, 1,000 records per page and 16,384 characters per field; oversized extraction is
reported as a page error. Page content and extracted records are retained in `crawl.jsonl`, one JSON object per page.
The receipt returns page summaries, errors and the artifact name. Partial crawls expose their failed pages; a crawl with
no successful pages fails. Successful replay reads the retained artifact without fetching the site again.

## Durable operations and limits

State defaults to `$XDG_STATE_HOME/agent-api`, or `~/.local/state/agent-api`. Its directory requires mode 0700. Each
canonical UUID claims one operation transactionally in SQLite. Successful identical requests replay without a worker or
provider preflight, after checking retained artifact checksums. Changed requests conflict. Running, failed and
interrupted UUIDs cannot submit again. Deadlines and payment permission are part of request identity.

The API permits two active jobs per state directory, 1–600 seconds per job, 64 KiB of request JSON, 4 MiB of result JSON
and 512 MiB of retained artifacts per operation. Workers run in separate process groups; deadline cleanup interrupts
them, then kills an unresponsive group after five seconds. Expired leases release concurrency slots and mark operations
interrupted without resubmitting them. Retention is persistent; this interface does not delete old jobs.

Media child IDs are recorded before dispatch. A local timeout does not cancel a cloud job or establish that it was free.
Inspect the retained operation and its media child receipt before deciding how to recover. The gateway never retries
submission.

## Directives

A directive is a standing order with a fixed target set, chosen by the user. When a capability's entry names a directive
and the request leaves the governed input out, the service fills that input with the directive's current target before
the operation is claimed. An explicit input value always wins. The first directive, `compute.placement`, governs the
`host` input of `compute.submit`; its targets are the inventory hosts and its default is `local`.

```sh
agent-api directives
agent-api direct compute.placement <host>
```

`directives` lists every directive with its targets and current target, and creates no state. `direct` accepts only a
target from the inventory; any other target fails with `unsupported_target` and leaves the previous target in place.
Choices are stored in `directives.json` in the state directory. That file is per machine; nothing synchronises it
between machines.

The resolved target is part of the request identity, so replaying one UUID after its directive moved conflicts. A
stored target that has left the inventory fails with `unsupported_target` instead of falling back to the default.
Discovery shows which directive governs each capability. The HTTP transport does not expose directives.

## Remote compute

`compute.hosts` lists the compute hosts with their system, size and trust tier, and contacts none of them.
`compute.submit` starts a command as a resource-limited job on a host and returns at once. `compute.status`,
`compute.logs` and `compute.cancel` take the `job` returned by submit, which is the submit operation's UUID.

```sh
agent-api run compute.submit --input '{"command":["nix","run","nixpkgs#hello"]}'
agent-api run compute.status --input '{"job":"<submit operation UUID>"}'
agent-api run compute.logs --input '{"job":"<submit operation UUID>"}'
agent-api run compute.cancel --input '{"job":"<submit operation UUID>"}'
```

Each job runs as the transient user unit `agent-api-<uuid>.service` on its host, with `MemoryMax`, `CPUQuota` and
`RuntimeMaxSec` set from the request. Defaults are 2048 MiB, 100 percent of one core and 3600 seconds; the accepted
ranges are 64 to 65536 MiB, 10 to 6400 percent and 1 to 86400 seconds. Tools that size their parallelism from the
cgroup quota see one core at the default, so a build needs `cpu_percent` raised to use more. The job's runtime limit is
separate from the 1 to 600 second deadline of the submit operation itself, which bounds that operation alone.

Arguments reach the job verbatim. The `local` host runs no shell, remote arguments are shell-quoted before ssh sends
them, and the unit is created with environment expansion disabled. The job inherits the user manager's environment, not
the caller's, so it brings its own tools through `nix shell` or `nix run`. The `local` host needs `systemd-run`; where
it is absent, including Darwin, submit to `local` fails with `unsupported_host`.

Remote hosts come from the JSON file named by `AGENT_API_COMPUTE_INVENTORY`: an array of at most 32 objects with
`name`, `ssh_alias`, `system` and `trust` (`owned` or `rented`), plus optional `cores` and `memory_gigabytes`. Other
keys are rejected. Names are lowercase, unique and never `local`. A host is reached as
`ssh -o BatchMode=yes -o ConnectTimeout=10 <ssh_alias> -- <quoted command>`. Nothing is copied to a host yet, so
`directory` must already exist there.

Job state lives in the host's systemd user manager. A finished job stays inspectable until `compute.cancel` releases
its unit, after which status reports `unknown`. Status reports `running`, `succeeded`, `failed` or `unknown`, with the
exit code once the job has finished. Logs return the last `lines` journal lines (default 200, at most 2000), keeping at
most 262,144 characters from the end, so the escaped result stays under the 4 MiB result limit.

Status, logs and cancel find the host from the retained submit request, not from the current directive. The gateway
never retries a submit.

## Private HTTP transport

```sh
agent-api serve
curl --unix-socket "$HOME/.local/state/agent-api/api.sock" http://localhost/v1/capabilities
curl --unix-socket "$HOME/.local/state/agent-api/api.sock" http://localhost/openapi.json
```

The server binds only a Unix socket inside a private directory. Access grants the same file and provider capabilities as
the CLI; it is intended for processes owned by the same user. It has no TCP listener. Invoke the CLI through existing
SSH access for another machine. No socket replacement, service installation or network exposure happens implicitly. A
stopped server can leave its socket path; remove that stale socket before starting it again.

Use `PUT /v1/operations/{uuid}` with `capability`, `input`, optional `timeout_seconds` and optional `allow_paid`.
`GET /v1/operations/{uuid}` returns state and receipts. Successful retained files are available at
`GET /v1/operations/{uuid}/artifacts/{filename}`. `/docs` and `/openapi.json` expose the transport contract.
