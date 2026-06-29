# arr-stack (chise only)

Self-hosted media-automation stack, deployed declaratively to `~/arr-stack/` on
host **chise** only, as a single docker-compose project. It is **down by
default**: nothing starts on boot and no systemd unit ups it. You bring it up
and down by hand.

## Roster

| Service     | Role                      | Local URL                |
| ----------- | ------------------------- | ------------------------ |
| gluetun     | VPN gateway for the torrent client | (no UI)         |
| qbittorrent | download client (via VPN) | http://127.0.0.1:8080    |
| prowlarr    | indexer manager           | http://127.0.0.1:9696    |
| sonarr      | TV                        | http://127.0.0.1:8989    |
| radarr      | movies                    | http://127.0.0.1:7878    |
| lidarr      | music                     | http://127.0.0.1:8686    |
| readarr     | books                     | http://127.0.0.1:8787    |
| bazarr      | subtitles                 | http://127.0.0.1:6767    |

All web UIs publish to `127.0.0.1` only, so they are reachable from chise
itself, not from the LAN. To reach them from another device, tunnel over SSH
(`ssh -L 9696:127.0.0.1:9696 chise`) or expose a port through Tailscale
deliberately.

qBittorrent shares gluetun's network namespace (`network_mode:
service:gluetun`), so all torrent traffic exits through the VPN. The *arr apps
reach qBittorrent at host `gluetun`, port `8080`, on the `arrnet` bridge.

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

## VPN credentials (required by the default stack)

The VPN credentials are stored in **agenix**, never in the public tree. The
encrypted secret is `secrets/credentials/arr-vpn-env.age`; on chise it is
decrypted to `/run/agenix/arr-vpn-env` (owner `zanoni`, mode 400) and loaded
into gluetun via `env_file`.

The shipped secret is a placeholder template. Put your real provider creds in
before the first `up`:

```sh
cd ~/.dotfiles
EDITOR=nvim nix run github:ryantm/agenix -- -e secrets/credentials/arr-vpn-env.age
```

It is a plain `KEY=value` env file consumed by gluetun. A WireGuard example:

```
VPN_SERVICE_PROVIDER=mullvad
VPN_TYPE=wireguard
WIREGUARD_PRIVATE_KEY=<your-key>
WIREGUARD_ADDRESSES=10.0.0.2/32
SERVER_COUNTRIES=Sweden
```

See the gluetun wiki for your provider's exact variables. After editing,
rebuild chise so the new ciphertext is re-decrypted.

## Running without a VPN (optional)

The VPN is the safe default. To run qBittorrent without it, drop the gluetun
service and give qBittorrent its own network and ports. Replace the
`qbittorrent` block with:

```yaml
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: arr-qbittorrent
    restart: "no"
    networks:
      - arrnet
    ports:
      - "127.0.0.1:8080:8080"
      - "127.0.0.1:6881:6881/tcp"
      - "127.0.0.1:6881:6881/udp"
    environment:
      PUID: ${PUID}
      PGID: ${PGID}
      TZ: ${TZ}
      WEBUI_PORT: "8080"
      TORRENTING_PORT: "6881"
    volumes:
      - ${ARR_CONFIG_ROOT}/qbittorrent:/config
      - ${ARR_DATA_ROOT}:/data
```

and delete the `gluetun` service. Without the VPN, the download client's
traffic is no longer tunneled.

## Optional media server

Jellyfin/Jellyseerr are intentionally not shipped: Jellyfin transcoding wants
GPU wiring (chise has an NVIDIA GPU) and Jellyseerr is pointless without a media
server, so neither is "trivial." Add them later as their own compose services
if wanted.
