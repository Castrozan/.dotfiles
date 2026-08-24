{
  pkgs,
  config,
  lib,
  ...
}:
let
  kubeconfigSourcePath = ../../../private-configuration + "/cloud-services/kubernetes/config";
  kubeconfigSourceExists = builtins.pathExists kubeconfigSourcePath;

  kubeconfigSource = builtins.path {
    path = kubeconfigSourcePath;
    name = "kubeconfig";
  };

  kubeconfigDestination = "${config.home.homeDirectory}/.kube/config";

  deployKubeconfigScript = pkgs.writeShellScript "deploy-kubeconfig" ''
    set -euo pipefail
    mkdir -p "$(dirname "${kubeconfigDestination}")"
    cp -f "${kubeconfigSource}" "${kubeconfigDestination}"
    chmod 600 "${kubeconfigDestination}"
  '';
in
{
  home.activation = lib.mkIf kubeconfigSourceExists {
    deployKubeconfig = config.lib.dag.entryAfter [ "writeBoundary" ] ''
      run ${deployKubeconfigScript}
    '';
  };
}
