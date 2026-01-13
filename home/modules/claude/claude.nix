{ latest, ... }:
{
  home.packages = with latest; [
    claude-code
  ];
}
