{
  pkgs,
  ...
}:
{
  home.sessionVariables = {
    MOZ_DISABLE_RDD_SANDBOX = "1";
  };

  programs.firefox = {
    enable = true;
    package = pkgs.firefox;

    policies = {
      DisableTelemetry = true;
      DisableFirefoxStudies = true;
      DisablePocket = true;
      DisableFirefoxAccounts = false;
      DisableSetDesktopBackground = true;
      DisplayBookmarksToolbar = "newtab";
      DontCheckDefaultBrowser = true;
      EnableTrackingProtection = {
        Value = true;
        Locked = true;
        Cryptomining = true;
        Fingerprinting = true;
        EmailTracking = true;
      };
      OfferToSaveLogins = false;
      PasswordManagerEnabled = false;
      FirefoxHome = {
        Search = true;
        TopSites = false;
        SponsoredTopSites = false;
        Highlights = false;
        Pocket = false;
        SponsoredPocket = false;
        Snippets = false;
      };
      FirefoxSuggest = {
        WebSuggestions = false;
        SponsoredSuggestions = false;
        ImproveSuggest = false;
      };
      UserMessaging = {
        ExtensionRecommendations = false;
        FeatureRecommendations = false;
        SkipOnboarding = true;
      };
      HttpsOnlyMode = "enabled";
      ExtensionSettings = {
        "uBlock0@raymondhill.net" = {
          install_url = "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi";
          installation_mode = "force_installed";
        };

        "jid1-MnnxcxisBPnSXQ@jetpack" = {
          install_url = "https://addons.mozilla.org/firefox/downloads/latest/privacy-badger17/latest.xpi";
          installation_mode = "force_installed";
        };
        "addon@darkreader.org" = {
          install_url = "https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi";
          installation_mode = "force_installed";
        };
      };
    };

    profiles.default = {
      isDefault = true;

      settings = {
        "browser.startup.homepage" = "about:home";
        "browser.newtabpage.enabled" = true;

        "gfx.webrender.all" = true;
        "gfx.webrender.enabled" = true;
        "layers.acceleration.force-enabled" = true;
        "gfx.x11-egl.force-enabled" = true;
        "media.ffmpeg.vaapi.enabled" = true;
        "media.hardware-video-decoding.force-enabled" = true;
        "media.rdd-ffmpeg.enabled" = true;
        "widget.dmabuf.force-enabled" = true;
        "gfx.canvas.accelerated" = true;
        "gfx.canvas.accelerated.cache-items" = 4096;
        "gfx.canvas.accelerated.cache-size" = 512;
        "gfx.content.skia-font-cache-size" = 20;

        "browser.cache.disk.enable" = true;
        "browser.cache.memory.enable" = true;
        "browser.cache.memory.capacity" = 524288;
        "network.http.max-connections" = 1800;
        "network.http.max-persistent-connections-per-server" = 10;
        "network.http.max-urgent-start-excessive-connections-per-host" = 5;
        "network.http.pacing.requests.enabled" = false;
        "network.dns.disablePrefetch" = false;
        "network.prefetch-next" = true;
        "network.predictor.enabled" = true;
        "network.predictor.enable-prefetch" = true;

        "javascript.options.baselinejit" = true;
        "javascript.options.ion" = true;
        "javascript.options.wasm" = true;
        "javascript.options.wasm_optimizingjit" = true;

        "dom.ipc.processCount" = 8;
        "browser.preferences.defaultPerformanceSettings.enabled" = false;

        "general.smoothScroll" = true;
        "general.smoothScroll.msdPhysics.enabled" = true;
        "mousewheel.default.delta_multiplier_y" = 275;

        "browser.contentblocking.category" = "strict";
        "privacy.trackingprotection.enabled" = true;
        "privacy.trackingprotection.socialtracking.enabled" = true;
        "privacy.trackingprotection.cryptomining.enabled" = true;
        "privacy.trackingprotection.fingerprinting.enabled" = true;
        "privacy.donottrackheader.enabled" = true;
        "privacy.globalprivacycontrol.enabled" = true;
        "privacy.resistFingerprinting" = false;

        "network.cookie.cookieBehavior" = 5;
        "privacy.clearOnShutdown.history" = false;
        "privacy.clearOnShutdown.cookies" = false;
        "privacy.clearOnShutdown.cache" = false;

        "dom.security.https_only_mode" = true;
        "dom.security.https_only_mode_ever_enabled" = true;
        "security.OCSP.enabled" = 1;
        "security.ssl.require_safe_negotiation" = true;

        "datareporting.healthreport.uploadEnabled" = false;
        "datareporting.policy.dataSubmissionEnabled" = false;
        "toolkit.telemetry.enabled" = false;
        "toolkit.telemetry.unified" = false;
        "toolkit.telemetry.archive.enabled" = false;
        "app.shield.optoutstudies.enabled" = false;

        "extensions.pocket.enabled" = false;
        "browser.newtabpage.activity-stream.feeds.section.topstories" = false;
        "browser.newtabpage.activity-stream.showSponsored" = false;
        "browser.newtabpage.activity-stream.showSponsoredTopSites" = false;

        "media.autoplay.default" = 5;

        "browser.tabs.loadInBackground" = true;
        "browser.tabs.unloadOnLowMemory" = true;
        "browser.aboutConfig.showWarning" = false;
        "browser.shell.checkDefaultBrowser" = false;
        "browser.toolbars.bookmarks.visibility" = "newtab";
        "browser.urlbar.suggest.engines" = false;
        "browser.urlbar.suggest.topsites" = false;

        "full-screen-api.transition-duration.enter" = "0 0";
        "full-screen-api.transition-duration.leave" = "0 0";
        "full-screen-api.warning.timeout" = 0;
      };

      search = {
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
      };
    };
  };
}
