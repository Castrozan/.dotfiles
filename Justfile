# just is a command runner, Justfile is very similar to Makefile, but simpler.

############################################################################
#
#  Common commands (suitable for all machines)
#
############################################################################

# List all the just commands
default:
    @just --list

# Run checks (for CI)
[group('nix')]
test:
  nix build .#checks.x86_64-linux.nixos-eval-test --show-trace
  nix build .#checks.x86_64-linux.home-manager-eval-test --show-trace

# Run checks (alias for test)
[group('nix')]
check:
  just test

# Check flake validity
[group('nix')]
flake-check:
  nix flake check --show-trace

# Update all the flake inputs
[group('nix')]
up:
  nix flake update --commit-lock-file

# Update specific input
# Usage: just upp nixpkgs
[group('nix')]
upp input:
  nix flake update {{input}} --commit-lock-file

# List all generations of the system profile
[group('nix')]
history:
  nix profile history --profile /nix/var/nix/profiles/system

# Open a nix shell with the flake
[group('nix')]
repl:
  nix repl -f flake:nixpkgs

# remove all generations older than 7 days
[group('nix')]
clean:
  # Wipe out NixOS's history
  sudo nix profile wipe-history --profile /nix/var/nix/profiles/system  --older-than 7d
  # Wipe out home-manager's history  
  nix profile wipe-history --profile ~/.local/state/nix/profiles/home-manager --older-than 7d

# Garbage collect all unused nix store entries
[group('nix')]
gc:
  # garbage collect all unused nix store entries(system-wide)
  sudo nix-collect-garbage --delete-older-than 7d
  # garbage collect all unused nix store entries(for the user - home-manager)
  nix-collect-garbage --delete-older-than 7d

# Format the nix files in this repo
[group('nix')]
fmt:
  find . -name "*.nix" -exec nixfmt {} \;

# Show all the auto gc roots in the nix store
[group('nix')]
gcroot:
  ls -al /nix/var/nix/gcroots/auto/

# Verify all the store entries
[group('nix')]
verify-store:
  nix store verify --all

############################################################################
#
#  NixOS Desktop related commands
#
############################################################################

[group('desktop')]
nixos-switch mode="switch":
  sudo nixos-rebuild {{mode}} --flake .#zanoni --show-trace

[group('desktop')]
nixos-test:
  sudo nixos-rebuild test --flake .#zanoni --show-trace

[group('desktop')]
nixos-boot:
  sudo nixos-rebuild boot --flake .#zanoni --show-trace

############################################################################
#
#  Home Manager related commands  
#
############################################################################

[group('home')]
home-switch:
  home-manager switch --flake .#lucas.zanoni@x86_64-linux --show-trace

[group('home')]
home-test:
  home-manager build --flake .#lucas.zanoni@x86_64-linux --show-trace

[group('home')]
home-news:
  home-manager news --flake .#lucas.zanoni@x86_64-linux

############################################################################
#
#  Development commands
#
############################################################################

[group('dev')]
dev-shell:
  nix develop

# Build configurations (dry-run)
[group('dev')]
build-test:
  nix build .#nixosConfigurations.zanoni.config.system.build.toplevel --dry-run --show-trace
  nix build .#homeConfigurations.\"lucas.zanoni@x86_64-linux\".activationPackage --dry-run --show-trace

# Show configuration info
[group('dev')]
info:
  @echo "NixOS Configuration: zanoni"
  @echo "Home Manager Configuration: lucas.zanoni@x86_64-linux"
  @echo "System: x86_64-linux"

############################################################################
#
#  Git and maintenance commands
#
############################################################################

# Remove all reflog entries and prune unreachable objects
[group('git')]
ggc:
  git reflog expire --expire-unreachable=now --all
  git gc --prune=now

# Amend the last commit without changing the commit message
[group('git')]
game:
  git commit --amend -a --no-edit
