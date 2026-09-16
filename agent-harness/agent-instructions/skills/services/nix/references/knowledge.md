### The build cannot see untracked files

`rebuild` builds the flake from `git+file://` with submodules, so a dirty tree copies modified tracked files into the
store but silently excludes untracked ones. A newly written file that was never staged does not exist as far as the
build is concerned while its tracked callers do, and the auto-stage helper rescues only `.nix`, leaving every new
`.swift`, `.py`, `.lua` and `.js` exposed. Stage each new file by name before rebuilding, never after and never with a
blanket add, since parallel work shares the index. "rebuild complete" is not evidence a compiled artifact shipped: check
the binary's mtime or source hash, and read the compile step's own output.

### Submodule content needs the gitlink bumped

The build resolves the submodule at the gitlink commit recorded in the superproject, not at the submodule's working-tree
HEAD, so committing inside the submodule is invisible until the bumped gitlink is also staged and committed in the
superproject. Verifying with `nix eval` has the mirror-image trap: without `?submodules=1` the flake source copied to
the store has no submodule at all, every path-existence check reads false, and the evaluation returns a confident
false-negative green.

### Landing a submodule change past a peer

The submodule is routinely parked on a detached HEAD carrying another agent's unpushed commits. Committing there puts
your work in a branchless stack that a reset silently orphans, and staging the submodule in the superproject captures
whatever the live HEAD is, dragging all of their unpushed work into your commit. Stage the intended pointer explicitly
with `git update-index --cacheinfo` rather than adding the submodule path.

### The machine local wrapper lock is not in the deploy path

On the host built through the machine-local entrypoint flake, the rebuild copies that flake to the system flake
directory and builds from there with lock writing disabled, and that directory carries no lock at all, so the dotfiles
input resolves fresh at the branch tip on every rebuild. Landing the commit on the branch is therefore the whole deploy
step, and the wrapper's own recorded revision can sit arbitrarily far behind without holding anything back. When a
change fails to appear, do not chase a stale lock there; check whether the commit reached the branch.

Only the switch refreshes that copy, so an entrypoint edit not yet switched leaves the system flake directory on the
superseded flake and any proof resolved from it silently reports green for the old one; compare the two before trusting
such a proof.

### A oneshot that runs long hangs every rebuild that restarts it

Activation waits for a restarted `Type=oneshot` to finish its `ExecStart` before it moves on, so any oneshot that can
legitimately run for minutes, one that polls for a condition or works through a queue, freezes the whole rebuild for its
full duration the moment a `restartTriggers` entry or a changed unit definition marks it for restart. Nothing reports
this as an error; the rebuild simply sits there, and killing the rebuild leaves activation half applied.

A timer-driven oneshot never needs the restart anyway, because its next fire runs the new configuration, so declare it
`restartIfChanged = false` with `stopIfChanged = false` and drop the secret restart trigger, which is redundant once
every fire reads the secret file fresh. Reach for `RuntimeMaxSec` to bound such a unit and systemd ignores it on a
oneshot with only a log line; `TimeoutStartSec` is the ceiling that applies.

### A failing activation can report green

An activation step that exits non-zero aborts before the profile swap, leaving `current-system` frozen on an old
generation while every subsequent rebuild appears to no-op. The wrapper masks it, because a failing pipe under strict
mode kills the wrapper before its own diagnostic prints. When changes stop deploying for no visible reason, check the
current-system mtime, then rerun capturing both streams and the real exit code. One recurring instance is the frozen
nix-darwin branch emitting a deprecated homebrew cleanup flag that current Homebrew rejects.

### Darwin app copying introduces a permission gate

Home Manager's `copyApps` activation modifies application bundles and requires App Management permission from the
responsible process. Its failed permission check resets that privacy service before trying again, discarding existing
grants. Native `linkApps` replaces a directory symlink without modifying bundles or resetting grants; the shared Darwin
configuration selects that mechanism through the desktop application-installation module.

A rebuild still reporting `checkAppManagementPermission` is activating a generation with app copying enabled. Inspect
that generation and the selected module before treating the failure as a request for another privacy grant. The first
switch from copies uses Home Manager's configured backup mechanism to retain the old directory, including files used by
running applications; later switches replace the managed link.

### Agenix stalls on a stale temporary file

