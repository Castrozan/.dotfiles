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
    # Workspace root files (RULES.md, CLAUDE.md, etc. — excludes private identity files)
    openclaw.deployDir {
      src = ../../../agents/openclaw/workspace;
      exclude = [
        "USER.md"
        "IDENTITY.md"
        "SOUL.md"
      ];
    }

    # Skills (each subdirectory is a skill with files inside)
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

    # TTS config (generated per-agent, not from files)
    // openclaw.deployGenerated (
      _agentName: agent: {
        "tts.json".text = builtins.toJSON {
          inherit (agent.tts) engine voice;
        };
      }
    )

    # Private workspace files (identity, soul — force to override public defaults)
    // lib.optionalAttrs privateWorkspaceExists (
      openclaw.deployDir {
        src = privateDir + "/workspace";
        filter = name: _: lib.hasSuffix ".md" name;
        force = true;
      }
    )

    # Private skills (from git submodule)
    // lib.optionalAttrs privateSkillsExists (
      openclaw.deployDir {
        src = privateDir + "/skills";
        prefix = "skills";
        recurse = true;
        filter = name: _: builtins.pathExists (privateDir + "/skills/${name}/SKILL.md");
        force = true;
      }
    );
}
