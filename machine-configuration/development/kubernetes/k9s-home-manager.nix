{ config, ... }:
{
  programs.k9s = {
    enable = true;

    settings.k9s = {
      liveViewAutoRefresh = false;
      gpuVendors = { };
      screenDumpDir = "${config.xdg.stateHome}/k9s/screen-dumps";
      refreshRate = 2;
      apiServerTimeout = "15s";
      maxConnRetry = 5;
      readOnly = false;
      noExitOnCtrlC = false;
      portForwardAddress = "localhost";
      ui = {
        enableMouse = false;
        headless = false;
        logoless = false;
        crumbsless = false;
        reactive = false;
        noIcons = false;
        defaultsToFullScreen = false;
        useFullGVRTitle = false;
      };
      skipLatestRevCheck = false;
      disablePodCounting = false;
      shellPod = {
        image = "busybox:1.35.0";
        namespace = "default";
        limits = {
          cpu = "100m";
          memory = "100Mi";
        };
      };
      imageScans = {
        enable = false;
        exclusions = {
          namespaces = [ ];
          labels = { };
        };
      };
      logger = {
        tail = 5000;
        buffer = 5000;
        sinceSeconds = 300;
        textWrap = false;
        disableAutoscroll = false;
        showTime = false;
      };
      thresholds = {
        cpu = {
          critical = 90;
          warn = 70;
        };
        memory = {
          critical = 90;
          warn = 70;
        };
      };
      defaultView = "";
    };

    aliases.aliases = {
      dp = "deployments";
      sec = "v1/secrets";
      jo = "jobs";
      cr = "clusterroles";
      crb = "clusterrolebindings";
      ro = "roles";
      rb = "rolebindings";
      np = "networkpolicies";
    };
  };
}
