{
  listenAddress,
  listenPort,
  authenticationDirectory,
  upstreamBaseUrl,
  upstreamProviderName,
  modelNames,
  apiKeyPlaceholder,
}:
let
  modelEntryLines = map (
    modelName: "      - name: \"${modelName}\"\n        alias: \"${modelName}\"\n"
  ) modelNames;
in
''
  host: "${listenAddress}"
  port: ${toString listenPort}
  auth-dir: "${authenticationDirectory}"
  api-keys: []
  debug: false
  openai-compatibility:
    - name: "${upstreamProviderName}"
      base-url: "${upstreamBaseUrl}"
      api-key-entries:
        - api-key: "${apiKeyPlaceholder}"
      models:
''
+ builtins.concatStringsSep "" modelEntryLines
