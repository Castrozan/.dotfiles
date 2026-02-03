_:
let
  mcpConfig = {
    mcpServers = { };
  };
in
{
  home.file.".claude/mcp.json".text = builtins.toJSON mcpConfig;
}
