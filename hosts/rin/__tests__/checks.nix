{
  pkgs,
  lib,
  inputs,
  self,
  nixpkgs-version,
  home-version,
}:
let
  helpers = import ../../../__tests__/nix-checks/helpers.nix {
    inherit
      pkgs
      lib
      inputs
      nixpkgs-version
      home-version
      ;
  };
  inherit (helpers) mkEvalCheck;

  rinHomeManagerConfiguration =
    self.darwinConfigurations.rin.config.home-manager.users."lucas.zanoni";
  rinPackageNames = map (
    package: package.name or package.pname or "unknown"
  ) rinHomeManagerConfiguration.home.packages;
  rinHasPackageMatching =
    pattern: builtins.any (name: builtins.match pattern name != null) rinPackageNames;
in
{
  rin-opencode-package =
    mkEvalCheck "rin-opencode-package" (rinHasPackageMatching ".*opencode.*")
      "Rin must install opencode";

  rin-opencode-bin-wrapper =
    mkEvalCheck "rin-opencode-bin-wrapper"
      (builtins.hasAttr ".local/bin/opencode" rinHomeManagerConfiguration.home.file)
      "Rin must deploy the opencode executable";

  rin-claude-gpt-package =
    mkEvalCheck "rin-claude-gpt-package" (rinHasPackageMatching ".*claude-gpt.*")
      "Rin must install claude-gpt";

  rin-claude-gpt-proxy-agent =
    mkEvalCheck "rin-claude-gpt-proxy-agent"
      rinHomeManagerConfiguration.launchd.agents."cli-proxy-api".enable
      "Rin must run the claude-gpt proxy";
}
