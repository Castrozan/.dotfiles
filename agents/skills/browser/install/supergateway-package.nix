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

  meta = {
    description = "Pristine pinned supergateway stdio-to-streamableHttp MCP bridge (no in-place patches)";
    homepage = "https://github.com/supercorp-ai/supergateway";
  };
}
