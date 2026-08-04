let
  modelsConsoleGoTranslatesToolsCorrectlyFor = [
    "qwen3.8-max"
    "qwen3.7-max"
    "qwen3.7-plus"
    "qwen3.6-plus"
    "qwen3.5-plus"
    "minimax-m2.7"
    "minimax-m2.5"
    "gpt-5.6-luna"
  ];

  toolCompatibleSubstitutes = {
    opus = "qwen3.8-max";
    sonnet = "qwen3.7-max";
    haiku = "qwen3.7-plus";
  };

  substituteWhenToolTranslationIsBroken =
    alias: model:
    if builtins.elem model modelsConsoleGoTranslatesToolsCorrectlyFor then
      model
    else
      toolCompatibleSubstitutes.${alias};
in
{
  inherit modelsConsoleGoTranslatesToolsCorrectlyFor;

  substituteToolCompatibleModels = builtins.mapAttrs substituteWhenToolTranslationIsBroken;
}
