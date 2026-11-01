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
    name = "darkness-shibu.vrm";
    url = "https://raw.githubusercontent.com/madjin/vrm-samples/e16eb187100149a315ad92c3c9968f1d5baa6c7d/vroid/beta/Darkness_Shibu.vrm";
    hash = "sha256-C1BXPS0FTZjApvxaXOhy4bLIv/hxhHb/cqmmjEhnT9g=";
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
