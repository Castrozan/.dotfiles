{ homeDirectory }:
{
  apiKeyFile = "${homeDirectory}/.secrets/opencode-api-key";
  baseUrl = "https://opencode.ai/zen/go";
  models = {
    opus = "deepseek-v4-pro";
    sonnet = "deepseek-v4-flash";
    haiku = "kimi-k3";
  };
  claudeCodeModels = {
    opus = "qwen3.7-max";
    sonnet = "qwen3.7-max";
    haiku = "qwen3.7-max";
  };
}
