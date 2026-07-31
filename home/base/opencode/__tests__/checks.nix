{
  pkgs,
  lib,
  inputs,
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

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;

  deployedFileNames = builtins.attrNames cfg.home.file;
  hasDeployedFilePrefix =
    prefix:
    builtins.any (
      name: builtins.substring 0 (builtins.stringLength prefix) name == prefix
    ) deployedFileNames;

  deployedOpencodeSettings = builtins.fromJSON cfg.home.file.".config/opencode/opencode.json".text;
  deployedTuiSettings = builtins.fromJSON cfg.home.file.".config/opencode/tui.json".text;
  deployedGlobalRules = cfg.home.file.".config/opencode/AGENTS.md".text;

  codexGlobalInstructions =
    (import ../../codex/global-instructions.nix { }).home.file.".codex/AGENTS.md".text;

  modelProviderOf = model: builtins.head (lib.splitString "/" model);
in
{
  domain-opencode-package =
    mkEvalCheck "domain-opencode-package" (hasPackageMatching ".*opencode.*")
      "opencode package should be installed";

  domain-opencode-bin-wrapper =
    mkEvalCheck "domain-opencode-bin-wrapper" (builtins.hasAttr ".local/bin/opencode" cfg.home.file)
      ".local/bin/opencode should be in home.file";

  domain-opencode-unwrapped-package-is-exposed =
    mkEvalCheck "domain-opencode-unwrapped-package-is-exposed"
      (cfg.opencode.unwrappedPackage.pname == "opencode")
      "the bare opencode binary must stay reachable so an autonomous harness can bypass the interactive wrapper";

  domain-opencode-default-model-resolves-against-an-authenticated-provider =
    mkEvalCheck "domain-opencode-default-model-resolves-against-an-authenticated-provider"
      (
        modelProviderOf deployedOpencodeSettings.model == "opencode"
        && modelProviderOf deployedOpencodeSettings.small_model == "opencode"
      )
      "opencode must default to a model on the built-in opencode provider, which needs no separate credential";

  domain-opencode-default-agent-runs-at-max-effort =
    mkEvalCheck "domain-opencode-default-agent-runs-at-max-effort"
      (
        deployedOpencodeSettings.agent.build.variant == "max"
        && deployedOpencodeSettings.agent.build.mode == "primary"
      )
      "opencode's default build agent must be primary and run at max reasoning effort";

  domain-opencode-global-rules-match-the-codex-surface =
    mkEvalCheck "domain-opencode-global-rules-match-the-codex-surface"
      (deployedGlobalRules == codexGlobalInstructions)
      "opencode's AGENTS.md must carry the same frontmatter-stripped core rules Claude and Codex deploy";

  domain-opencode-loads-the-global-rules =
    mkEvalCheck "domain-opencode-loads-the-global-rules"
      (builtins.elem "~/.config/opencode/AGENTS.md" deployedOpencodeSettings.instructions)
      "opencode must load the deployed global rules through its instructions list";

  domain-opencode-runs-with-full-access = mkEvalCheck "domain-opencode-runs-with-full-access" (
    deployedOpencodeSettings.permission."*" == "allow"
    && deployedOpencodeSettings.permission.bash == "allow"
    && deployedOpencodeSettings.permission.edit == "allow"
  ) "opencode must run without approval prompts, matching Claude's bypassPermissions posture";

  domain-opencode-enables-language-servers-and-formatters =
    mkEvalCheck "domain-opencode-enables-language-servers-and-formatters"
      (deployedOpencodeSettings.lsp == true && deployedOpencodeSettings.formatter == true)
      "opencode must enable its built-in LSP servers and formatters rather than leaving them off";

  domain-opencode-wires-the-browser-mcp = mkEvalCheck "domain-opencode-wires-the-browser-mcp" (
    deployedOpencodeSettings.mcp ? chrome-devtools
    && deployedOpencodeSettings.mcp.chrome-devtools.enabled
  ) "opencode must wire the shared chrome-devtools MCP that Claude and Codex both wire";

  domain-opencode-allows-nested-subagents = mkEvalCheck "domain-opencode-allows-nested-subagents" (
    deployedOpencodeSettings.subagent_depth >= 2
  ) "opencode must let a subagent launch its own subagents, matching Claude's nesting";

  domain-opencode-deploys-subagent-definitions =
    mkEvalCheck "domain-opencode-deploys-subagent-definitions"
      (builtins.hasAttr ".config/opencode/agent" cfg.home.file)
      "the shared subagent definitions must be translated into opencode's agent directory";

  domain-opencode-deploys-commands =
    mkEvalCheck "domain-opencode-deploys-commands" (hasDeployedFilePrefix ".config/opencode/command/")
      "the shared slash commands must be deployed into opencode's command directory";

  domain-opencode-deploys-skills =
    mkEvalCheck "domain-opencode-deploys-skills" (hasDeployedFilePrefix ".config/opencode/skills/")
      "the shared skills must be deployed into opencode's skills directory";

  domain-opencode-tui-matches-the-desktop-theme =
    mkEvalCheck "domain-opencode-tui-matches-the-desktop-theme"
      (deployedTuiSettings.theme == "kanagawa" && deployedTuiSettings.attention.enabled)
      "opencode's TUI must follow the machine's selected theme and chime when a turn finishes";
}
