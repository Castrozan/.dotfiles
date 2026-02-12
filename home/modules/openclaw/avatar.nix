{
  lib,
  pkgs,
  config,
  ...
}:
let
  inherit (config) openclaw;
  homeDir = config.home.homeDirectory;

  # Avatar is shared infrastructure - deploy to default agent's workspace
  defaultAgentWorkspace =
    if openclaw.defaultAgent != null then
      openclaw.agents.${openclaw.defaultAgent}.workspace
    else
      "openclaw";

  avatarDir = "${homeDir}/${defaultAgentWorkspace}/skills/avatar";
  controlServerSource = ../../../agents/skills/avatar/control-server;

  controlServerFiles = [
    "server.js"
    "package.json"
    "package-lock.json"
    "virtual-camera.js"
    "virtual-mic.sh"
  ];

  rendererSrc = pkgs.fetchFromGitHub {
    owner = "Castrozan";
    repo = "ChatVRM";
    rev = "27980c893afae4ca3b5f451d9edf19c1bc37ac26";
    hash = "sha256-BZbFrX1aRGwW7RZ5iZ5HQCLwhOit/lYvIH+NeO644yo=";
  };

  # Generate deploy files for default agent
  mkDeployFiles =
    agentName:
    builtins.listToAttrs (
      map (filename: {
        name = "skills/avatar/control-server/${filename}";
        value =
          if lib.hasSuffix ".sh" filename then
            {
              text = openclaw.substituteAgentConfig agentName (controlServerSource + "/${filename}");
              executable = true;
            }
          else if filename == "server.js" then
            { text = openclaw.substituteAgentConfig agentName (controlServerSource + "/${filename}"); }
          else
            { source = controlServerSource + "/${filename}"; };
      }) controlServerFiles
    );

  deployFiles =
    if openclaw.defaultAgent != null then
      openclaw.deployToWorkspace openclaw.defaultAgent (mkDeployFiles openclaw.defaultAgent)
    else
      { };
in
{
  home = {
    packages = lib.mkIf (openclaw.defaultAgent != null) [
      pkgs.python3Packages.edge-tts
    ];
    file = deployFiles;
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
            cd "$RENDERER_DIR" && ${pkgs.nodejs_22}/bin/npm install 2>&1 || true
          fi

          if [ -d "$RENDERER_DIR" ] && [ ! -d "$RENDERER_DIR/node_modules" ]; then
            echo "Installing renderer npm dependencies..."
            cd "$RENDERER_DIR" && ${pkgs.nodejs_22}/bin/npm install 2>&1 || true
          fi
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
          ]
        }:/run/current-system/sw/bin"
        "NODE_PATH=${avatarDir}/control-server/node_modules"
        "XDG_RUNTIME_DIR=/run/user/1000"
      ];
    };
  };
}
