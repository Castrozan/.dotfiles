# Repository architecture

## The organising principle

A directory names a domain. It does not name a deployment mechanism, a platform, a machine, or a file format. Those
four are attributes of a leaf and belong inside the domain that owns it, never as a partition above it. The test is
whether a person who wants to change one capability can find every file that capability owns by opening one directory,
and whether deleting that directory removes the capability and nothing else.

## What the tree already knows

The repository already agrees on its domain names. Open `home/base` and they are all there: browser, desktop, dev,
editor, gaming, media, network, security, system, terminal, and the cluster of agent directories. That vocabulary is
correct. It is simply published one level too low, so it partitions a platform instead of partitioning the repository,
and the three trees that never received the vocabulary at all have no domain structure to speak of.

`nixos` is flat and unsorted, holding ten media provisioners next to fonts, sudo, tailscale, steam and virtualization
at one indistinguishable level. `hosts` mixes machine composition with darwin capability modules, so `brave`, `chrome`
and `vivaldi` sit beside `configs`, `secrets.nix` and `rebuild`. `.config` holds 219 raw configuration files sorted by
the program that reads them, which is a fourth naming scheme for the same capabilities the other three trees already
name.

The result is that the top level partitions by deployment mechanism first, then platform, then machine, then artifact
type, and reaches a domain name only at depth three or four. One capability therefore lands in several trees at once.
Media occupies `home/linux/arr-stack`, ten directories under `nixos`, and a check file under `hosts`. The desktop shell
occupies 598 files across eight directories in four trees. The agent harness occupies 852 files across eleven
directories in five trees. Nobody holds that map, so every change to one capability starts with a search, and a change
that should touch one directory touches four.

## Bounded contexts

Lift the existing vocabulary to the top and the domains are already named: agent harness, terminal, editor, desktop
shell, browser, media, home automation, network, security, development, gaming, and base system. Each owns its nix
modules for every platform, its raw configuration files, its scripts, its assets, its tests, and the agent skill that
describes it, because a skill explaining the arr stack is arr stack knowledge written for a different reader rather
than a member of a separate skills collection.

Three things are not domains. Machines are compositions that declare which domains a host receives and what it
overrides, so they keep a top-level tree of their own and finally merge the system half and the home half that today
are split across `hosts` and `home/hosts`. The nix library is a shared kernel every domain may depend on and nothing
may depend back into. The flake is the composition root.

The agent harness is the only domain large enough to need sub-contexts, and it has three. Harness behaviour governs how
an agent works and owns the hooks, the core rules, the evals and the conduct skills. The integrations are the per-tool
surfaces for Claude, Codex, OpenCode, clawde and hermes. Usage telemetry is one pipeline currently scattered across
four unrelated trees as `agents/usage`, `ingestion`, `apps/usage-dashboard` and the terraform in `infra/gcp` that
provisions its bucket and its upload identity.

## Target shape

```
domains/
  agent-harness/
    harness-behaviour/     hooks, core rules, evals, conduct skills
    integrations/          claude, codex, opencode, clawde, hermes
    usage-telemetry/       collection, ingestion, dashboard, its terraform
  media/
    home.nix               arr-stack user configuration
    services/              the ten arr and jellyseerr provisioners
    skill/  __tests__/
  desktop-shell/
    linux/                 hyprland, gnome, quickshell, audio
    darwin/                window manager, karabiner, hotkeys, finder
    common/                theming, wallpapers, screensaver, launcher
  browser/  terminal/  editor/  home-automation/
  network/  security/  development/  gaming/  system/
machines/
  chise/                   system.nix, home.nix, secrets.nix, configs/
  kira/  rin/  darwin-shared/
lib/  flake/  secrets/  private-config/
```

Inside a domain, platform is a directory only where the domain genuinely differs per platform, and a domain that does
not differ carries no platform directories at all. Raw configuration files that ship as-is live in the domain that owns
them rather than in a top-level `.config`, because the symlink into `~/.config` is a deployment detail the flake
already expresses and not a reason to keep a whole tree. Assets follow the same rule: wallpapers belong to desktop
shell theming and documentation screenshots belong beside the documentation they illustrate, so `static` dissolves
rather than moving.

Every current top-level tree lands somewhere. `home`, `nixos`, `hosts` and `.config` split into the domains and the
machines. `apps`, `ingestion` and `infra` join usage telemetry, apart from the one terraform file provisioning a
website deploy identity, which is not part of this repository's job and moves out. `static` dissolves into the domains
that display its files. `ril` holds four saved links and is a personal reading inbox rather than machine
configuration, so it belongs in the vault. `__tests__` keeps only the cross-domain suites once each domain carries its
own, which removes the second competing test root.

## Migration constraint

Every nix module reaches its neighbours by relative path, so moving a directory invalidates every path crossing its
boundary in both directions. That makes this mechanical rather than judgement-heavy, and it makes it verifiable: the
flake's check attribute set is a complete fingerprint of what the repository evaluates to, so a move that leaves those
names and that count unchanged on both systems has preserved behaviour.

Migrate one domain per change, verifying the fingerprint after each. Order by inbound references, fewest first, so the
early moves are cheap and the pattern is proven before it meets anything large. Gaming, editor, browser and terminal
are nearly self-contained. Media, network, security and home automation follow. The desktop shell and the agent
harness come last because they are the largest and the most referenced. Machines move only once the domains they
compose have settled, since a machine file is a list of paths into them.
