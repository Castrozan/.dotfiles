{
  pkgs,
  lib,
  hostname,
  config,
  ...
}:
let
  hostsWithClaudeGo = [
    "chise"
    "kira"
    "rin"
  ];
  claudeGoEnabledOnThisHost = lib.elem hostname hostsWithClaudeGo;
  opencodeGo = import ../../opencode/go-provider.nix { inherit (config.home) homeDirectory; };

  claudeGoLauncher = pkgs.writeShellScriptBin "claude-go" ''
    opencodeGoApiKeyFile="${opencodeGo.apiKeyFile}"
    if [ ! -f "$opencodeGoApiKeyFile" ] || [ ! -r "$opencodeGoApiKeyFile" ]; then
      echo "claude-go: no readable API key at $opencodeGoApiKeyFile" >&2
      echo "deploy the opencode-api-key agenix secret and retry" >&2
      exit 1
    fi
    unset ANTHROPIC_AUTH_TOKEN
    export ANTHROPIC_API_KEY="$(cat "$opencodeGoApiKeyFile")"
    export ANTHROPIC_BASE_URL="${opencodeGo.baseUrl}"
    export ANTHROPIC_DEFAULT_OPUS_MODEL="${opencodeGo.claudeCodeModels.opus}"
    export ANTHROPIC_DEFAULT_SONNET_MODEL="${opencodeGo.claudeCodeModels.sonnet}"
    export ANTHROPIC_DEFAULT_HAIKU_MODEL="${opencodeGo.claudeCodeModels.haiku}"
    exec ${config.claude.package}/bin/claude --model "${opencodeGo.claudeCodeModels.sonnet}" "$@"
  '';
in
{
  config = lib.mkIf claudeGoEnabledOnThisHost {
    home.packages = [ claudeGoLauncher ];
  };
}
