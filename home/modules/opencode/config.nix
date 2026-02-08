_:
let
  globalRules = ''
    ${builtins.readFile ../../../agents/core.md}
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
  };
in
{
  home = {
    file = {
      ".config/opencode/.keep".text = ""; # to keep the directory in git
      ".config/opencode/opencode.json".text = builtins.toJSON opencodeGlobalSettings;
      ".config/opencode/AGENTS.md".text = globalRules;
    };

    sessionVariables = {
      OPENCODE_AUTO_UPDATE = "false";
    };
  };
}
