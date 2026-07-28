---
name: arr-stack
description: Manage the chise media stack: Jellyfin friend accounts and Jellyseerr request and download status. Use for friends, media requests, or Jellyfin users.
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
