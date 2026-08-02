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

  configurationWithTheZenProxyEnabled = helpers.homeManagerTestConfiguration [
    ../.
    { opencode.zenAnonymousProxy.enable = true; }
  ];

  packageNames = map (p: p.name or p.pname or "unknown") cfg.home.packages;
  hasPackageMatching = pattern: builtins.any (n: builtins.match pattern n != null) packageNames;

  deployedFileNames = builtins.attrNames cfg.home.file;
  hasDeployedFilePrefix =
    prefix:
    builtins.any (
      name: builtins.substring 0 (builtins.stringLength prefix) name == prefix
    ) deployedFileNames;

  parseDeployedJson =
    deployedText: builtins.fromJSON (builtins.unsafeDiscardStringContext deployedText);

  deployedOpencodeSettings = parseDeployedJson cfg.home.file.".config/opencode/opencode.json".text;
  deployedTuiSettings = parseDeployedJson cfg.home.file.".config/opencode/tui.json".text;
  deployedGlobalRules = cfg.home.file.".config/opencode/AGENTS.md".text;

  codexGlobalInstructions =
    (import ../../codex/global-instructions.nix { }).home.file.".codex/AGENTS.md".text;

  modelProviderOf = model: builtins.head (lib.splitString "/" model);

  providersThisMachineCanAuthenticate = [
    "opencode"
    "opencode-go"
  ];
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
      (cfg.opencode.unwrappedPackage.name == "opencode")
      "an autonomous harness launches this package instead of the interactive wrapper, and clawde symlinks it onto the agent's PATH as `opencode`, so it must keep providing a binary of that name. It is no longer the bare upstream release: that one never reads OPENCODE_API_KEY, which left every agent on a paid opencode-go model unauthenticated while the free tier hid the fault";

  domain-opencode-default-model-resolves-against-an-authenticated-provider =
    mkEvalCheck "domain-opencode-default-model-resolves-against-an-authenticated-provider"
      (
        builtins.elem (modelProviderOf deployedOpencodeSettings.model) providersThisMachineCanAuthenticate
        && builtins.elem (modelProviderOf deployedOpencodeSettings.small_model) providersThisMachineCanAuthenticate
      )
      "both defaults must resolve against opencode.ai: the free zen tier under `opencode`, which needs no credential, or the paid plan under `opencode-go`, which the wrapper authenticates from the agenix key. Any other provider needs a credential nothing here deploys, so opencode would open on a model it cannot call";

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
      (
        deployedOpencodeSettings.lsp.pyright.env.PYTHONPATH != ""
        && deployedOpencodeSettings.formatter == true
      )
      "opencode must enable its built-in LSP servers and formatters with the Python test environment available to Pyright";

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

  domain-opencode-ships-no-zen-proxy-unless-asked =
    mkEvalCheck "domain-opencode-ships-no-zen-proxy-unless-asked"
      (!(cfg.systemd.user.services ? opencode-zen-anonymous-proxy))
      "the Zen anonymous proxy is an opt-in for a runtime that cannot call a keyless remote provider, so a machine that never enables it must get no such service";

  domain-opencode-zen-proxy-listens-where-its-base-url-points =
    mkEvalCheck "domain-opencode-zen-proxy-listens-where-its-base-url-points"
      (
        let
          service = configurationWithTheZenProxyEnabled.systemd.user.services.opencode-zen-anonymous-proxy;
          declaredPort = toString configurationWithTheZenProxyEnabled.opencode.zenAnonymousProxy.port;
        in
        builtins.elem "OPENCODE_ZEN_PROXY_PORT=${declaredPort}" service.Service.Environment
        &&
          configurationWithTheZenProxyEnabled.opencode.zenAnonymousProxy.baseUrl
          == "http://127.0.0.1:${declaredPort}/v1"
      )
      "the port the proxy is told to listen on and the base URL its consumers are handed must come from the same option, or a model runtime silently calls a closed port";
}
