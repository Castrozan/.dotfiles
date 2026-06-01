{ pkgs, config, ... }:
let
  aerospaceBinPath = "/etc/profiles/per-user/${config.home.username}/bin";

  swiftbarPluginDirectory = "${config.home.homeDirectory}/repo/swiftbar";
  workspaceIndicatorPluginPath = "${swiftbarPluginDirectory}/aerospace-workspaces.1s.sh";

  workspaceIndicatorPlugin = pkgs.replaceVars ./plugins/aerospace-workspaces.1s.sh {
    inherit aerospaceBinPath;
  };
in
{
  home = {
    packages = [ pkgs.swiftbar ];

    activation = {
      # SwiftBar is sandboxed and cannot read a plugin through a symlink that
      # points into the nix store (outside its granted folder bookmark), so
      # home.file's store symlink renders no menu-bar item. Copy the plugin in
      # as a real file the sandbox can read directly.
      installSwiftbarWorkspacePlugin = config.lib.dag.entryAfter [ "writeBoundary" ] ''
        $DRY_RUN_CMD /bin/mkdir -p "${swiftbarPluginDirectory}"
        $DRY_RUN_CMD /bin/cp -f "${workspaceIndicatorPlugin}" "${workspaceIndicatorPluginPath}"
        $DRY_RUN_CMD /bin/chmod u+rwx "${workspaceIndicatorPluginPath}"
      '';

      configureSwiftbarDefaults = config.lib.dag.entryAfter [ "writeBoundary" ] ''
        /usr/bin/defaults write com.ameba.SwiftBar PluginDirectory -string "${swiftbarPluginDirectory}"
        /usr/bin/defaults write com.ameba.SwiftBar SUEnableAutomaticChecks -bool false
      '';

      refreshSwiftbarAfterPluginInstalled =
        config.lib.dag.entryAfter [ "installSwiftbarWorkspacePlugin" "setupLaunchAgents" ]
          ''
            $DRY_RUN_CMD /bin/launchctl kickstart -k "gui/$UID/org.nix-community.home.swiftbar" 2>/dev/null || true
          '';
    };
  };

  launchd.agents.swiftbar = {
    enable = true;
    config = {
      Label = "org.nix-community.home.swiftbar";
      ProgramArguments = [ "${pkgs.swiftbar}/Applications/SwiftBar.app/Contents/MacOS/SwiftBar" ];
      RunAtLoad = true;
      KeepAlive = true;
      StandardOutPath = "/tmp/swiftbar.log";
      StandardErrorPath = "/tmp/swiftbar.err.log";
    };
  };
}
