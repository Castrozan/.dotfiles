{
  lib,
  pkgs,
  config,
  healthCheckLib,
  ...
}:
let
  workspaceGrid = import ./workspace-grid.nix;
  workspaceGridColumns = workspaceGrid.columns;
  totalWorkspaceCount = workspaceGrid.columns * workspaceGrid.rows;

  registeredWorkspaceNumbers = lib.range 1 totalWorkspaceCount;
  directlyBoundWorkspaceNumbers = lib.range 1 workspaceGridColumns;

  userBinPath = "/etc/profiles/per-user/${config.home.username}/bin";

  workspaceSwitchBindings = lib.listToAttrs (
    map (n: {
      name = "cmd-${toString n}";
      value = "workspace ${toString n}";
    }) directlyBoundWorkspaceNumbers
  );

  workspaceMoveBindings = lib.listToAttrs (
    map (n: {
      name = "cmd-shift-${toString n}";
      value = [
        "move-node-to-workspace ${toString n}"
        "workspace ${toString n}"
      ];
    }) directlyBoundWorkspaceNumbers
  );

  workspaceAccordionStartupCommands =
    lib.concatMap (n: [
      "workspace ${toString n}"
      "flatten-workspace-tree"
      "layout accordion"
    ]) registeredWorkspaceNumbers
    ++ [ "workspace 1" ];

  focusBindings = {
    cmd-left = "focus left";
    cmd-right = "focus right";
    cmd-up = "focus up";
    cmd-down = "focus down";
  };

  workspaceNavigationBindings = {
    ctrl-alt-left = "exec-and-forget ${userBinPath}/workspace-navigate prev";
    ctrl-alt-right = "exec-and-forget ${userBinPath}/workspace-navigate next";
    ctrl-alt-up = "exec-and-forget ${userBinPath}/workspace-navigate row-up";
    ctrl-alt-down = "exec-and-forget ${userBinPath}/workspace-navigate row-down";
    ctrl-alt-shift-left = "exec-and-forget ${userBinPath}/workspace-navigate prev --move-window";
    ctrl-alt-shift-right = "exec-and-forget ${userBinPath}/workspace-navigate next --move-window";
    ctrl-alt-shift-up = "exec-and-forget ${userBinPath}/workspace-navigate row-up --move-window";
    ctrl-alt-shift-down = "exec-and-forget ${userBinPath}/workspace-navigate row-down --move-window";
    cmd-alt-left = "exec-and-forget ${userBinPath}/workspace-navigate prev";
    cmd-alt-right = "exec-and-forget ${userBinPath}/workspace-navigate next";
    cmd-alt-up = "exec-and-forget ${userBinPath}/workspace-navigate row-up";
    cmd-alt-down = "exec-and-forget ${userBinPath}/workspace-navigate row-down";
    cmd-alt-shift-left = "exec-and-forget ${userBinPath}/workspace-navigate prev --move-window";
    cmd-alt-shift-right = "exec-and-forget ${userBinPath}/workspace-navigate next --move-window";
    cmd-alt-shift-up = "exec-and-forget ${userBinPath}/workspace-navigate row-up --move-window";
    cmd-alt-shift-down = "exec-and-forget ${userBinPath}/workspace-navigate row-down --move-window";
  };

in
{
  programs.aerospace = {
    enable = true;
    launchd.enable = false;
    userSettings = {
      enable-normalization-flatten-containers = true;
      enable-normalization-opposite-orientation-for-nested-containers = true;

      accordion-padding = 0;
      default-root-container-layout = "accordion";
      default-root-container-orientation = "auto";

      after-startup-command = workspaceAccordionStartupCommands;

      key-mapping.preset = "qwerty";

      on-focus-changed = [
        ''exec-and-forget ${userBinPath}/workspace-switcher-send "focus:$AEROSPACE_WINDOW_ID"''
      ];
      on-focused-monitor-changed = [ "move-mouse monitor-lazy-center" ];

      exec-on-workspace-change = [
        "/bin/bash"
        "-c"
        "/usr/bin/open -g 'swiftbar://refreshallplugins'"
      ];

      on-window-detected = [
        { run = [ "layout accordion" ]; }
      ];

      gaps = {
        inner = {
          horizontal = 0;
          vertical = 0;
        };
        outer = {
          left = 0;
          right = 0;
          top = 0;
          bottom = 0;
        };
      };

      mode.main.binding =
        workspaceSwitchBindings // workspaceMoveBindings // focusBindings // workspaceNavigationBindings;
    };
  };

  home.activation.installAerospaceAppAtCanonicalPath = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    canonicalPath="/Applications/AeroSpace.app"
    sourceAppBundle="${pkgs.aerospace}/Applications/AeroSpace.app"
    installedSourceMarker="$canonicalPath/Contents/.nix-source"

    # Reinstalling rm's, re-copies, and re-codesigns the bundle, which mints a
    # new ad-hoc code identity and makes macOS revoke AeroSpace's Accessibility
    # grant. That breaks the IPC socket until the user re-approves it. So only
    # reinstall when the nix store source actually changed, recorded in a marker
    # file; an unchanged source is a no-op that preserves the existing grant.
    if [ "$(cat "$installedSourceMarker" 2>/dev/null)" != "${pkgs.aerospace}" ]; then
      if [ -L "$canonicalPath" ] || [ -d "$canonicalPath" ]; then
        # /bin/cp -R from the nix store preserves the store's 0555 dir mode, so
        # subsequent activations cannot rm -rf the canonical path until we
        # restore write permission on every directory.
        $DRY_RUN_CMD /usr/bin/chflags -R nouchg "$canonicalPath" 2>/dev/null || true
        $DRY_RUN_CMD /bin/chmod -R u+w "$canonicalPath" 2>/dev/null || true
        $DRY_RUN_CMD /bin/rm -rf "$canonicalPath"
      fi
      $DRY_RUN_CMD /bin/cp -R "$sourceAppBundle" "$canonicalPath"
      $DRY_RUN_CMD /usr/bin/chflags -R nouchg "$canonicalPath" 2>/dev/null || true
      $DRY_RUN_CMD /bin/chmod -R u+w "$canonicalPath" 2>/dev/null || true
      $DRY_RUN_CMD /usr/bin/codesign --force --deep --sign - "$canonicalPath" 2>/dev/null || true
      $DRY_RUN_CMD /bin/echo "${pkgs.aerospace}" >"$installedSourceMarker"
    fi
  '';

  home.activation.dismissAerospaceAccessibilityPopup =
    lib.hm.dag.entryAfter [ "setupLaunchAgents" ]
      ''
        $DRY_RUN_CMD /usr/bin/pkill -x universalAccessAuthWarn 2>/dev/null || true
      '';

  launchd.agents.aerospace-app = {
    enable = true;
    config = {
      Label = "org.nix-community.home.aerospace-app";
      ProgramArguments = [
        "/Applications/AeroSpace.app/Contents/MacOS/AeroSpace"
      ];
      RunAtLoad = true;
      KeepAlive = true;
      StandardOutPath = "/tmp/aerospace.log";
      StandardErrorPath = "/tmp/aerospace.err.log";
    };
  };

  healthCheck.probes = [
    (healthCheckLib.mkProcessProbe {
      name = "AeroSpace running";
      pattern = "AeroSpace.app/Contents/MacOS/AeroSpace";
    })
  ];
}
