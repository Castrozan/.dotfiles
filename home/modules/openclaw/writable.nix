{ lib, config, ... }:
let
  ws = "${config.home.homeDirectory}/clawd";
in
{
  home.activation.openclawWritableFiles = lib.hm.dag.entryAfter [ "writeBoundary" ] ''
    mkdir -p "${ws}/memory" "${ws}/projects" "${ws}/research"

    if [ ! -f "${ws}/MEMORY.md" ]; then
      cat > "${ws}/MEMORY.md" << 'INITIAL'
# MEMORY.md — Long-Term Memory

_No memories yet. This file will be populated as I learn._
INITIAL
    fi

    if [ ! -f "${ws}/TOOLS.md" ]; then
      cat > "${ws}/TOOLS.md" << 'INITIAL'
# TOOLS.md - Local Notes

_Operational notes will be added here as tools are configured._
INITIAL
    fi

    if [ ! -f "${ws}/HEARTBEAT.md" ]; then
      cat > "${ws}/HEARTBEAT.md" << 'INITIAL'
# HEARTBEAT.md

_No active heartbeat tasks._
INITIAL
    fi
  '';
}
