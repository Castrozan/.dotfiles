{ lib, ... }:
{
  system.activationScripts.postActivation.text = lib.mkAfter ''
    echo "disabling Spotlight metadata indexing on all volumes..." >&2
    /usr/bin/mdutil -a -i off || true
  '';
}
