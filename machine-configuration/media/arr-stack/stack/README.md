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

## Reaching it

Every container publishes to chise's tailscale IP alone, which the `arr` alias
resolves to, so it answers on the tailnet and on no other interface. Read the
compose file for what runs and on which port; a roster here would only go stale.
Most of these apps ship no login at all, which is the whole reason the tailnet is
the boundary: nothing loginless may ever be published past it.

The user-facing front ends are the deliberate exception, so that someone can watch
and request without joining the tailnet. The Tailscale funnel module names which
ones and on what hostname; the rule it exists to enforce is that a service reachable
from the public internet carries a login and sits behind the login rate-limiting
proxy, or it is not published at all. That proxy throttles attempts per real client
IP recovered from the funnel's `X-Forwarded-For`, and it is the enforcement point
the host firewall cannot be, because a funnelled request arrives wearing the
funnel's own address rather than the caller's. Use the HTTPS address rather than the raw tailnet port even
from inside the tailnet: the plain port sends credentials in cleartext, which is
also why a password manager holding the HTTPS origin refuses to fill a login form
served over the other one.

The stack carries only the libraries that get used. Music and books are gone and
their *arr apps are not coming back, Readarr having been archived upstream in
mid-2025 with no maintained successor. Manga is carried, but by a separate path
that shares none of the machinery below; see "Manga is a second pipeline".

Nothing in the stack speaks to a VPN and there is no per-container gateway to
configure. Routing traffic through one is a host-level toggle that moves everything
on the host at once, described below.

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
`machine-configuration/media/arr-stack/stack/` in the dotfiles and rebuild chise. Container config and
media persist on disk under the paths below, untouched by rebuilds.

## Persistence

Each app keeps its own config directory, and every app that moves files shares one
data root, both created on rebuild and bind-mounted in. The compose file and the
arr-stack module declare the paths; the constraint they exist to satisfy is that
downloads and the finished library sit on a single filesystem, so an import is an
atomic hardlink move rather than a copy and seeding survives it. Anything that
splits those across filesystems, including mounting one of them elsewhere, breaks
that and has to be undone rather than worked around.

## Who sees which library

Not every library is for everyone. Which ones an account may see is a declared
per-account allowlist in the `arr_users` package, never a role test, applied by
pinning `EnableAllFolders` false and writing the permitted libraries out
explicitly. Jellyfin honours a restricted folder list for administrators too, so
administering the server and seeing everything on it stay separate concerns, and
the reconcile writes visibility onto administrators like anyone else while never
touching who is one. Restricting an account this way is not putting anything out of
its reach: an administrator can re-grant itself a library in the dashboard, and the
next rebuild pins it back.

The declaration is default-deny, so a library nobody declared visible is visible to
nobody and one added later stays hidden until someone says otherwise. A restricted
library must also be kept out of the request front end's synced-library list,
because that front end announces a synced title as available to every account
regardless of whether Jellyfin will actually serve it to them.

The reconcile runs from a systemd unit on every rebuild and from `arr-users` on
demand, and refuses to write any policy at all when a declared library is missing
from Jellyfin, because acting on a half-read library list would silently narrow or
widen what everyone sees. Editing visibility in the dashboard is drift and does not
survive the next rebuild.

## Routing a request to a chosen root folder

Which account requests decides where the title lands. The routing module in the
`arr_users` package declares which accounts get their requests rewritten to a
different root folder, and the override rules that do it, reconciled from a systemd
unit on every rebuild and by `arr-users` on demand.

Two upstream behaviours make this fragile enough to know before touching it. First,
Jellyseerr evaluates override rules only for ordinary requesters, and `MediaRequest`
takes that gate from the logged-in session user rather than from the account chosen
in the Advanced panel's "Request As" dropdown, which only reassigns attribution. A
request made from an admin session therefore ignores every rule and uses whatever
root folder was submitted, no matter whose name is on it, so route by logging in as
the intended account or by setting the root folder by hand. The same gate is why a
routing account must never be promoted. Second, an anime series needs its own rule
naming the anime keyword, because Jellyseerr drops every rule that omits it.

Adding a title in Radarr or Sonarr directly with the root folder picked there works
too, and is the fallback when a request has to bypass the request front end
entirely.

## Nobody approves anything

The account-permission module in the `arr_users` package declares what every
Jellyseerr account holds, request and auto-approve and nothing else, pinned from a
systemd unit on every rebuild and by `arr-users` on demand. No request from anyone
sits pending, so approving is a capability nobody needs rather than a chore someone
owes.

