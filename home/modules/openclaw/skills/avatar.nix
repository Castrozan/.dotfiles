{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  defaultAgentWorkspace =
    if openclaw.defaultAgent != null then
      openclaw.agents.${openclaw.defaultAgent}.workspace
    else
      "openclaw";

  avatarDir = "${homeDir}/${defaultAgentWorkspace}/skills/comms";

  agentsWithAvatar = lib.filterAttrs (
    _name: agent: agent.enable && (agent.skills == [ ] || builtins.elem "comms" agent.skills)
  ) openclaw.agents;

  nonDefaultAvatarAgents = lib.filterAttrs (
    name: _: openclaw.defaultAgent != null && name != openclaw.defaultAgent
  ) agentsWithAvatar;

  rendererSrc = pkgs.fetchFromGitHub {
    owner = "Castrozan";
    repo = "ChatVRM";
    rev = "90cfc391796d38d0d9e43ece238c78b931b3cebd";
    hash = "sha256-aqRuL9hoghKw0MgT5JWRFls3dM8i8WVr2yt4MhLznKE=";
  };

  controlServerNodeModules = pkgs.buildNpmPackage {
    pname = "avatar-control-server-deps";
    version = "1.0.0";
    src = ../../../../agents/skills/comms/control-server;
    npmDepsHash = "sha256-gP9LivOQ+3+CcAbzg/Dt2RfB0p1j4045TABD3vQzu2s=";
    nodejs = pkgs.nodejs_22;
    dontNpmBuild = true;
    installPhase = ''
      runHook preInstall
      mkdir -p $out
      cp -r node_modules $out/
      runHook postInstall
    '';
  };

in
{
  openclaw.gridPlaceholders = {
    "@avatarWsPort@" = "8765";
    "@avatarHttpPort@" = "8766";
    "@avatarRendererPort@" = "3000";
  };

  home = {
    packages = lib.mkIf (openclaw.defaultAgent != null) [
      pkgs.python3Packages.edge-tts
    ];
    file = { };
    activation = {
      avatarRenderer = lib.mkIf (openclaw.defaultAgent != null) (
        lib.hm.dag.entryAfter [ "linkGeneration" ] ''
          RENDERER_DIR="${avatarDir}/renderer"
          RENDERER_MARKER="${avatarDir}/renderer/.nix-source-rev"
          EXPECTED_REV="${rendererSrc}"

          if [ ! -d "$RENDERER_DIR" ] || [ ! -f "$RENDERER_MARKER" ] || [ "$(cat "$RENDERER_MARKER" 2>/dev/null)" != "$EXPECTED_REV" ]; then
            echo "Deploying avatar renderer from nix store..."
            rm -rf "$RENDERER_DIR"
            mkdir -p "$RENDERER_DIR"
            cp -rT "$EXPECTED_REV" "$RENDERER_DIR"
            chmod -R u+w "$RENDERER_DIR"
            echo "$EXPECTED_REV" > "$RENDERER_MARKER"
            echo "Installing renderer npm dependencies..."
            cd "$RENDERER_DIR" && ${pkgs.nodejs_22}/bin/npm install --legacy-peer-deps 2>&1 || true
          fi

          if [ -d "$RENDERER_DIR" ] && [ ! -d "$RENDERER_DIR/node_modules" ]; then
            echo "Installing renderer npm dependencies..."
            cd "$RENDERER_DIR" && ${pkgs.nodejs_22}/bin/npm install --legacy-peer-deps 2>&1 || true
          fi

          ${lib.concatStringsSep "\n" (
            lib.mapAttrsToList (name: agent: ''
              AGENT_RENDERER="${homeDir}/${agent.workspace}/skills/comms/renderer"
              if [ ! -e "$AGENT_RENDERER" ]; then
                mkdir -p "$(dirname "$AGENT_RENDERER")"
                ln -sfn "$RENDERER_DIR" "$AGENT_RENDERER"
                echo "Symlinked avatar renderer for ${name}"
              fi
            '') nonDefaultAvatarAgents
          )}
        ''
      );
      avatarControlServerDeps = lib.mkIf (openclaw.defaultAgent != null) (
        lib.hm.dag.entryAfter [ "linkGeneration" ] ''
          CONTROL_DIR="${avatarDir}/control-server"
          if [ -d "$CONTROL_DIR" ]; then
            rm -rf "$CONTROL_DIR/node_modules"
            ln -sfn "${controlServerNodeModules}/node_modules" "$CONTROL_DIR/node_modules"
          fi

          ${lib.concatStringsSep "\n" (
            lib.mapAttrsToList (name: agent: ''
              AGENT_CONTROL_DIR="${homeDir}/${agent.workspace}/skills/comms/control-server"
              if [ -d "$AGENT_CONTROL_DIR" ]; then
                rm -rf "$AGENT_CONTROL_DIR/node_modules"
                ln -sfn "${controlServerNodeModules}/node_modules" "$AGENT_CONTROL_DIR/node_modules"
              fi
            '') nonDefaultAvatarAgents
          )}
        ''
      );
    };
  };

  systemd.user.services.avatar-control-server = lib.mkIf (openclaw.defaultAgent != null) {
    Unit.Description = "Avatar Control Server";
    Service = {
      Type = "simple";
      WorkingDirectory = "${avatarDir}/control-server";
      ExecStart = "${pkgs.nodejs_22}/bin/node server.js";
      Restart = "on-failure";
      RestartSec = 5;
      Environment = [
        "PATH=${
          lib.makeBinPath [
            pkgs.python3Packages.edge-tts
            pkgs.nodejs_22
            pkgs.ffmpeg
            pkgs.pulseaudio
          ]
        }:/run/current-system/sw/bin"
        "NODE_PATH=${controlServerNodeModules}/node_modules"
        "AVATAR_WS_PORT=8765"
        "AVATAR_HTTP_PORT=8766"
        "XDG_RUNTIME_DIR=/run/user/%U"
      ];
    };
  };
}
