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
  characters = import ./characters.nix { inherit pkgs; };
  characterCatalog = pkgs.writeText "characters.json" (
    builtins.toJSON (map (character: { inherit (character) name description; }) characters)
  );
  linkCharacter = character: "ln -s ${character.model} $out/characters/${character.name}.vrm";
in
pkgs.runCommand "avatar-renderer" { } ''
  mkdir -p $out/vendor/three $out/vendor/vrm $out/characters
  tar xf ${three} --strip-components=1 -C $out/vendor/three
  tar xf ${vrm} --strip-components=1 -C $out/vendor/vrm
  cp ${./renderer}/* $out/
  ${pkgs.lib.concatMapStringsSep "\n" linkCharacter characters}
  ln -s ${characterCatalog} $out/characters.json
  ln -s ${../../../agent-harness/agent-instructions/skills/workstation/avatar/avatars} $out/portraits
''
