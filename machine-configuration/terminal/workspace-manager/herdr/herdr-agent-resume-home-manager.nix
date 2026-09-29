{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  agentResumePackage = import ./herdr-agent-resume-package.nix { inherit pkgs lib; };
  herdrPackage = import ./herdr-package.nix { inherit pkgs inputs; };
in
{
  home.packages = [ agentResumePackage ];
  home.activation.linkHerdrAgentResume = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    run ${herdrPackage}/bin/herdr plugin link ${agentResumePackage}/share/herdr/plugins/agent-resume --enabled
  '';
}
