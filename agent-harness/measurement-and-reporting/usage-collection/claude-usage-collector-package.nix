{ pkgs, lib }:
pkgs.rustPlatform.buildRustPackage {
  pname = "claude-usage-collector";
  version = "0.1.0";

  src = lib.fileset.toSource {
    root = ./.;
    fileset = lib.fileset.unions [
      ./Cargo.toml
      ./Cargo.lock
      ./src
      ./tests
    ];
  };
  cargoLock.lockFile = ./Cargo.lock;

  meta = {
    description = "Incremental Claude Code usage ledger and ingestion publisher";
    mainProgram = "claude-usage-collector";
    platforms = lib.platforms.unix;
  };
}
