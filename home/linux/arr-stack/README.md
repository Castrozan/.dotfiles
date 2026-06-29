# arr-stack (chise only)

Self-hosted media-automation stack, deployed declaratively to `~/arr-stack/` on
host **chise** only, as a single docker-compose project. It is **down by
default**: nothing starts on boot and no systemd unit ups it. You bring it up
and down by hand.

## Roster

| Service     | Role                          | Tailnet URL                  |
| ----------- | ----------------------------- | ---------------------------- |
| qbittorrent | download client               | http://100.94.11.81:8080     |
| prowlarr    | indexer manager               | http://100.94.11.81:9696     |
| sonarr      | TV                            | http://100.94.11.81:8989     |
| radarr      | movies                        | http://100.94.11.81:7878     |
| lidarr      | music                         | http://100.94.11.81:8686     |
| readarr     | books                         | http://100.94.11.81:8788     |
| bazarr      | subtitles                     | http://100.94.11.81:6767     |

All web UIs publish to chise's tailscale IP literal `100.94.11.81` only, so they
are reachable from any device on the tailnet but not on the LAN or any other
interface. Open e.g. `http://100.94.11.81:9696` from a tailnet-joined machine.
The *arr apps have no login, so this exposes them to the tailnet (accepted);
qBittorrent keeps its WebUI password.

Readarr's host port is `8788` rather than its default `8787` (chise's cockpit
session bridge already owns `8787` on loopback). Inside the stack Readarr still
listens on `8787`, so other apps reach it at `readarr:8787`.

By default there is no VPN: qBittorrent runs directly on the `arrnet` bridge and
the *arr apps reach it at host `qbittorrent`, port `8080`. Routing the stack
through a VPN is an independent, host-level toggle (see below), not a container
in this stack.

## Bring it up / down

```sh
cd ~/arr-stack
docker compose up -d      # start the whole stack
docker compose ps         # status
docker compose logs -f    # tail logs
docker compose pull       # update images
docker compose down       # stop and remove containers (config/data persist)
```

The compose file, `.env`, and this README are read-only symlinks into the Nix
store. To change the stack, edit the sources under
`home/linux/arr-stack/` in the dotfiles and rebuild chise. Container config and
media persist on disk under the paths below, untouched by rebuilds.

## Persistence

Config and data live under documented host paths (created on rebuild, owned by
`zanoni`), bind-mounted into the containers:

- `~/arr-stack/config/<service>` -> `/config` per app
- `~/arr-stack/data` -> `/data` shared across qBittorrent and the *arr apps,
  laid out as `data/torrents` and `data/media/{tv,movies,music,books}` so
  imports are atomic hardlink moves on one filesystem (no slow copies).

## Optional VPN (off by default, host-level)

The default stack runs with no VPN: qBittorrent talks to the internet directly.
There is no per-container VPN gateway in this stack and nothing to configure here
to get the default behavior.

chise already has host-level NordVPN via `wgnord`, toggled by the packaged
scripts in this repo. Because it is a host-level WireGuard tunnel, turning it on
routes *all* of chise's traffic, the arr-stack containers included, with no
compose changes:

```sh
nord-on-us    # connect NordVPN (US) on chise: wgnord c US
nord-off      # disconnect: wgnord d
```

See `home/base/network/scripts/` (`nord-on-us`, `nord-off`, `nord-on`,
`setup_wgnord`) and `hosts/chise/scripts/` for the script definitions. Bring the
stack up the same way regardless; the VPN is an independent host toggle.

## Optional media server

Jellyfin/Jellyseerr are intentionally not shipped: Jellyfin transcoding wants
GPU wiring (chise has an NVIDIA GPU) and Jellyseerr is pointless without a media
server, so neither is "trivial." Add them later as their own compose services
if wanted.
