{
  helpers,
  pkgs,
  lib,
  ...
}:
let
  inherit (helpers) mkEvalCheck;
  interactiveAgentSkills =
    import
      ../../../../agent-harness/agent-instructions/interactive-skill-catalog/interactive-agent-skills.nix
      {
        hostname = "test";
      };

  cfg = helpers.homeManagerTestConfiguration [ ../. ];

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
  deployedHookBridge = cfg.home.file.".config/opencode/plugins/opencode-hook-bridge.js";
  opencodeWrapperSource = builtins.readFile ../opencode.nix;
  opencodeGoProvider = import ../go-provider.nix { inherit (cfg.home) homeDirectory; };

  codexGlobalInstructions =
    (import ../../codex/global-instructions.nix { }).home.file.".codex/AGENTS.md".text;

  modelProviderOf = model: builtins.head (lib.splitString "/" model);

  providersThisMachineCanAuthenticate = [
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
      "both defaults must resolve against opencode.ai on the paid Go plan under `opencode-go`, which the wrapper authenticates from the agenix key. Any other provider needs a credential nothing here deploys, so opencode would open on a model it cannot call";

  domain-opencode-default-models-use-the-shared-go-provider =
    mkEvalCheck "domain-opencode-default-models-use-the-shared-go-provider"
      (
        deployedOpencodeSettings.model == "opencode-go/${opencodeGoProvider.models.sonnet}"
        && deployedOpencodeSettings.small_model == "opencode-go/${opencodeGoProvider.models.haiku}"
      )
      "the interactive and title defaults must use the shared Go provider model definitions";

  domain-opencode-go-provider-exposes-one-model-selection =
    mkEvalCheck "domain-opencode-go-provider-exposes-one-model-selection"
      (
        !(opencodeGoProvider ? claudeCodeModels)
        &&
          builtins.attrNames opencodeGoProvider.models == [
            "haiku"
            "opus"
            "sonnet"
          ]
      )
      "Console Go's Anthropic endpoint drops tool names, and claude-go answers that by translating locally rather than by running different models, so a second per-harness model set would silently split the two surfaces again";

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
      (deployedOpencodeSettings.lsp.pyright.env.PYTHONPATH != "" && deployedOpencodeSettings.formatter)
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

  domain-opencode-deploys-skills =
    mkEvalCheck "domain-opencode-deploys-skills" (hasDeployedFilePrefix ".config/opencode/skills/")
      "the shared skills must be deployed into opencode's skills directory";

  domain-opencode-carries-the-shared-interactive-set =
    mkEvalCheck "domain-opencode-carries-the-shared-interactive-set"
      (builtins.all (
        skillName: builtins.hasAttr ".config/opencode/skills/${skillName}" cfg.home.file
      ) interactiveAgentSkills.defaultInteractiveSkillNames)
      "every shared interactive skill must deploy into the OpenCode machine tier";

  domain-opencode-core-skill =
    mkEvalCheck "domain-opencode-core-skill"
      (builtins.hasAttr ".config/opencode/skills/core/SKILL.md" cfg.home.file)
      "core must deploy as a generated OpenCode skill as well as global instructions";

  domain-opencode-deploys-hook-bridge =
    mkEvalCheck "domain-opencode-deploys-hook-bridge"
      (
        deployedHookBridge ? source
        && lib.hasInfix "pkgs.replaceVars" (
          builtins.readFile ../../../../agent-harness/hooks/integrations/opencode/opencode-hooks-home-manager.nix
        )
        && lib.hasInfix "opencodeHookDispatcher" (
          builtins.readFile ../../../../agent-harness/hooks/integrations/opencode/opencode-hooks-home-manager.nix
        )
      )
      "OpenCode must deploy the auto-discovered hook bridge and substitute its dispatcher path from Nix, so pre-tool guard denials and post-tool dispatchers run without depending on a shell-session environment variable";

  domain-opencode-marks-interactive-sessions =
    mkEvalCheck "domain-opencode-marks-interactive-sessions"
      (lib.hasInfix "OPENCODE_INTERACTIVE_PREFERENCES_PATH" opencodeWrapperSource)
      "the interactive OpenCode wrapper must mark keyboard-driven sessions so shared prompt and subagent hook guards run there while unwrapped autonomous sessions remain excluded";

  domain-opencode-tui-matches-the-desktop-theme =
    mkEvalCheck "domain-opencode-tui-matches-the-desktop-theme"
      (deployedTuiSettings.theme == "kanagawa" && deployedTuiSettings.attention.enabled)
      "opencode's TUI must follow the machine's selected theme and chime when a turn finishes";
}