Approval and request visibility are global in Jellyseerr, with no per-library or
per-root-folder term in the query behind either, so an account that may approve also
reads every other account's requests by title. A scoped approver cannot be built,
which is what makes universal auto-approve the replacement rather than a shortcut,
and it is why holding approval is the exception rather than the norm. Exactly one
declared administrator is exempt, so the capability exists without anyone carrying
it by default, and the reconcile refuses to run at all if it would leave none:
granting the permission back is itself gated on holding it, so no remaining account
could recover. The CLIs and provisioners never depend on any of this, because
Jellyseerr resolves an API key to the owner account regardless of what the human
accounts hold.

An *arr app keys a title by its TMDB or TVDB id and can hold it under exactly one
root folder, so a title the stack already holds makes a new request for it fail
rather than relocate it. Grab a second copy by hand when both are genuinely wanted.

## Manga is a second pipeline

Manga shares the data drive and nothing else. No *arr app indexes it, Prowlarr and
qBittorrent never see it, and the request front end cannot reach it: Jellyseerr
descends from Overseerr and models only movies and television, so books and manga
have no media type there and no plugin adds one. Wanting a title is therefore
something you act on in the manga reader, not something anyone approves.

Suwayomi acquires and Kavita serves. Suwayomi pulls from scanlation sources through
its own extensions rather than from indexers, and the module in
`machine-configuration/media/manga-streaming/` forces the settings the rest of this
pipeline depends on: chapters archived as CBZ, written under the data drive's manga
root, on a bind address that is never the wildcard, and a web interface taken from
the pinned server build rather than fetched at runtime. They are forced as JVM system
properties on every start, so changing them in the Suwayomi UI is drift the next
start overwrites, the same bargain the Jellyfin library allowlist makes. Left to
itself Suwayomi periodically looks for a newer web interface and rewrites the one it
serves into its mutable data directory, which both nags on open and takes the served
version out of this repo's hands; pinned to the bundled build, that version moves
only when the package moves. Kavita
mounts that tree read-only, which is what stops the reader mutating what the
downloader owns, and reads the source directory as a publisher with the title
directory beneath it as a series, a nesting Kavita documents as supported. Loose
chapter image folders are not, which is why CBZ is forced rather than preferred.

Two boundaries are easy to erase by accident. The manga tree sits beside the Jellyfin
media root rather than inside it, because Jellyfin bind-mounts that whole root while
the per-account allowlist reasons only about declared Jellyfin libraries, so anything
else living there is content Jellyfin serves paths into and no allowlist covers. And
who may read what is Kavita's own account model, not the friend policy in the
`arr_users` package, which knows only Jellyfin and Jellyseerr. Kavita carries a login
and is published on the funnel behind the login rate-limiting proxy like the other
front ends; Suwayomi carries none and stays on the tailnet, which is the rule the
rest of the stack already follows rather than an exception made for it.

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
  `machine-configuration/machines/chise/system/configs/configuration.nix`:

  ```nix
  "/home/zanoni/arr-stack/data" = {
    device = "/dev/disk/by-label/arr-data";
    fsType = "ext4";
    options = [ "nofail" "x-systemd.device-timeout=10s" ];
  };
  ```

- Gate the stack on the mount in the `systemd.services` block of
  `machine-configuration/media/arr-stack/chise/chise-arr-stack-nixos.nix`, so the host still boots if the drive dies but
  docker (the whole stack) waits for it:

  ```nix
  docker.unitConfig.RequiresMountsFor = [ "/home/zanoni/arr-stack/data" ];
  ```

- Point the disk-guard at the drive instead of the internal disk by adding
  `path = "/home/zanoni/arr-stack/data";` to the `arrStackOnDemandSupervisor.diskGuard`
  block in `machine-configuration/media/arr-stack/chise/chise-arr-stack-nixos.nix`.

## Optional VPN (off by default, host-level)

The default stack runs with no VPN: qBittorrent talks to the internet directly.
There is no per-container VPN gateway in this stack and nothing to configure here
to get the default behavior.

chise has a host-level Proton VPN OpenVPN tunnel, toggled by packaged commands
in this repo. Turning it on
routes *all* of chise's traffic, the arr-stack containers included, with no
compose changes:

```sh
vpn-py        # connect Proton VPN through a Paraguay server
vpn-off       # disconnect Proton VPN
```

See `machine-configuration/network/vpn/protonvpn/protonvpn-nixos.nix` for the
service and command definitions. Bring the stack up the same way regardless;
the VPN is an independent host toggle.

## Media server GPU transcoding

Jellyfin and Jellyseerr now ship as compose services. Jellyfin mounts
`data/media` read-only and serves the library at port 8096. Hardware transcoding
uses chise's NVIDIA RTX 3050 via `hardware.nvidia-container-toolkit` (enabled in
`machine-configuration/media/arr-stack/chise/chise-arr-stack-host-integration-nixos.nix`); direct play works without
it, and the GPU is used for on-the-fly transcode when a client needs it.
