{
  pkgs,
  nodejs,
}:
pkgs.buildNpmPackage {
  pname = "supergateway";
  version = "3.4.3";

  src = pkgs.fetchFromGitHub {
    owner = "supercorp-ai";
    repo = "supergateway";
    rev = "v3.4.3";
    hash = "sha256-pTM2+rzQF1480dQdMsKrmkUec7Ixk9VxcnPXc39Cw6U=";
  };

  npmDepsHash = "sha256-oUDkpAh9BF99hQM6CM4GZgwN+YkF2pypclVRBxRar7o=";

  inherit nodejs;

  npmFlags = [ "--ignore-scripts" ];

  postPatch = ''
    substituteInPlace src/gateways/stdioToStatefulStreamableHttp.ts \
      --replace-fail \
        "transport.send(jsonMsg)" \
        "transport.send(jsonMsg).catch((asyncChildResponseSendError) => logger.error('Failed to send child response to StreamableHttp', asyncChildResponseSendError))"
  '';

  meta = {
    description = "Pinned supergateway stdio-to-streamableHttp MCP bridge; guards the async transport.send so a late child response on an already-closed connection logs instead of crashing the whole bridge process";
    homepage = "https://github.com/supercorp-ai/supergateway";
  };
}
