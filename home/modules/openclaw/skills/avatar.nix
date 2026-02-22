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

  avatarDir = "${homeDir}/${defaultAgentWorkspace}/skills/avatar";

  agentsWithAvatar = lib.filterAttrs (
    _name: agent: agent.enable && (agent.skills == [ ] || builtins.elem "avatar" agent.skills)
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

in
{
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
              AGENT_RENDERER="${homeDir}/${agent.workspace}/skills/avatar/renderer"
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
          if [ -d "$CONTROL_DIR" ] && [ -f "$CONTROL_DIR/package-lock.json" ]; then
            LOCK_HASH=$(sha256sum "$CONTROL_DIR/package-lock.json" | cut -d' ' -f1)
            MARKER="$CONTROL_DIR/.npm-ci-hash"
            if [ ! -d "$CONTROL_DIR/node_modules" ] || [ ! -f "$MARKER" ] || [ "$(cat "$MARKER" 2>/dev/null)" != "$LOCK_HASH" ]; then
              echo "Installing control server npm dependencies..."
              cd "$CONTROL_DIR" && ${pkgs.nodejs_22}/bin/npm ci --production 2>&1 || true
              echo "$LOCK_HASH" > "$MARKER"
            fi
          fi

          ${lib.concatStringsSep "\n" (
            lib.mapAttrsToList (name: agent: ''
              AGENT_CONTROL_MODULES="${homeDir}/${agent.workspace}/skills/avatar/control-server/node_modules"
              if [ ! -e "$AGENT_CONTROL_MODULES" ] && [ -d "$CONTROL_DIR/node_modules" ]; then
                ln -sfn "$CONTROL_DIR/node_modules" "$AGENT_CONTROL_MODULES"
                echo "Symlinked avatar control-server node_modules for ${name}"
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
        "NODE_PATH=${avatarDir}/control-server/node_modules"
        "XDG_RUNTIME_DIR=/run/user/%U"
      ];
    };
  };
}
