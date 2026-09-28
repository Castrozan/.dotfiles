{ pkgs, lib }:
pkgs.rustPlatform.buildRustPackage (finalAttributes: {
  pname = "herdr-agent-resume";
  version = "0.1.1-unstable-2026-09-17";

  src = pkgs.fetchFromGitHub {
    owner = "Angel-O";
    repo = "herdr-agent-resume";
    rev = "dcd6417ac87b5d73e8b32e12486a4838850e8b1a";
    hash = "sha256-TClh+l0+2XT04NLQD9ZEq1cny1LuSENyxDLy62OKEaQ=";
  };

  cargoLock.lockFile = "${finalAttributes.src}/Cargo.lock";

  postInstall = ''
    mkdir -p "$out/share/herdr/plugins/agent-resume/target/release"
    cp herdr-plugin.toml "$out/share/herdr/plugins/agent-resume/"
    ln -s "$out/bin/herdr-agent-resume" "$out/share/herdr/plugins/agent-resume/target/release/herdr-agent-resume"
  '';

  meta = {
    description = "Recover agent resume commands from Herdr pane scrollback";
    homepage = "https://github.com/Angel-O/herdr-agent-resume";
    license = lib.licenses.mit;
    platforms = lib.platforms.linux ++ lib.platforms.darwin;
    mainProgram = "herdr-agent-resume";
  };
})
