{ pkgs, lib, ... }:
let
  realXwayland = pkgs.xwayland;

  wrapperDependencies = with pkgs; [
    xauth
    openssl
    coreutils
    hostname
  ];

  extraPath = lib.makeBinPath wrapperDependencies;

  xwaylandAuthWrapper = pkgs.writeScript "Xwayland" (
    builtins.replaceStrings
      [
        "@REAL_XWAYLAND@"
        "@EXTRA_PATH@"
      ]
      [
        "${realXwayland}/bin/Xwayland"
        extraPath
      ]
      (builtins.readFile ../../../bin/xwayland-auth-wrapper)
  );

  xwaylandWithAuth = pkgs.symlinkJoin {
    name = "xwayland-with-auth-${realXwayland.version}";
    paths = [ realXwayland ];
    postBuild = ''
      rm -f $out/bin/Xwayland
      cp ${xwaylandAuthWrapper} $out/bin/Xwayland
      chmod +x $out/bin/Xwayland
    '';
  };
in
{
  home.packages = [ xwaylandWithAuth ];
}
