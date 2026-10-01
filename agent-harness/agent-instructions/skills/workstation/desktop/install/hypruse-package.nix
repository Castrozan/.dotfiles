{ pkgs }:
pkgs.python312Packages.buildPythonApplication {
  pname = "hypruse";
  version = "0.11.0";
  pyproject = true;
  src = pkgs.fetchFromGitHub {
    owner = "IlyasKhallouki";
    repo = "hypruse";
    rev = "v0.11.0";
    hash = "sha256-MjDpzB5qDPHnPYOzxg9pa5mAzjb1SMvo67kFLq8pU2k=";
  };
  build-system = [ pkgs.python312Packages.hatchling ];
  dependencies = [ pkgs.python312Packages.mcp ];
  nativeBuildInputs = [ pkgs.makeWrapper ];
  pythonImportsCheck = [ "hypruse.server" ];
  postFixup = ''
    wrapProgram "$out/bin/hypruse" \
      --prefix PATH : ${
        pkgs.lib.makeBinPath [
          pkgs.hyprland
          pkgs.grim
          pkgs.wtype
          pkgs.systemd
          pkgs.imagemagick
          pkgs.wl-clipboard
        ]
      } \
      --set HYPRUSE_SCREENSHOT_MODE image
  '';
  doInstallCheck = true;
  installCheckPhase = ''
    ${pkgs.python312.interpreter} ${./__tests__/mcp-smoke.py} "$out/bin/hypruse" desktop screenshot ui pointer keyboard
  '';
  meta = {
    description = "Native Hyprland desktop control over MCP";
    homepage = "https://github.com/IlyasKhallouki/hypruse";
    license = pkgs.lib.licenses.mit;
    platforms = pkgs.lib.platforms.linux;
    mainProgram = "hypruse";
  };
}
