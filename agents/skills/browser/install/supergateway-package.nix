{
  pkgs,
  nodejs,
}:
let
  prebuiltSourceWithModernMcpSdkLock = pkgs.applyPatches {
    name = "supergateway-3.4.3-prebuilt-modern-mcp-sdk-lock";
    src = pkgs.fetchurl {
      url = "https://registry.npmjs.org/supergateway/-/supergateway-3.4.3.tgz";
      hash = "sha256-0mORmWAmu1lnp36HdHTN/6lDHtWcZRhtVXBk3pj1q4Q=";
    };
    postPatch = ''
      cp ${./supergateway-package-lock.json} package-lock.json
    '';
  };
in
pkgs.buildNpmPackage {
  pname = "supergateway";
  version = "3.4.3";

  src = prebuiltSourceWithModernMcpSdkLock;

  npmDepsHash = "sha256-hZ5yEqfv0za8A+EHQHtDBMr1cTV2I4wrYOWzBRkZYtk=";

  inherit nodejs;

  npmFlags = [ "--ignore-scripts" ];

  dontNpmBuild = true;

  postPatch = ''
    substituteInPlace dist/gateways/stdioToStatefulStreamableHttp.js \
      --replace-fail \
        "transport.send(jsonMsg);" \
        "transport.send(jsonMsg).catch((asyncChildResponseSendError) => logger.error('Failed to send child response to StreamableHttp', asyncChildResponseSendError));"
  '';

  meta = {
    description = "Pinned supergateway stdio-to-streamableHttp MCP bridge from the published prebuilt dist, with the bundled @modelcontextprotocol/sdk bumped to 1.29.0 so the streamableHttp server accepts the 2025-11-25 protocol that current Claude Code negotiates, and the async transport.send guarded so a late child response on a closed connection logs instead of crashing the whole bridge";
    homepage = "https://github.com/supercorp-ai/supergateway";
  };
}
