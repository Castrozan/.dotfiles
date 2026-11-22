{ homeDirectory }:
{
  apiKeyFile = "${homeDirectory}/.secrets/opencode-api-key";
  baseUrl = "https://opencode.ai/inference/go";
  models = {
    fable = "kimi-k3.1-pro";
    opus = "deepseek-v4-pro";
    sonnet = "deepseek-v4.1-flash";
    haiku = "kimi-k3";
  };
}
