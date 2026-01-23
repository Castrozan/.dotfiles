{
  pkgs,
  ...
}:
{
  home.sessionVariables = {
    PLAYWRIGHT_BROWSERS_PATH = "${pkgs.playwright-driver.browsers}";
    PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";
  };

  home.packages = with pkgs; [
    playwright-driver
    playwright-driver.browsers
  ];
}
