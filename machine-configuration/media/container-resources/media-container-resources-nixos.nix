{
  systemd.slices.media-containers = {
    description = "Bounded media containers";
    sliceConfig = {
      MemoryAccounting = true;
      MemoryHigh = "3G";
      MemoryMax = "5G";
      MemorySwapMax = "3G";
    };
  };
}
