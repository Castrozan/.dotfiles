# arr-stack (chise only)

Self-hosted media-automation stack, deployed declaratively to `~/arr-stack/` on
host **chise** only, as a single docker-compose project. The front ends
(Jellyfin, Jellyseerr) run under `restart: unless-stopped`, so they start on boot
and self-heal. The download chain (qBittorrent and the *arr apps) stays
`restart: "no"` and is driven by the on-demand supervisor
(`arr-stack-on-demand-supervisor`): it comes up when a Jellyseerr request needs
fulfilling and idles down after a grace, or stays resident when
`keepChainAlwaysOn` is set, as it is on chise. A drive-guard stops the stack the
instant its data drive disconnects and brings the front ends back when it
reconnects. You can still drive it by hand with `docker compose` (below).

## Roster

| Service     | Role                          | Tailnet URL     |
| ----------- | ----------------------------- | --------------- |
| jellyfin    | media server / watch UI       | http://arr:8096 |
| jellyseerr  | browse and request front end  | http://arr:5055 |
| qbittorrent | download client               | http://arr:8080 |
| prowlarr    | indexer manager               | http://arr:9696 |
| sonarr      | TV                            | http://arr:8989 |
| radarr      | movies                        | http://arr:7878 |
| bazarr      | subtitles                     | http://arr:6767 |

