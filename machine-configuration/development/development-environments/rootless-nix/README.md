# Rootless dot environment

A headless standalone Home Manager profile for Linux x86_64 workspaces. It uses
this checkout and its existing lockfile directly; no external patch or private
submodule is needed for `homeConfigurations.dot`.

## Restore from a public clone

```sh
git clone https://github.com/Castrozan/.dotfiles.git
cd .dotfiles
./machine-configuration/development/development-environments/rootless-nix/scripts/activate.sh
./machine-configuration/development/development-environments/rootless-nix/scripts/verify.sh
python3 machine-configuration/development/development-environments/rootless-nix/scripts/run.py bash -l
```

Until this branch is merged, check out the pull request branch before activation.
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

The thin `a2a` client is included through its existing Home Manager module. Use
its explicit `--daemon` endpoint or invoke it through SSH on a configured peer;
this profile starts no A2A daemon and installs no full session-control stack.

`media-speech` uses the existing CLI with the ElevenLabs SDK. Verification runs
help only: it neither loads credentials nor makes synthesis calls. The Kokoro
catalog entry does not mean its model/runtime is installed.

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
