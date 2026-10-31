{ pkgs }:
let
  piperVoices = "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0";
  fetchVoiceFile =
    voicePath: extension: sha256:
    pkgs.fetchurl {
      url = "${piperVoices}/${voicePath}.${extension}";
      inherit sha256;
    };
  linkVoice =
    {
      name,
      voicePath,
      modelHash,
      configurationHash,
    }:
    ''
      ln -s ${fetchVoiceFile voicePath "onnx" modelHash} $out/${name}.onnx
      ln -s ${fetchVoiceFile voicePath "onnx.json" configurationHash} $out/${name}.onnx.json
    '';
in
pkgs.runCommand "avatar-speech-voices" { } ''
  mkdir $out
  ${linkVoice {
    name = "pt_BR-faber-medium";
    voicePath = "pt/pt_BR/faber/medium/pt_BR-faber-medium";
    modelHash = "19ssz4rkmx6abrfw805a7v859p63qiqbvrlg11brq834l3imb1c5";
    configurationHash = "0vqx1baz0y5r0rawp4s8hm4vcjgv0kmlbi1jsxnw6gxfjphlssby";
  }}
  ${linkVoice {
    name = "en_US-lessac-medium";
    voicePath = "en/en_US/lessac/medium/en_US-lessac-medium";
    modelHash = "17q1mzm6xd5i2rxx2xwqkxvfx796kmp1lvk4mwkph602k7k0kzjy";
    configurationHash = "184hnvd8389xpdm0x2w6phss23v5pb34i0lhd4nmy1gdgd0rrqgg";
  }}
''
