{
  pkgs,
  inputs,
  ...
}:
{
  home.packages = [
    (
      if pkgs.stdenv.hostPlatform.isDarwin then
        pkgs.cmatrix
      else
        inputs.cmatrix.packages.${pkgs.stdenv.hostPlatform.system}.default
    )
  ];
}
