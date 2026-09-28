{
  pkgs,
  lib,
  inputs,
  ...
}:
let
  agentResumePackage = import ./herdr-agent-resume-package.nix { inherit pkgs lib; };
  herdrPackage = inputs.herdr.packages.${pkgs.stdenv.hostPlatform.system}.default;
in
{
  home.packages = [ agentResumePackage ];
  home.activation.linkHerdrAgentResume = lib.hm.dag.entryAfter [ "linkGeneration" ] ''
    run ${herdrPackage}/bin/herdr plugin link ${agentResumePackage}/share/herdr/plugins/agent-resume --enabled
  '';
}
