_:
let

  globalRules = ''
    ${builtins.readFile ../../../agents/core_rules/core.md}
  '';

  opencodeGlobalSettings = {
    "$schema" = "https://opencode.ai/config.json";
    autoupdate = false;

    permission = {
      "*" = "allow";
      read = "allow";
      edit = "allow";
      bash = "allow";
      glob = "allow";
      grep = "allow";
      list = "allow";
      task = "allow";
      skill = "allow";
      lsp = "allow";
      todoread = "allow";
      todowrite = "allow";
      webfetch = "allow";
      websearch = "allow";
      codesearch = "allow";
      external_directory = "allow";
      doom_loop = "allow";
    };

    compaction = {
      auto = true;
      prune = true;
    };

    share = "manual";

    instructions = [ "~/.config/opencode/AGENTS.md" ];

    agent = {
      build = {
        mode = "primary";
        description = "Full-access coding agent with all tools enabled";
      };
    };

    mcp = { };
  };
in
{
  home = {
    file = {
      ".config/opencode/.keep".text = "";
      ".config/opencode/opencode.json".text = builtins.toJSON opencodeGlobalSettings;
      ".config/opencode/AGENTS.md".text = globalRules;
    };

    sessionVariables = {
      OPENCODE_AUTO_UPDATE = "false";
      OPENCODE_DISABLE_CLAUDE_CODE_SKILLS = "false";
    };
  };
}
