{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../tests/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  cfg = helpers.homeManagerTestConfiguration [
    self.homeManagerModules.claude-code
  ];

  fileNames = builtins.attrNames cfg.home.file;

  hasFilePrefix =
    prefix: builtins.any (n: builtins.substring 0 (builtins.stringLength prefix) n == prefix) fileNames;

  deployedSettings = builtins.fromJSON cfg.home.file.".claude/settings.json.nix-source".text;

  testMachinePrivateMarketplacePluginsFixture = ../../../../private-config/machines/test/claude-plugins.nix;
  testMachinePrivateMarketplacePluginsFixtureExists = builtins.pathExists testMachinePrivateMarketplacePluginsFixture;
  testMachinePrivateMarketplacePlugins =
    if testMachinePrivateMarketplacePluginsFixtureExists then
      import testMachinePrivateMarketplacePluginsFixture
    else
      { };
  privateMarketplacePluginsAreFoldedIntoSettings =
    !testMachinePrivateMarketplacePluginsFixtureExists
    || (
      (deployedSettings.extraKnownMarketplaces or { })
      == testMachinePrivateMarketplacePlugins.extraKnownMarketplaces
      && (deployedSettings.enabledPlugins or { }) == testMachinePrivateMarketplacePlugins.enabledPlugins
    );
in
{
  claude-settings-nix-source =
    mkEvalCheck "claude-settings-nix-source"
      (builtins.hasAttr ".claude/settings.json.nix-source" cfg.home.file)
      "settings.json.nix-source should be in home.file (mutable settings.json is seeded from this)";

  claude-hooks-deployed-as-single-directory =
    mkEvalCheck "claude-hooks-deployed-as-single-directory"
      (builtins.hasAttr ".claude/hooks" cfg.home.file && !(hasFilePrefix ".claude/hooks/"))
      "hooks must deploy as one atomic directory symlink (home.file.\".claude/hooks\"), never per-file entries; per-file relinking transiently removes helper modules mid-rebuild and breaks hook imports";

  claude-skills-directory =
    mkEvalCheck "claude-skills-directory" (hasFilePrefix ".claude/skills/")
      "skills directory entries should be in home.file";

  claude-bin-wrapper =
    mkEvalCheck "claude-bin-wrapper" (builtins.hasAttr ".local/bin/claude" cfg.home.file)
      ".local/bin/claude should be in home.file";

  claude-research-skill =
    mkEvalCheck "claude-research-skill"
      (builtins.hasAttr ".local/share/claude-skill-sets/personal/.claude/skills/research" cfg.home.file)
      "research skill should be deployed in the personal vault for claude";

  claude-steward-not-in-personal-set =
    mkEvalCheck "claude-steward-not-in-personal-set"
      (!(builtins.hasAttr ".local/share/claude-skill-sets/personal/.claude/skills/steward" cfg.home.file))
      "the privileged steward payload must not be in the personal skill set every general-purpose agent loads; it lives in the steward agent type and is scoped to the steward instance";

  chrome-devtools-mcp-bridge-service-removed =
    mkEvalCheck "chrome-devtools-mcp-bridge-service-removed"
      (!(cfg.systemd.user.services ? "chrome-devtools-mcp-bridge"))
      "chrome-devtools-mcp-bridge.service must not exist; chrome-devtools is a direct stdio MCP";

  a2a-mcp-bridge-service-removed = mkEvalCheck "a2a-mcp-bridge-service-removed" (
    !(cfg.systemd.user.services ? "a2a-mcp-bridge")
  ) "a2a-mcp-bridge.service must not exist; a2a is a direct stdio MCP";

  claude-private-marketplace-plugins-folded-into-settings =
    mkEvalCheck "claude-private-marketplace-plugins-folded-into-settings"
      privateMarketplacePluginsAreFoldedIntoSettings
      "when a private-config/machines/<hostname>/claude-plugins.nix exists, global-settings.nix must fold its extraKnownMarketplaces and enabledPlugins into the deployed settings.json.nix-source; a dropped `// privateMarketplacePlugins` would silently regress the only path that installs the per-machine plugin";

}
// import ./mem0-mcp-checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    cfg
    ;
}
// import ./mcp-server-injection-checks.nix {
  inherit
    lib
    mkEvalCheck
    ;
}
// import ./hook-registration-checks.nix {
  inherit
    lib
    mkEvalCheck
    cfg
    ;
}
// import ./discord-channel-access-checks.nix {
  inherit
    lib
    mkEvalCheck
    helpers
    self
    ;
}
// import ./chrome-devtools-mcp-stealth-checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    ;
}
// import ./clawde-service-checks.nix {
  inherit
    mkEvalCheck
    helpers
    self
    ;
}
