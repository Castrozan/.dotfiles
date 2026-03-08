{
  lib,
  config,
  ...
}:
let
  inherit (config) openclaw;

  privateDir = ../../../private-config/openclaw;
  privateWorkspaceExists = builtins.pathExists (privateDir + "/workspace");
  privateSkillsExists = builtins.pathExists (privateDir + "/skills");
in
{
  home.file =
    openclaw.deployDir {
      src = ./workspace;
      exclude = [
        "USER.md"
        "IDENTITY.md"
        "SOUL.md"
      ];
    }

    // openclaw.deployDir {
      src = ../../../agents/skills;
      prefix = "skills";
      exclude = [
        "bot-bridge"
        "whatsapp-polling"
      ];
      executable = true;
      recurse = true;
      filterForAgent =
        agentName: name: _:
        let
          agent = openclaw.agents.${agentName};
        in
        agent.skills == [ ] || builtins.elem name agent.skills;
    }

    // openclaw.deployGenerated (
      _agentName: agent: {
        "tts.json".text = builtins.toJSON {
          inherit (agent.tts) engine voice;
        };
      }
    )

    // lib.optionalAttrs privateWorkspaceExists (
      openclaw.deployDir {
        src = privateDir + "/workspace";
        filter = name: _: lib.hasSuffix ".md" name;
        force = true;
      }
    )

    // lib.optionalAttrs privateSkillsExists (
      openclaw.deployDir {
        src = privateDir + "/skills";
        prefix = "skills";
        recurse = true;
        filter = name: _: builtins.pathExists (privateDir + "/skills/${name}/SKILL.md");
        force = true;
      }
    )

    // openclaw.deployToAllWorkspaces {
      "skills/aplicacoes-atendimento-triage" = {
        source = config.lib.file.mkOutOfStoreSymlink "${config.home.homeDirectory}/repo/aplicacoes-atendimento-triage";
      };
    }

    // openclaw.deployToAllWorkspaces {
      "skills/sourcebot" = {
        source = ../sourcebot/skill;
        recursive = true;
      };
    };
}
