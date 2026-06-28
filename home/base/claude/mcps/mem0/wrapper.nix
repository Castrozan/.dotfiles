{
  pkgs,
  lib,
  hostname,
  homeDir,
  privateConfigRoot,
}:
let
  privateMem0HostFile = "${toString privateConfigRoot}/machines/${hostname}/mem0-host.nix";
  privateMem0HostExists = builtins.pathExists privateMem0HostFile;
  remoteBaseUrl = if privateMem0HostExists then import privateMem0HostFile else "";

  scriptsDirectory = ./scripts;
  pythonInterpreter = "${pkgs.python312}/bin/python3.12";
  localStoreDirectory = "${homeDir}/.local/share/mem0-local-fallback";
  embeddingModel = "sentence-transformers/all-MiniLM-L6-v2";
  collectionName = "claude_global_memory";
  defaultUserId = "lucas";

  memoryServerPythonDependencies = [
    "mem0ai"
    "chromadb"
    "sentence-transformers"
  ];
  uvWithDependencyFlags = lib.concatMapStringsSep " " (
    dependency: "--with ${dependency}"
  ) memoryServerPythonDependencies;

  runMemoryServer = pkgs.writeShellScript "mem0-mcp-server" ''
    export HOME=${lib.escapeShellArg homeDir}
    export MEM0_REMOTE_BASE_URL=${lib.escapeShellArg remoteBaseUrl}
    export MEM0_LOCAL_STORE_DIR=${lib.escapeShellArg localStoreDirectory}
    export MEM0_EMBEDDING_MODEL=${lib.escapeShellArg embeddingModel}
    export MEM0_COLLECTION_NAME=${lib.escapeShellArg collectionName}
    export MEM0_DEFAULT_USER_ID=${lib.escapeShellArg defaultUserId}
    export PYTORCH_ENABLE_MPS_FALLBACK=1
    export CUDA_VISIBLE_DEVICES=""
    export TOKENIZERS_PARALLELISM=false
    export ANONYMIZED_TELEMETRY=False
    export MEM0_TELEMETRY=False
    export HF_HUB_DISABLE_TELEMETRY=1
    exec ${pkgs.uv}/bin/uv run --no-project --python ${pythonInterpreter} \
      ${uvWithDependencyFlags} \
      python ${scriptsDirectory}/mem0_mcp_server.py "$@"
  '';

  prewarmMemoryServerDependencies = pkgs.writeShellScript "mem0-mcp-prewarm" ''
    export HOME=${lib.escapeShellArg homeDir}
    export ANONYMIZED_TELEMETRY=False
    export HF_HUB_DISABLE_TELEMETRY=1
    if ${pkgs.coreutils}/bin/timeout 300 ${pkgs.uv}/bin/uv run --no-project --python ${pythonInterpreter} \
      ${uvWithDependencyFlags} \
      python -c 'import mem0, chromadb, sentence_transformers' >/dev/null 2>&1; then
      echo "mem0-mcp: python dependencies ready"
    else
      echo "mem0-mcp: dependency prewarm skipped (offline?); resolves on first use" >&2
    fi
  '';
in
{
  mcpServerCommand = "${runMemoryServer}";
  mcpServerArgs = [ ];
  prewarmScript = prewarmMemoryServerDependencies;
  remoteConfigured = remoteBaseUrl != "";
}
