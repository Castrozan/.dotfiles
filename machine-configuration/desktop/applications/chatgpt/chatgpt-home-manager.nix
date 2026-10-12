{
  pkgs,
  lib,
  isNixOS,
  ...
}:
let
  chatgpt = pkgs.callPackage ./package.nix { };
  resourceControlSource = pkgs.writeText "chatgpt-resource-control.py" (
    builtins.readFile ./scripts/chatgpt_resource_control.py
  );
  resourcePolicyModules = pkgs.linkFarm "chatgpt-resource-policy-modules" (
    map
      (source: {
        name = builtins.baseNameOf source;
        path = source;
      })
      [
        ./scripts/chatgpt_memory_policy.py
        ./scripts/chatgpt_processes.py
        ./scripts/chatgpt_resource_scope.py
        ./scripts/chatgpt_window_observer.py
      ]
  );
  resourceLauncher = pkgs.writeShellScriptBin "chatgpt" ''
    export PATH="${lib.makeBinPath [ pkgs.systemd ]}:$PATH"
    export PYTHONPATH="${resourcePolicyModules}:''${PYTHONPATH:-}"
    chatgpt_resource_unit="app-chatgpt-$BASHPID-$RANDOM"
    exec ${pkgs.systemd}/bin/systemd-run --user --scope --quiet --collect \
      --unit="$chatgpt_resource_unit" --property=MemoryAccounting=yes --property=Delegate=memory \
      --property=MemoryHigh=4G --property=MemoryMax=infinity --property=MemorySwapMax=infinity \
      ${pkgs.python312}/bin/python3 ${resourceControlSource} \
      "$chatgpt_resource_unit.scope" ${chatgpt}/bin/chatgpt "$@"
  '';
  resourceManagedChatgpt = pkgs.symlinkJoin {
    name = "chatgpt-resource-managed";
    paths = [ resourceLauncher ];
    postBuild = ''
      mkdir -p "$out/share/applications" "$out/share/pixmaps"
      cp ${chatgpt}/share/applications/chatgpt.desktop "$out/share/applications/"
      cp ${chatgpt}/share/pixmaps/chatgpt.png "$out/share/pixmaps/"
      substituteInPlace "$out/share/applications/chatgpt.desktop" \
        --replace-fail "Exec=${chatgpt}/bin/chatgpt %U" "Exec=$out/bin/chatgpt %U"
    '';
    inherit (chatgpt) meta;
  };
in
{
  config = lib.mkIf isNixOS {
    home.packages = [ resourceManagedChatgpt ];
    xdg.dataFile."applications/chatgpt.desktop".source =
      "${resourceManagedChatgpt}/share/applications/chatgpt.desktop";
  };
}
