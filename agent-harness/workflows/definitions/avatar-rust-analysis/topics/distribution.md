# Topic: distribution

Context files: {AVATAR_ROOT}/docs/PROPOSAL.md, {AVATAR_ROOT}/docs/CUTOVER.md, {AVATAR_ROOT}/runtime/README.md.

Settle how the single Rust artifact reaches Linux, macOS and Windows on x86-64 and arm64, and how it installs through a
Nix flake as well. Compare cargo-dist, release-plz, cargo-release, cross, cargo-zigbuild and plain GitHub Actions
matrices for building; crane, naersk, buildRustPackage and flake-parts for Nix; Homebrew, winget, installer scripts and
signing and notarization for delivery. Decide how bundled native code (model runtimes, audio libraries) and downloaded
model files are built, pinned and cached per target, and whether the flake exposes a package, an overlay, and the existing
Home Manager and NixOS module options named in docs/PROPOSAL.md. Give the CI matrix and release flow as concrete steps,
and name which of the six targets cannot be built or tested in CI without extra runners.
