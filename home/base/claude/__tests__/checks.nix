{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../../__tests__/nix-checks/helpers.nix {
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
    ../../agents/interactive-skill-index.nix
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
  darwinCfg = helpers.homeManagerTestConfigurationForDarwin [
    self.homeManagerModules.claude-code
  ];

  canonicalIngestBaseUrl = "https://lucaszanoni.com/ingest";

  launchdIngestPublishEnvironment =
    darwinCfg.launchd.agents.claude-usage-ingest-publish.config.EnvironmentVariables;

  systemdIngestPublishEnvironment =
    cfg.systemd.user.services.claude-usage-ingest-publish.Service.Environment;
in
{
  claude-usage-ingest-publish-targets-the-canonical-domain-on-darwin =
    mkEvalCheck "claude-usage-ingest-publish-targets-the-canonical-domain-on-darwin"
      (launchdIngestPublishEnvironment.INGEST_BASE_URL == canonicalIngestBaseUrl)
      "the usage producer must POST to the canonical domain; the lucaszanoni.com.br zone is a permanent redirect alias and a 301 silently drops a POST body instead of ingesting it";

  claude-usage-ingest-publish-targets-the-canonical-domain-on-linux =
    mkEvalCheck "claude-usage-ingest-publish-targets-the-canonical-domain-on-linux"
      (builtins.elem "INGEST_BASE_URL=${canonicalIngestBaseUrl}" systemdIngestPublishEnvironment)
      "the linux timer publishes through the same producer, so its systemd Environment must carry the canonical ingest url too; a redirect alias would silently drop the POST body";

  claude-settings-nix-source =
    mkEvalCheck "claude-settings-nix-source"
      (builtins.hasAttr ".claude/settings.json.nix-source" cfg.home.file)
      "settings.json.nix-source should be in home.file (mutable settings.json is seeded from this)";

  claude-hooks-deployed-as-single-directory =
    mkEvalCheck "claude-hooks-deployed-as-single-directory"
      (builtins.hasAttr ".claude/hooks" cfg.home.file && !(hasFilePrefix ".claude/hooks/"))
      "hooks must deploy as one atomic directory symlink (home.file.\".claude/hooks\"), never per-file entries; per-file relinking transiently removes helper modules mid-rebuild and breaks hook imports";

  claude-bin-wrapper =
    mkEvalCheck "claude-bin-wrapper" (builtins.hasAttr ".local/bin/claude" cfg.home.file)
      ".local/bin/claude should be in home.file";

  chrome-devtools-mcp-bridge-service-removed =
    mkEvalCheck "chrome-devtools-mcp-bridge-service-removed"
      (!(cfg.systemd.user.services ? "chrome-devtools-mcp-bridge"))
      "chrome-devtools-mcp-bridge.service must not exist; chrome-devtools is a direct stdio MCP";

  a2a-mcp-bridge-service-removed =
    mkEvalCheck "a2a-mcp-bridge-service-removed" (!(cfg.systemd.user.services ? "a2a-mcp-bridge"))
      "a2a-mcp-bridge.service must not exist; a2a is reached through the `a2a` command line tool over plain HTTP, so neither a bridge service nor an MCP server belongs here";

  claude-private-marketplace-plugins-folded-into-settings =
    mkEvalCheck "claude-private-marketplace-plugins-folded-into-settings"
      privateMarketplacePluginsAreFoldedIntoSettings
      "when a private-config/machines/<hostname>/claude-plugins.nix exists, global-settings.nix must fold its extraKnownMarketplaces and enabledPlugins into the deployed settings.json.nix-source; a dropped `// privateMarketplacePlugins` would silently regress the only path that installs the per-machine plugin";

}
// import ./skill-tier-checks.nix {
  inherit
    lib
    mkEvalCheck
    cfg
    hasFilePrefix
    ;
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
// import ./hook-flat-deploy-checks.nix {
  inherit
    lib
    mkEvalCheck
    ;
}
// import ./chrome-devtools-mcp-stealth-checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    ;
}
// import ../gpt-proxy/__tests__/checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    helpers
    self
    ;
}
// import ../opencode-go/__tests__/checks.nix {
  inherit
    pkgs
    lib
    mkEvalCheck
    helpers
    self
    ;
}
