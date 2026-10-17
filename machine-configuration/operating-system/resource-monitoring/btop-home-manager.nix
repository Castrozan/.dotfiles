{
  config,
  lib,
  pkgs,
  ...
}:
{
  home.activation.configureBtopMemoryPercent = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    ${pkgs.python312}/bin/python3 - ${lib.escapeShellArg "${config.xdg.configHome}/btop/btop.conf"} <<'PY'
    import re
    import sys
    from pathlib import Path

    configuration_path = Path(sys.argv[1])
    configuration_path.parent.mkdir(parents=True, exist_ok=True)
    configuration = configuration_path.read_text() if configuration_path.exists() else ""
    configuration = re.sub(r"(?m)^[ \t]*proc_mem_bytes[ \t]*=.*\n?", "", configuration)
    configuration_path.write_text(configuration.rstrip("\n") + "\nproc_mem_bytes = False\n")
    PY
  '';
}
