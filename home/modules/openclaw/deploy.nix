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

    # Agent rules
    // openclaw.deployDir {
      src = ../../../agents/rules;
      prefix = "rules";
    }

    # Executable scripts (.sh, .py)
    // openclaw.deployDir {
      src = ../../../agents/scripts;
      prefix = "scripts";
      filter = name: _: lib.hasSuffix ".sh" name || lib.hasSuffix ".py" name;
      executable = true;
      # hey-clever scripts only deploy to the default agent
      filterForAgent =
        agentName: name: _:
        if lib.hasPrefix "hey-clever" name then agentName == openclaw.defaultAgent else true;
    }

    # Skills (each subdirectory is a skill with files inside)
    // openclaw.deployDir {
      src = ../../../agents/skills;
      prefix = "skills";
      exclude = [
        "bot-bridge"
        "whatsapp-polling"
      ];
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
