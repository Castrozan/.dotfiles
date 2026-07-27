---
name: arr-stack
description: Manage the chise media stack: Jellyfin friend accounts, private libraries friends cannot see, and Jellyseerr request and download status. Use for friends, media requests, private media, or Jellyfin users.
---

<commands>
Two CLIs, chise only: `arr-users` manages friend accounts and reconciles the private-library boundary, and `arr-status
[title]` prints one line per Jellyseerr request with its stage and any live download progress. Run either with `--help`
for the exact interface; do not reconstruct flags from memory. On any host other than chise these commands do not exist.
</commands>

<private_libraries>
Media friends must not see goes in a private library, backed by a `-private` media directory and hidden by pinning every
non-administrator to `EnableAllFolders: false` with only the public libraries enabled.
The library declaration module in the `arr_users` package is the sole source of truth for the split and is default-deny,
so edit that module to change what is public, never a Jellyfin dashboard checkbox. Log in as `friends-view`, an ordinary
friend account kept for the purpose, to see the library as a friend does.
</private_libraries>

<private_requesting>
Requesting privately is a matter of which account requests, not of remembering a root folder: the routing module in the
`arr_users` package declares one ordinary Jellyseerr account whose every request is rewritten to a `-private` root
folder by committed override rules, reconciled on each rebuild. Request from that account to keep a title off the public
libraries, and from the admin account for anything friends should get. Adding the title in Radarr or Sonarr by hand and
picking the `-private` root still works and is the fallback when a request must bypass Jellyseerr entirely.
</private_requesting>

<private_library_traps>
An *arr app holds a title under exactly one root folder, so a title already held privately makes a friend's Jellyseerr
request fail rather than move into public view; grab a second public copy by hand if they should have it. A private
library added to Jellyseerr's synced libraries leaks its titles as available even though Jellyfin refuses to play them,
so leave the private libraries unsynced there. The reconcile refuses to write any policy when a declared public library
is missing from Jellyfin, because a half-read library list would otherwise silently narrow or widen what friends see.
</private_library_traps>

<private_requesting_traps>
Jellyseerr evaluates override rules only for accounts holding neither admin nor manage-requests, so promoting the
routing account, or requesting as the admin, silently sends the title to the public library while the rules still read
as configured; the reconcile refuses a privileged routing account rather than leave that trap armed. An anime series
needs its own rule naming the anime keyword, because Jellyseerr drops every rule that does not for anime. Requests stay
private only against friends, who see none but their own; an admin always sees every account's requests, so the split
hides nothing from the owner.
</private_requesting_traps>

<account_model>
A friend is exactly one Jellyfin account, not two. Jellyseerr authenticates against Jellyfin and its local signup is
off, so the same username and password logs into both apps: Jellyfin to watch, Jellyseerr to request. `arr-users create`
mints the Jellyfin user and imports it into Jellyseerr in one step, so never create a separate Jellyseerr login. The
generated password prints once and cannot be read back, only reset, so relay it to the user the turn it appears and do
not claim to recall it later.
</account_model>

<guards_and_traps>
`arr-users` refuses to delete, disable, or reset any account whose Jellyfin policy is administrator, so it cannot lock
out or wipe an admin or the Jellyseerr service user; that guard is deliberate, never work around it. `create` fails
rather than overwrite when the name already exists. `arr-status` degrades instead of erroring: an item reads `processing
(download chain idle)` when the on-demand supervisor has stopped the download chain, and a title that fails to resolve
shows as `tmdb:<id>`; only Jellyseerr being unreachable is a hard failure.
</guards_and_traps>

<declarative_boundary>
Friend permissions and stack config are code: the friend policy lives in the `arr_users` package and the stack in the
arr-stack nix module, changed by editing the repo and rebuilding. Never change a friend's access or the stack by
clicking in the Jellyfin or Jellyseerr dashboard, which drifts from the repo and is erased on the next rebuild. Jellyfin
admin access is an agenix secret, so the tools keep working after a wipe-and-rebuild. A rebuild re-applies the
library-visibility half of the friend policy to every existing account, so a dashboard edit to it does not even survive
until the next wipe.
</declarative_boundary>
