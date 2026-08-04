{ homeDirectory }:
{
  apiKeyFile = "${homeDirectory}/.secrets/opencode-api-key";
  baseUrl = "https://opencode.ai/zen/go";
  models = {
    opus = "deepseek-v4-pro";
    sonnet = "deepseek-v4-flash";
    haiku = "kimi-k3";
  };
}
