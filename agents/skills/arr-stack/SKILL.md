---
name: arr-stack
description: Manage the chise media stack: create and manage Jellyfin friend accounts, and check Jellyseerr request and download status. Use for friends, media requests, or Jellyfin users.
---

<commands>
Two CLIs, chise only: `arr-users` manages friend accounts (list, create, set-email, delete, reset-password, enable, disable) and `arr-status [title]` prints one line per Jellyseerr request with its stage and any live download progress. Run either with `--help` for the exact interface; do not reconstruct flags from memory. On any host other than chise these commands do not exist.
</commands>

<account_model>
A friend is exactly one Jellyfin account, not two. Jellyseerr authenticates against Jellyfin and its local signup is off, so the same username and password logs into both apps: Jellyfin to watch, Jellyseerr to request. `arr-users create` mints the Jellyfin user and imports it into Jellyseerr in one step, so never create a separate Jellyseerr login. The generated password prints once and cannot be read back, only reset, so relay it to the user the turn it appears and do not claim to recall it later.
</account_model>

<guards_and_traps>
`arr-users` refuses to delete, disable, or reset any account whose Jellyfin policy is administrator, so it cannot lock out or wipe an admin or the Jellyseerr service user; that guard is deliberate, never work around it. `create` fails rather than overwrite when the name already exists. `arr-status` degrades instead of erroring: an item reads `processing (download chain idle)` when the on-demand supervisor has stopped the download chain, and a title that fails to resolve shows as `tmdb:<id>`; only Jellyseerr being unreachable is a hard failure.
</guards_and_traps>

<declarative_boundary>
Friend permissions and stack config are code: the friend policy lives in the `arr_users` package and the stack in the arr-stack nix module, changed by editing the repo and rebuilding. Never change a friend's access or the stack by clicking in the Jellyfin or Jellyseerr dashboard, which drifts from the repo and is erased on the next rebuild. Jellyfin admin access is an agenix secret, so the tools keep working after a wipe-and-rebuild.
</declarative_boundary>
