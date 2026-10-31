{ pkgs }:
let
  three = pkgs.fetchurl {
    url = "https://registry.npmjs.org/three/-/three-0.149.0.tgz";
    hash = "sha512-tohpUxPDht0qExRLDTM8sjRLc5d9STURNrdnK3w9A+V4pxaTBfKWWT/IqtiLfg23Vfc3Z+ImNfvRw1/0CtxrkQ==";
  };
  vrm = pkgs.fetchurl {
    url = "https://registry.npmjs.org/@pixiv/three-vrm/-/three-vrm-1.0.9.tgz";
    hash = "sha512-OXExupt3p/6oT3acM236Z5f6nVGAU0nYz2Al8UZXkaZKwVklaIBTCy0iC+57PFTkdpj+6Urxa9CiWagKg3ihXA==";
  };
  model = pkgs.fetchurl {
    name = "avatar-original.vrm";
    url = "https://gateway.pinata.cloud/ipfs/bafybeihx4xjb5mphocdq2os63g43pgnpi46ynolpmhln3oycoasywdnl3u";
    hash = "sha256-f8pKd/3GCrLHipkHQwdEViYmGAEl+jhut0+y6hXC5Rg=";
  };
in
pkgs.runCommand "avatar-renderer" { } ''
  mkdir -p $out/vendor/three $out/vendor/vrm
  tar xf ${three} --strip-components=1 -C $out/vendor/three
  tar xf ${vrm} --strip-components=1 -C $out/vendor/vrm
  cp ${./renderer}/* $out/
  ln -s ${model} $out/model.vrm
  ln -s ${../../../agent-harness/agent-instructions/skills/workstation/avatar/avatars} $out/portraits
''
