{ homeDirectory }:
let
  nativeModels = {
    opus = "deepseek-v4-pro";
    sonnet = "deepseek-v4-flash";
    haiku = "kimi-k3";
  };

  consoleGoAnthropicToolTranslation = import ./console-go-anthropic-tool-translation-workaround.nix;
in
{
  apiKeyFile = "${homeDirectory}/.secrets/opencode-api-key";
  baseUrl = "https://opencode.ai/zen/go";
  models = nativeModels;
  claudeCodeModels = consoleGoAnthropicToolTranslation.substituteToolCompatibleModels nativeModels;
}
