{ pkgs }:
let
  frequencyWords =
    language: hash:
    pkgs.fetchurl {
      url = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/525f9b560de45753a5ea01069454e72e9aa541c6/content/2018/${language}/${language}_50k.txt";
      inherit hash;
    };
in
builtins.concatStringsSep ":" [
  (frequencyWords "en" "sha256-U1H/QFsRJu9VV5HdTZeYpI4+mlAan8SBqdqVd1LPtFg=")
  (frequencyWords "pt_br" "sha256-ph1vLt6XxdqtX7OQe3KiKPCv8SZovm0k2lkNIIBPphE=")
]
