---
name: arr-stack
description: Manage the chise media stack: Jellyfin friend accounts, Jellyseerr request and download status, and the separate Suwayomi and Kavita manga pipeline. Use for friends, media requests, Jellyfin users, or manga.
---

<commands>
Two CLIs, chise only: `arr-users` manages friend accounts and `arr-status [title]` prints one line per Jellyseerr
request with its stage and any live download progress. Run either with `--help` for the exact interface; do not
reconstruct flags from memory. On any host other than chise these commands do not exist.
</commands>

<account_model>
A friend is exactly one Jellyfin account, not two. Jellyseerr authenticates against Jellyfin and its local signup is
off, so the same username and password logs into both apps: Jellyfin to watch, Jellyseerr to request. `arr-users create`
mints the Jellyfin user and imports it into Jellyseerr in one step, so never create a separate Jellyseerr login. The
generated password prints once and cannot be read back, only reset, so relay it to the user the turn it appears and do
not claim to recall it later.
</account_model>

<library_visibility>
Which Jellyfin libraries an account sees is declared per account in the `arr_users` package and re-applied to every
account on each rebuild, administrators included, by pinning `EnableAllFolders: false` and writing an explicit
`EnabledFolders` list. It is a named allowlist rather than a role test, and the reconcile never changes who is an
administrator. Edit that module rather than a Jellyfin dashboard checkbox, and expect a dashboard edit not to survive
the next rebuild. The reconcile refuses to write any policy at all when a declared library is missing from Jellyfin,
because a half-read library list would silently narrow or widen what everyone sees.
</library_visibility>

<jellyseerr_account_permissions>
No request from anyone waits on an approval: the account-permission module in the `arr_users` package pins every
Jellyseerr account to request-and-auto-approve, reconciled on each rebuild, so approving is a capability nobody needs
rather than a chore someone owes. Jellyseerr scopes approval and request visibility globally, with no per-library term
in either, so an account that may approve reads and approves every request; universal auto-approve is what replaces a
scoped approver, and the reconcile keeps exactly one declared administrator so the capability exists without anyone
routinely holding it. Requesting from an admin session also bypasses the per-account request defaults, which are
evaluated only for ordinary requesters, so route a request by logging in as the intended account.
</jellyseerr_account_permissions>

<guards_and_traps>
`arr-users` refuses to delete, disable, or reset any account whose Jellyfin policy is administrator, so it cannot lock
out or wipe an admin or the Jellyseerr service user; that guard is deliberate, never work around it. `create` fails
rather than overwrite when the name already exists. `arr-status` degrades instead of erroring: an item reads `processing
(download chain idle)` when the on-demand supervisor has stopped the download chain, and a title that fails to resolve
shows as `tmdb:<id>`; only Jellyseerr being unreachable is a hard failure. An *arr app holds a title under exactly one
root folder, so a title the stack already holds can make a new request for it fail rather than relocate it.
</guards_and_traps>

<manga_is_a_separate_pipeline>
Manga never touches Jellyseerr, Prowlarr, the *arr apps or the torrent client. Jellyseerr descends from Overseerr and
models only movies and television, so it has no media type for manga and no plugin adds one; never search for a way to
request manga there, and answer that it cannot. Suwayomi acquires from its own scanlation-source extensions and Kavita
serves what it wrote, both declared in the repo like the rest of the stack. `arr-status` and `arr-users` know nothing
about either, so neither reports manga; Kavita holds its own accounts and the friend policy in the `arr_users` package
does not reach them.
</manga_is_a_separate_pipeline>

<manga_traps>
Suwayomi's download format, download path, bind address and web interface source are forced as JVM system properties on
every start, so a change made in its UI silently reverts on restart; edit the manga module in the repo instead. The web
interface is pinned to the build inside the packaged server with its update check off, so an offer to update it never
appears and never should: the version is the package's, and a newer interface arrives by bumping the package rather than
by letting the server rewrite its own mutable copy. CBZ is forced rather than
preferred because Kavita ingests archives and skips the loose per-chapter image folders Suwayomi writes by default, so
a chapter downloaded before that setting took effect stays invisible in Kavita until it is downloaded again. Suwayomi
ships no login and stays on the tailnet; Kavita has one and is published, so never publish Suwayomi to reach it from
outside.
</manga_traps>

<declarative_boundary>
Friend permissions and stack config are code: the friend policy lives in the `arr_users` package and the stack in the
arr-stack nix module, changed by editing the repo and rebuilding. Never change a friend's access or the stack by
clicking in the Jellyfin or Jellyseerr dashboard, which drifts from the repo and is erased on the next rebuild. Jellyfin
admin access is an agenix secret, so the tools keep working after a wipe-and-rebuild.
</declarative_boundary>

<reporting>
`arr-status` and `arr-users list` return every account and every request on the stack. Report only what the user asked
about: answer for the titles or accounts named in the request and leave the rest of the listing out, rather than
dumping the full roster or request history into a reply.
</reporting>

<knowledge>
For traps that cost real debugging: a request that stalls forever because its one search hit zero active indexers, a
completed download blocked by a title mismatch that the default queue query hides, and credentials that exist but never
autofill; read `knowledge.md`.
</knowledge>
