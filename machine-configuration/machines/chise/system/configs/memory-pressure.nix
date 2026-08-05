{ config, ... }:
{
  assertions = [
    {
      assertion = config.zramSwap.enable;
      message = "zram swap is required — with only 16GB RAM and heavy Nix builds, zram provides compressed swap in memory that is 3-5x faster than disk swap and prevents OOM kills during parallel compilation";
    }
    {
      assertion = config.services.earlyoom.enable;
      message = "earlyoom is required — without proactive OOM killing the kernel OOM killer activates too late, freezing the desktop for 30+ seconds before killing a random process instead of the actual memory hog";
    }
    {
      assertion = config.boot.kernel.sysctl."vm.swappiness" >= 100;
      message = "High swappiness (>=100) is required — with zram enabled, swappiness above 100 tells the kernel to prefer compressing pages into zram over evicting file cache, which keeps build artifacts cached and improves rebuild speed";
    }
  ];

  boot.kernel.sysctl."vm.swappiness" = 150;

  zramSwap = {
    enable = true;
    memoryPercent = 50;
    algorithm = "zstd";
  };

  swapDevices = [
    {
      device = "/swapfile";
      size = 4096;
    }
  ];

  services.earlyoom = {
    enable = true;
    freeMemThreshold = 10;
    freeSwapThreshold = 15;
    freeMemKillThreshold = 5;
    freeSwapKillThreshold = 5;
    enableNotifications = true;
    extraArgs = [
      "-r"
      "3600"
      "--avoid"
      "(^|/)(init|Xorg|Xwayland|sshd|systemd)$"
      "--prefer"
      "(^|/)(nix|nix-build|cc1plus|rustc|node|java|chrome_crashpad|claude)$"
    ];
  };
}
