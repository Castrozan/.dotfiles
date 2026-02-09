{
  pkgs,
  inputs,
  isNixOS,
  ...
}:
let
  defaultModel = "base.en";
  defaultBackend = "whisper-cpp";

  whisp-awayPackage = pkgs.callPackage "${inputs.whisp-away}/build.nix" {
    inherit (pkgs) rustPlatform addDriverRunpath;
    accelerationType = "vulkan";
    whisper-cpp = null;
    useCrane = false;
  };

  nixVulkanWrapper = inputs.nixgl.packages.${pkgs.stdenv.hostPlatform.system}.nixVulkanIntel;

  whisp-away-vulkan = pkgs.writeShellScriptBin "whisp-away" ''
    exec ${nixVulkanWrapper}/bin/nixVulkanIntel ${whisp-awayPackage}/bin/whisp-away "$@"
  '';

  whisp-away-wrapped = pkgs.symlinkJoin {
    name = "whisp-away-wrapped";
    paths = [
      whisp-away-vulkan
      whisp-awayPackage
    ];
  };

  finalPackage = if isNixOS then whisp-awayPackage else whisp-away-wrapped;
in
{
  home.packages = [ finalPackage ];

  xdg.configFile."whisp-away/config.json".text = builtins.toJSON {
    default_model = defaultModel;
    default_backend = defaultBackend;
    use_clipboard = false;
  };

  home.sessionVariables = {
    WA_WHISPER_MODEL = defaultModel;
    WA_WHISPER_BACKEND = defaultBackend;
    WA_WHISPER_SOCKET = "/tmp/whisp-away-daemon.sock";
    WA_USE_CLIPBOARD = "false";
  };

  systemd.user.tmpfiles.rules = [
    "d %h/.cache/faster-whisper 0755 - - -"
    "d %h/.cache/whisper-cpp 0755 - - -"
    "d %h/.cache/whisper-cpp/models 0755 - - -"
  ];
}
