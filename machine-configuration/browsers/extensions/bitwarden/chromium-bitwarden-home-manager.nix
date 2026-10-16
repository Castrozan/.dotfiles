# Configuration-only: Chromium remains owned by the host/platform.
{
  programs.chromium = {
    enable = true;
    package = null;
    extensions = [
      {
        id = "nngceckbapebfimnlniiiahkandclblb";
        updateUrl = "https://clients2.google.com/service/update2/crx";
      }
    ];
  };
}
