{ lib, ... }:
{
  system.activationScripts.disableSpotlightMetadataIndexing.text = lib.mkAfter ''
    echo "disabling Spotlight metadata indexing on all volumes..." >&2
    /usr/bin/mdutil -a -i off || true
    /usr/bin/mdutil -a -E || true
  '';
}
