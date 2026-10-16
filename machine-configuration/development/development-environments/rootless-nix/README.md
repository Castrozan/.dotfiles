# Rootless dot environment

A headless standalone Home Manager profile for Linux x86_64 workspaces. It uses
this checkout and its existing lockfile directly; no external patch or private
submodule is needed for `homeConfigurations.dot`.

## Restore from a public clone

Before activation, place the already approved cloud age identity at
`$DOT_ROOT/home/.config/age/keys.txt` with mode `0600`; create its parent directory
with mode `0700`. The default `DOT_ROOT` is the scripts directory's sibling
`.runtime`. Keep the private identity outside Git. Its public recipient must match
`dot_key` in `secrets/secrets.nix`.


```sh
git clone https://github.com/Castrozan/.dotfiles.git
cd .dotfiles
./machine-configuration/development/development-environments/rootless-nix/scripts/activate.sh
./machine-configuration/development/development-environments/rootless-nix/scripts/verify.sh
python3 machine-configuration/development/development-environments/rootless-nix/scripts/run.py bash -l
```

Prerequisites: Linux x86_64, Python 3, bubblewrap, curl, Git, tar with xz support,
sha256sum, permitted unprivileged user/mount/PID namespaces, and access to GitHub,
releases.nixos.org and cache.nixos.org. Do not change security settings to work
around platform denials. Bootstrap verifies the pinned Nix 2.35.3 archive checksum.

Keep the Git checkout (including its `.git` metadata); source-only tarballs are not
supported by this entry point. Nix reads the tracked source so runtime state never
becomes part of the flake.

The ignored `.runtime/` directory holds downloads, the physical Nix store,
generated HOME, temporary files and the result link. Set `DOT_ROOT` to an absolute
writable directory to keep state elsewhere; use the same value for all commands.
When updating from the earlier `development/rootless-nix` layout, set `DOT_ROOT`
to its existing absolute `.runtime` path to reuse the store and generated home.
The source checkout is read-only inside the launcher. No root install or system
service is required. `/nix` exists only in the process namespace, so always run
installed binaries through `run.py`. The launcher mirrors host entries read-only
and inherits the outer platform restrictions; it is not a secret-isolation or
network-isolation boundary. Only its dedicated runtime directory is writable.
Avoid using an existing personal HOME or an ancestor of the source as `DOT_ROOT`.

Nix builds use `sandbox = true` and `sandbox-fallback = false`. The bootstrap
configuration has no build-users group because this is a single-user install.
The profile has Bash completion, Git, GitHub CLI, OpenSSH, age, jq, ripgrep, fd,
bat, fzf, zoxide, tmux, nano, less, tree, transfer/archive utilities, Python 3.12, Node 22, ShellCheck,
nixfmt and Home Manager. Login shells restore the managed package PATH after
host `/etc/profile`. User systemd management is disabled.

The thin `dot-fleet` client is included through `fleet-client-package.nix`. Its
cached status reads local metadata; remote operations use already authorized SSH
to confirmed workers. This profile starts no A2A daemon and installs no full
session-control stack. Follow the [fleet runbook](../../../../agent-harness/agent-to-agent-communication/client/FLEET.md) for confirmation, receipts and independent result verification.

`media-speech` uses the existing CLI with the ElevenLabs SDK. Verification runs
help only: it neither loads credentials nor makes synthesis calls. The Kokoro
catalog entry does not mean its model/runtime is installed.

## GitHub authentication

Dot uses the existing shared `credentials/github-com-token.age` through agenix and
the fleet's GitHub authentication module. Only this secret grants dot access;
Chise, Kira and Rin retain their recipients. The credential has the existing
`repo`, `read:org` and `gist` scopes, which are broader than this repository.
Activation runs agenix's native mount executable before configuring GitHub CLI;
it starts no user service. Git uses HTTPS through the native `gh` credential helper.
The decrypted token is mode `0400` under the managed home; GitHub CLI stores its
native authentication in `~/.config/gh/hosts.yml`. Neither file belongs in Git.

After loss of the cloud identity, Git ciphertext alone cannot restore access.
Recovery requires a newly verified cloud public recipient and re-encryption of
only this token from an authorized fleet machine. Never copy a fleet private key
into the cloud or add dot to the shared `all_keys` recipient list.

## Checks and persistence

`verify.sh` checks package entry points, managed config symlinks, Git defaults,
read-only host files, strict Nix sandbox settings and managed login-shell PATH.
Repeat activation is supported. A clean runtime can be restored with the same
activation command; downloaded binaries and generated HOME are never committed.
Workspace persistence depends on the host platform. Keep this source in Git and
restore after a reset. This profile does not verify the repository's other hosts.

Build concurrency is bounded to one job and two cores. Budget several GiB for the
store and additional headroom for downloads and builds; actual usage depends on
the locked packages. Reuse the same runtime instead of making duplicate stores.
Old Home Manager generations keep rollback paths alive. Review generations and
Nix garbage-collection roots before explicitly removing anything; these scripts
never run automatic garbage collection or delete previous generations.
