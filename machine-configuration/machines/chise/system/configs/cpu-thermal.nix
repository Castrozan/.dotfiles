let
  cpuBoostPath = "/sys/devices/system/cpu/cpufreq/boost";
in
{
  powerManagement.powerUpCommands = ''
    if test -w ${cpuBoostPath}; then
      printf '0\n' > ${cpuBoostPath}
    fi
  '';
}
