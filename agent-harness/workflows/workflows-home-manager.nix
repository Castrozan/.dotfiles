{
  pkgs,
  lib,
  config,
  ...
}:
let
  archon = import ./archon-package.nix { inherit pkgs lib; };

  skillsDirectory = ../agent-instructions/skills;

  workflowDefinitionDirectories = {
    dotfiles-housekeeping = ./definitions/dotfiles-housekeeping;
    dotfiles-housekeeping-slice = ./definitions/dotfiles-housekeeping-slice;
    dotfiles-housekeeping-verify = ./definitions/dotfiles-housekeeping-verify;
    compose-page = skillsDirectory + "/writing/page-composer/workflow/compose-page";
    research-pulse = skillsDirectory + "/knowledge/research/workflow/research-pulse";
    research-pulse-fetch = skillsDirectory + "/knowledge/research/workflow/research-pulse-fetch";
  };

  installWorkflowDefinition = workflowName: definitionDirectory: ''
    cp -r ${definitionDirectory} "$out/${workflowName}"
    chmod -R u+w "$out/${workflowName}"
    find "$out/${workflowName}" -name '*.yaml' -exec sed -i \
      -e "s|@python@|${pkgs.python312}/bin/python3|g" \
      -e "s|@jq@|${pkgs.jq}/bin/jq|g" \
      -e "s|@instructionData@|${pkgs.python312}/bin/python3 ${./scripts}/instruction_data.py|g" \
      -e "s|@workflowDirectory@|$out/${workflowName}|g" {} +
  '';

  dotfilesWorkflowPack = pkgs.runCommand "dotfiles-archon-workflows" { } ''
    mkdir -p "$out"
    ${lib.concatStrings (lib.mapAttrsToList installWorkflowDefinition workflowDefinitionDirectories)}
  '';

  yamlFormat = pkgs.formats.yaml { };

  archonConfiguration = yamlFormat.generate "archon-config.yaml" {
    defaultAssistant = "claude";
    assistants =
      lib.optionalAttrs (config ? claude) {
        claude.claudeBinaryPath = "${config.claude.unwrappedPackage}/bin/claude";
      }
      // lib.optionalAttrs (config ? codex) {
        codex.codexBinaryPath = "${config.codex.unwrappedPackage}/bin/codex";
      };
  };

  providerRunConfigurations = lib.genAttrs [ "claude" "codex" ] (
    provider: yamlFormat.generate "archon-run-${provider}.yaml" { assistant = provider; }
  );

  workflowRuntimePath = lib.makeBinPath [
    archon
    pkgs.git
  ];

  mkWorkflowCommand =
    {
      commandName,
      workflowName,
      argumentNames,
    }:
    pkgs.writeShellScriptBin commandName ''
      export PATH="${workflowRuntimePath}:$PATH"
      export DOTFILES_WORKFLOW_COMMAND="${commandName}"
      export DOTFILES_WORKFLOW_NAME="${workflowName}"
      export DOTFILES_WORKFLOW_ARGUMENTS="${lib.concatStringsSep " " argumentNames}"
      export DOTFILES_WORKFLOW_PROVIDER_CONFIGURATIONS=${lib.escapeShellArg (builtins.toJSON providerRunConfigurations)}
      exec ${pkgs.python312}/bin/python3 ${./scripts}/dotfiles_workflow.py "$@"
    '';

  workflowWaitCommand = pkgs.writeShellScriptBin "dotfiles-workflow-wait" ''
    export PATH="${workflowRuntimePath}:$PATH"
    exec ${pkgs.python312}/bin/python3 ${./scripts}/wait_for_dotfiles_workflow.py "$@"
  '';
in
{
  home.packages = [
    archon
    workflowWaitCommand
  ]
  ++ map mkWorkflowCommand [
    {
      commandName = "dotfiles-housekeeping";
      workflowName = "dotfiles-housekeeping";
      argumentNames = [
        "root"
        "subtree"
      ];
    }
    {
      commandName = "dotfiles-compose-page";
      workflowName = "compose-page";
      argumentNames = [
        "brief"
        "output"
        "constraints"
      ];
    }
    {
      commandName = "dotfiles-research-pulse";
      workflowName = "research-pulse";
      argumentNames = [
        "topic"
        "accounts"
        "max_items"
      ];
    }
  ];

  home.file = {
    ".archon/config.yaml".source = archonConfiguration;
    ".archon/plugins".source = "${archon}/share/archon/plugins";
    ".archon/workflows/dotfiles".source = dotfilesWorkflowPack;
  };
}
