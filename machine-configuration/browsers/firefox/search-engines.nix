{
  default = "google";
  force = true;
  engines = {
    "Nix Packages" = {
      urls = [
        {
          template = "https://search.nixos.org/packages";
          params = [
            {
              name = "channel";
              value = "unstable";
            }
            {
              name = "query";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "https://nixos.org/favicon.png";
      definedAliases = [ "@np" ];
    };
    "NixOS Options" = {
      urls = [
        {
          template = "https://search.nixos.org/options";
          params = [
            {
              name = "channel";
              value = "unstable";
            }
            {
              name = "query";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "https://nixos.org/favicon.png";
      definedAliases = [ "@no" ];
    };
    "Home Manager Options" = {
      urls = [
        {
          template = "https://home-manager-options.extranix.com";
          params = [
            {
              name = "query";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      definedAliases = [ "@hm" ];
    };
    "youtube" = {
      urls = [
        {
          template = "https://www.youtube.com/results";
          params = [
            {
              name = "search_query";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "https://www.youtube.com/favicon.ico";
      definedAliases = [ "@yt" ];
    };
    "GitHub" = {
      urls = [
        {
          template = "https://github.com/search";
          params = [
            {
              name = "q";
              value = "{searchTerms}";
            }
          ];
        }
      ];
      icon = "https://github.com/favicon.ico";
      definedAliases = [ "@gh" ];
    };
  };
}
