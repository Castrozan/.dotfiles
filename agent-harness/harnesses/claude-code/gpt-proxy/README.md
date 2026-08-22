# claudex: Claude Code on a ChatGPT subscription

Runs Claude Code against a ChatGPT/Codex subscription instead of Anthropic billing,
by bridging the Anthropic Messages API through a local
[CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI) instance.

Scoped to the hosts in `hostsWithClaudex` (currently `chise`, `kira`, and `rin`), with
packaged CLIProxyAPI binaries for x86_64 Linux and Apple silicon macOS.

## What this module provides

- `cli-proxy-api`: the pinned proxy binary for each supported platform.
- A managed service that keeps the proxy listening on `127.0.0.1:8317`, reading a
  read-only nix-store `config.yaml` and booting from the embedded model catalog
  (`--local-model`, so boot is offline-deterministic). Its upstream requests use a
  loopback CONNECT gateway that resolves and dials IPv4 only, avoiding blackholed
  temporary IPv6 routes while leaving the machine's IPv6 configuration untouched.
- `claudex`: launches Claude Code pointed at the proxy. It forces the main loop to
  `gpt-5.6-sol(max)[1m]` with `--model` (the shared `settings.json` pins a concrete
  Opus model slug (see `global-settings.nix`) that would otherwise bypass the opus-alias remap), and maps the
  sonnet/haiku alias tiers to `gpt-5.6-sol` at medium/low effort for subagent and
  background traffic. A `--model` you pass yourself still wins.
- `claudex-login`: the one-time interactive OAuth step.

## One-time setup

The proxy boots with zero credentials (it just returns 502 until authenticated). Log in once:

```
claudex-login
```

This opens a browser OAuth flow (callback on `127.0.0.1:1455`), writes the subscription
credential under `~/.cli-proxy-api/`, and reloads the proxy. The proxy's file watcher also
hot-reloads that directory, so re-logins take effect without a rebuild. Then:

```
claudex
```

## Where things live

- Credentials: `~/.cli-proxy-api/codex-<email>-<plan>.json`
- Logs: `~/.local/state/cli-proxy-api/cli-proxy-api.log`
- Service: `launchctl print gui/$(id -u)/com.dotfiles.cli-proxy-api`

## Tuning

Change the `gptModelFor*Tier` bindings to swap model or effort. The proxy is open on the
loopback interface (`api-keys: []`), so `ANTHROPIC_AUTH_TOKEN` in the launcher is a
placeholder the proxy ignores. The haiku tier maps to `gpt-5.6-sol(low)`; every background
Claude Code call spends subscription usage, so lower it to a cheaper Codex slug if that
matters.

Anthropic bans subscription-key reuse through gateways; this bridges a _ChatGPT_
subscription, which OpenAI tolerates. Do not point the same pattern at an Anthropic
subscription.