Jellyfin is the Netflix-style page for watching the library; Jellyseerr is the
browse-and-request front end wired to Radarr/Sonarr. Reach each service directly at
its tailnet URL from any tailnet device, e.g. `http://arr:8096` for Jellyfin on chise
(where `arr` is a hostname alias to chise's tailscale IP) or via chise's MagicDNS name.

All web UIs publish only to chise's tailscale IP, which the `arr` alias resolves
to, so they are reachable from any device on the tailnet but not on the LAN or any
other interface. Open e.g. `http://arr:9696` from a tailnet-joined machine.
The *arr apps have no login, so this exposes them to the tailnet (accepted);
qBittorrent keeps its WebUI password.

The stack covers TV and movies only. Lidarr (music) and Readarr (books) were
removed: neither library was ever used, and Readarr was archived upstream on
2025-06-27 with no maintained successor.

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
  laid out as `data/torrents` and `data/media/{tv,movies,tv-private,movies-private}`
  so imports are atomic hardlink moves on one filesystem (no slow copies).

## Private libraries friends cannot see

`data/media/movies-private` and `data/media/tv-private` back two Jellyfin
libraries, `Movies (Private)` and `TV (Private)`, that only administrators can
see. Friends are pinned to `EnableAllFolders: false` with the public `Movies` and
`TV` libraries as their entire `EnabledFolders` list, so a private title is
invisible in their Jellyfin: not in browse, not in search, not playable by direct
item id. The libraries stay out of Jellyseerr's synced-library list too, so a
private title is never announced there as available.

The split is code, not clicks. `scripts/arr_users/jellyfin_library_declaration.py`
is the single source of truth: anything not named in `PUBLIC_LIBRARY_DECLARATIONS`
is private, so a library added later is hidden from friends by default and has to
be declared public deliberately. The `jellyfin-library-access-provisioner` systemd
unit re-applies the whole boundary on every rebuild, creating any declared library
that is missing and rewriting every non-administrator policy; `arr-users sync`
runs the same reconcile by hand. Both refuse to write a policy at all when a
declared public library is missing from Jellyfin, so a half-read library list can
never silently narrow or widen what friends see.

## Requesting into a private library

Which account requests decides where the title lands.
`scripts/arr_users/private_request_routing.py` declares one ordinary Jellyseerr
account, `private-requests`, and the override rules that rewrite every request it
makes to a `-private` root folder. The
`jellyseerr-private-request-routing-provisioner` systemd unit reconciles those
rules on every rebuild, and `arr-users sync-request-routing` runs the same
reconcile by hand. Request as `private-requests` to keep a title off the public
libraries and as the admin for anything friends should get. Adding the title in
Radarr or Sonarr directly (`http://arr:7878`, `http://arr:8989`) with the
`-private` root folder picked still works, and is the fallback when a request has
to bypass Jellyseerr.

Jellyseerr evaluates override rules only for accounts holding neither admin nor
manage-requests, so the routing account has to stay an ordinary requester:
promoting it makes every rule silently stop applying while still reading as
configured in the dashboard, which is why the reconcile refuses a privileged
routing account outright. Anime series need a second rule naming the anime
keyword, because Jellyseerr drops every rule that omits it for anime. Requests are
private against friends only, who each see nothing but their own; an admin sees
every account's requests, so this hides private titles from friends, not from you.

Radarr and Sonarr key a title by its TMDB/TVDB id and can only hold it under one
root folder, so a title you already keep privately will fail a friend's request
rather than move itself into public view; grab a second public copy by hand if you
want them to have it.

To see exactly what a friend sees, log into Jellyfin as the `friends-view`
account, which is an ordinary friend account kept for that purpose.

## Moving data to an external drive

The stack keeps downloads and media under one root, `~/arr-stack/data` (`/data`
in the containers). To move that onto an external drive, mount the drive **at
that same path** so `ARR_DATA_ROOT` and every container path stay identical: no
compose, `.env`, app, or `arr-stack.nix` test change, and hardlink imports keep
working because torrents and media still share one filesystem.

The drive must be **ext4, xfs, or btrfs** (never exFAT or NTFS, which break
hardlinks and unix ownership), formatted with the filesystem label `arr-data` so
the mount is declared by label like chise's root disk.

Do the migration in this order; the nix change must land **after** the drive is
formatted and its data copied, because the chise steward auto-rebuilds and a
by-label mount that is absent (or mounted but empty) would take the stack down or
expose an empty library:

1. Format the drive ext4 with label `arr-data`, mount it somewhere temporary
   (`sudo mount /dev/disk/by-label/arr-data /mnt/arr-data`).
2. Stop the stack: `cd ~/arr-stack && docker compose down`.
3. Copy preserving hardlinks and ownership:
   `sudo rsync -aHAX --info=progress2 ~/arr-stack/data/ /mnt/arr-data/`. The `-H`
   is load-bearing: it preserves the torrent-to-media hardlinks, so space does
   not double and seeding survives. Confirm `sudo du -sh` matches and
   `sudo chown -R zanoni:users /mnt/arr-data` so the PUID/PGID owner is intact.
4. Unmount the temp mount, then land the nix change and rebuild chise.
5. `docker compose up -d`, confirm Sonarr/Radarr see the library and a test grab
   imports as an instant hardlink move; only then reclaim the shadowed internal
   copy underneath the mountpoint.

The nix change is three edits:

- Add the mount to chise's forced filesystems block in
  `hosts/chise/configs/configuration.nix`:

  ```nix
  "/home/zanoni/arr-stack/data" = {
    device = "/dev/disk/by-label/arr-data";
    fsType = "ext4";
    options = [ "nofail" "x-systemd.device-timeout=10s" ];
  };
  ```

- Gate the stack on the mount in the `systemd.services` block of
  `hosts/chise/arr-stack.nix`, so the host still boots if the drive dies but
  docker (the whole stack) waits for it:

  ```nix
  docker.unitConfig.RequiresMountsFor = [ "/home/zanoni/arr-stack/data" ];
  ```

- Point the disk-guard at the drive instead of the internal disk by adding
  `path = "/home/zanoni/arr-stack/data";` to the `arrStackOnDemandSupervisor.diskGuard`
  block in `hosts/chise/arr-stack.nix`.

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

## Media server GPU transcoding

Jellyfin and Jellyseerr now ship as compose services. Jellyfin mounts
`data/media` read-only and serves the library at port 8096. Hardware transcoding
uses chise's NVIDIA RTX 3050 via `hardware.nvidia-container-toolkit` (enabled in
`hosts/chise/configs/arr-stack-host-integration.nix`); direct play works without
it, and the GPU is used for on-the-fly transcode when a client needs it.
