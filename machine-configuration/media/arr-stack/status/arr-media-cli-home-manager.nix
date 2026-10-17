{
  pkgs,
  stackRoot,
  operatorDiscordUserId,
}:
pkgs.writeShellScriptBin "arr-media" ''
  export ARR_MEDIA_STACK_HOME=${pkgs.lib.escapeShellArg stackRoot}
  export ARR_MEDIA_OPERATOR_DISCORD_USER_ID=${
    pkgs.lib.escapeShellArg (if operatorDiscordUserId == null then "" else operatorDiscordUserId)
  }
  exec ${pkgs.python312}/bin/python3 ${./scripts/arr_media}/__main__.py "$@"
''
