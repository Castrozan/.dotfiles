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
  sampleCharacter =
    {
      name,
      sample,
      hash,
    }:
    {
      inherit name;
      model = pkgs.fetchurl {
        name = "${name}.vrm";
        url = "https://raw.githubusercontent.com/madjin/vrm-samples/e16eb187100149a315ad92c3c9968f1d5baa6c7d/vroid/beta/${sample}.vrm";
        inherit hash;
      };
    };
  characters = map sampleCharacter [
    {
      name = "darkness-shibu";
      sample = "Darkness_Shibu";
      hash = "sha256-C1BXPS0FTZjApvxaXOhy4bLIv/hxhHb/cqmmjEhnT9g=";
    }
    {
      name = "sendagaya-shino";
      sample = "Sendagaya_Shino";
      hash = "sha256-Hhd8GnsU94OpxIOVgx24YWJg073dQVTLJ4S3ea3KSbU=";
    }
    {
      name = "victoria-rubin";
      sample = "Victoria_Rubin";
      hash = "sha256-sTchMb2/Iz9GMgFG1WXzQqfk9vS48q77MB8aKD7Afh4=";
    }
    {
      name = "vita";
      sample = "Vita";
      hash = "sha256-8r948ook4vdfXKC2w7ZGZUw5TksDWS36oNBjPvCXK00=";
    }
    {
      name = "vivi";
      sample = "Vivi";
      hash = "sha256-6vkC4EGnqBDxQjWZrnVoL2EYSrbvAgbamo7ZyqjsOp0=";
    }
    {
      name = "sakurada-fumiriya";
      sample = "Sakurada_Fumiriya";
      hash = "sha256-2PsF8z43ffAoy2udWMRBzmgybEH6I/bHNdQMZa49xxA=";
    }
    {
      name = "hair-sample-male";
      sample = "HairSample_Male";
      hash = "sha256-euyhQtq7wmug9bnJmMjzy23zQSh9Z3iEJ6yDciN4Wj8=";
    }
  ];
  characterNames = pkgs.writeText "characters.json" (
    builtins.toJSON (map (character: character.name) characters)
  );
  linkCharacter = character: "ln -s ${character.model} $out/characters/${character.name}.vrm";
in
pkgs.runCommand "avatar-renderer" { } ''
  mkdir -p $out/vendor/three $out/vendor/vrm $out/characters
  tar xf ${three} --strip-components=1 -C $out/vendor/three
  tar xf ${vrm} --strip-components=1 -C $out/vendor/vrm
  cp ${./renderer}/* $out/
  ${pkgs.lib.concatMapStringsSep "\n" linkCharacter characters}
  ln -s ${characterNames} $out/characters.json
  ln -s ${../../../agent-harness/agent-instructions/skills/workstation/avatar/avatars} $out/portraits
''