The home-manager agenix activation agent can loop on a stale read-only temporary file it recreates and cannot overwrite,
dying on that secret before reaching any later one, so no newly added secret decrypts machine-wide while older ones from
a previous generation stay present and make everything look healthy. The activation log names the blocking secret. Clear
the offending temporary file or the whole generation directory, kickstart the agent, and verify by decrypting the secret
directly.

### The agenix recipients here are user keys not host keys

`secrets/secrets.nix` names one ssh key per machine, and each is that machine's `~/.ssh/id_ed25519.pub`, not
`/etc/ssh/ssh_host_ed25519_key.pub`. So decrypting a secret by hand, to read an older version out of git history or to
re-encrypt a list with one entry added, uses `age --decrypt --identity ~/.ssh/id_ed25519` and needs no sudo. Reaching
for the host key instead fails with "no identity matched any of the recipients", which reads like the wrong recipient
set or a corrupt file rather than the wrong identity.

The armored files defeat the obvious sanity checks too: the recipient stanzas are inside the base64 body, so grepping
the file for `ssh-ed25519` returns nothing on a perfectly good secret. Decode the body first, then count `->
ssh-ed25519`.

### A store swap kills long lived processes on darwin

Ad-hoc-signed nix binaries carry a code hash tied to on-disk content, so replacing or collecting a store path under a
running process makes the kernel's integrity subsystem invalidate the mapped image and kill it. A rebuild that changes a
terminal multiplexer's store hash therefore kills the running server and all its sessions even when the version is
unchanged, and no person and no kill command appears in any history. Confirm it in the system log by searching for the
signature-issue message around the death window and correlating the killed store hash. The remedy is session restore,
not preventing the kill.

### Launchd agents drift after a rebuild

On darwin a rebuild that rewrites a declared launch agent's plist can leave the agent absent from launchctl entirely,
neither disabled nor erroring: it simply stops running, with no log line, no failed activation step and no warning. When
an agent's output looks stale right after a rebuild, list it in launchctl before debugging its own logic. Re-registering
it needs an enable before the bootstrap, because a bare bootstrap on a disabled label fails with an opaque IO error.
Only one module carries a self-heal activation step today; the rest drift silently.

### The neovim config is live from the working tree

`~/.config/nvim` is an out-of-store symlink into the neovim module's `program-configuration` directory, so every lua
file under it is live the moment it is saved and no rebuild publishes it. A green rebuild is therefore no evidence at
all for a keymap or plugin change; verify by opening a real nvim and pressing the key. The trap runs the other way too,
because an uncommitted or half-finished lua edit is already affecting every running editor on the machine.

`repository/git-hooks` looks like the same mode and is not, though its symlink is identical in shape:
`~/.dotfiles/.githooks` points into the working tree and git never reads that path. Resolve `core.hooksPath` before
believing a hook edit is live, because it selects a different directory whose entries are store paths built from these
sources, and a local override in `~/.dotfiles/.git/config` can leave the repo running no hook at all.

A third mode is the quiet one: a policy document or a module's own tests are copied into no closure and symlinked out of
none, so they reach no machine and a green rebuild after editing one published nothing whatsoever. Establish which of
the three a file is in before reading a rebuild as evidence about it.

### Test tiers and report publishing

The python test tier is provisioned on every machine and fails loudly rather than skipping when a collected test's
runner is absent, so a skip is a real signal. The quick and nix tiers run only the unit scope, which means integration
and end-to-end tests slip past them; CI is the gate that runs everything. Reports are published to a single bucket
prefix by exactly one workflow, and adding a second publisher to that prefix clobbers the others' output.

### A home manager package loses to usr bin on darwin

On darwin the user's session path prepends `/run/current-system/sw/bin`, the default nix profile, `/usr/bin` and `/bin`
in that order, all ahead of the home-manager profile at `/etc/profiles/per-user/<user>/bin`. Every home-manager package
whose command name also exists in macOS therefore never wins: git, curl, tar, jq, vim and python3 all resolve to Apple's
copy while the declared one sits unreachable further down the path, and nothing about that is visible in the module that
declared it.

The ordering is load-bearing rather than accidental, because the same home profile carries a gcc wrapper as `cc`,
cctools as `ld` and `as` and llvm as `ar`; hoisting it above `/usr/bin` would hand every native build on the machine a
different toolchain. A command that has to beat a macOS binary belongs in `environment.systemPackages`, whose profile is
already first on that path, not in `home.packages`.
