{
  pkgs,
  config,
  lib,
  hostname,
  ...
}:
let
  privateConfigRoot = ../../../private-configuration;
  kubeconfigSourcePath = "${toString privateConfigRoot}/machines/${hostname}/kubeconfig";
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
