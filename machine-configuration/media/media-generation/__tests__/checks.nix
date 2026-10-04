{ pkgs, ... }:
let
  testPython = pkgs.python312.withPackages (pythonPackages: [
    pythonPackages.pytest
    pythonPackages.elevenlabs
  ]);
in
{
  domain-media-speech-contract = pkgs.runCommand "domain-media-speech-contract" { } ''
    export PYTHONDONTWRITEBYTECODE=1
    cp -R ${../.} source
    chmod -R u+w source
    cd source
    ${testPython}/bin/python3 -m pytest -q -p no:cacheprovider \
      __tests__/unit/test_speech_contract.py \
      __tests__/unit/test_speech_discovery.py \
      __tests__/unit/test_speech_service.py \
      __tests__/integration/test_elevenlabs_adapter.py \
      __tests__/integration/test_elevenlabs_voice_catalog.py
    touch "$out"
  '';
}
