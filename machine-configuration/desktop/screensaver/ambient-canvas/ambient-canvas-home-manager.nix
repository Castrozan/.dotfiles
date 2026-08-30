{
  pkgs,
  lib,
  config,
  ...
}:
let
  ambientCanvasWebRoot = ./web;
  ambientCanvasIndexFile = "${ambientCanvasWebRoot}/index.html";
  ambientCanvasMediaScriptsDirectory = ./scripts/ambient_canvas_media;
  ambientCanvasStateDirectory = "${config.home.homeDirectory}/.local/state/ambient-canvas";
  ambientCanvasSourceIdentifier = "${ambientCanvasWebRoot}";
  ambientCanvasPlayerBinaryPath = "${config.home.homeDirectory}/.local/bin/ᓚᘏᗢ";
  ambientCanvasPlaybackDwellSecondsPath = "${ambientCanvasStateDirectory}/playback-dwell-seconds";
  ambientCanvasDefaultPlaybackDwellSeconds = 30;

  ambientCanvasSceneVideoDownloaderPath = lib.makeBinPath [ pkgs.yt-dlp ];
  ambientCanvasPlayerRuntimePath = lib.makeBinPath (
    lib.optionals pkgs.stdenv.hostPlatform.isLinux [
      pkgs.mpv
      pkgs.hyprland
    ]
  );

  ambientCanvasPlayerRuntimePathPrefix = lib.optionalString pkgs.stdenv.hostPlatform.isLinux "${ambientCanvasPlayerRuntimePath}:";

  ambientCanvasScreensaverLauncher = pkgs.writeShellScriptBin "ambient-canvas" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasIndexFile}"
    export PATH="${ambientCanvasSceneVideoDownloaderPath}:${ambientCanvasPlayerRuntimePathPrefix}$PATH"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/ensure_ambient_canvas_screensaver.py \
      --output-directory "${ambientCanvasStateDirectory}" \
      --source-identifier "${ambientCanvasSourceIdentifier}" \
      --player-binary "${ambientCanvasPlayerBinaryPath}" \
      "$@"
  '';

  ambientCanvasLoopRenderer = pkgs.writeShellScriptBin "ambient-canvas-render" ''
    export AMBIENT_CANVAS_INDEX="${ambientCanvasIndexFile}"
    export PATH="${ambientCanvasSceneVideoDownloaderPath}:$PATH"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/render_ambient_canvas_loop.py \
      --output-directory "${ambientCanvasStateDirectory}" \
      --source-identifier "${ambientCanvasSourceIdentifier}" \
      "$@"
  '';

  ambientCanvasMpvPlayer = pkgs.writeShellScriptBin "ᓚᘏᗢ" ''
    export PATH="${ambientCanvasPlayerRuntimePath}:$PATH"
    export PYTHONPATH="${ambientCanvasMediaScriptsDirectory}"
    exec ${pkgs.python312}/bin/python3 \
      ${ambientCanvasMediaScriptsDirectory}/play_ambient_canvas_loop_mpv.py "$@"
  '';
in
{
  config = lib.mkMerge [
    {
      home = {
        packages = [
          ambientCanvasScreensaverLauncher
          ambientCanvasLoopRenderer
        ];

        activation.ensureAmbientCanvasStateDirectory =
          lib.hm.dag.entryAfter
            [
              "writeBoundary"
            ]
            ''
              run mkdir -p ${lib.escapeShellArg ambientCanvasStateDirectory}
              if [ ! -e ${lib.escapeShellArg ambientCanvasPlaybackDwellSecondsPath} ]; then
                run ${pkgs.coreutils}/bin/tee ${lib.escapeShellArg ambientCanvasPlaybackDwellSecondsPath} \
                  <<<${toString ambientCanvasDefaultPlaybackDwellSeconds} >/dev/null
              fi
            '';
      };
    }

    (lib.mkIf pkgs.stdenv.hostPlatform.isDarwin {
      home.activation.compileAmbientCanvasPlayer = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
        export AMBIENT_CANVAS_PLAYER_BINARY_PATH=${lib.escapeShellArg ambientCanvasPlayerBinaryPath}
        export AMBIENT_CANVAS_PLAYER_SOURCES_DIR=${./swift-sources}
        export AMBIENT_CANVAS_PLAYER_COMPILE_RECIPE_HASH=${builtins.hashFile "sha256" ./compile-player.sh}
        ${builtins.readFile ./compile-player.sh}
      '';

      launchd.agents.ambient-canvas = {
        enable = true;
        config = {
          Label = "com.dotfiles.ambient-canvas";
          ProgramArguments = [ "${ambientCanvasScreensaverLauncher}/bin/ambient-canvas" ];
          RunAtLoad = true;
          StartInterval = 300;
          StandardOutPath = "${ambientCanvasStateDirectory}/keep-alive.log";
          StandardErrorPath = "${ambientCanvasStateDirectory}/keep-alive.log";
        };
      };
    })

    (lib.mkIf pkgs.stdenv.hostPlatform.isLinux {
      home.file."${config.home.homeDirectory}/.local/bin/ᓚᘏᗢ".source =
        "${ambientCanvasMpvPlayer}/bin/ᓚᘏᗢ";

      systemd.user.timers.ambient-canvas = {
        Unit = {
          Description = "ambient-canvas screensaver keep-alive timer";
        };
        Timer = {
          OnBootSec = "1min";
          OnUnitActiveSec = "5min";
          OnCalendar = "*:0/5";
          Persistent = true;
        };
        Install = {
          WantedBy = [ "timers.target" ];
        };
      };

      systemd.user.services.ambient-canvas = {
        Unit = {
          Description = "ambient-canvas screensaver keep-alive";
          After = [ "graphical-session.target" ];
          PartOf = [ "graphical-session.target" ];
          ConditionEnvironment = "WAYLAND_DISPLAY";
          X-RestartIfChanged = false;
          X-StopIfChanged = false;
        };
        Service = {
          Type = "oneshot";
          KillMode = "process";
          ExecStart = "${ambientCanvasScreensaverLauncher}/bin/ambient-canvas";
        };
        Install = {
          WantedBy = [ "graphical-session.target" ];
        };
      };
    })
  ];
}
