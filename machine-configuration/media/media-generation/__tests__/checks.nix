{ pkgs, ... }:
let
  testPython = pkgs.python312.withPackages (
    pythonPackages:
    [
      pythonPackages.pytest
      pythonPackages.elevenlabs
      pythonPackages.jsonschema
    ]
    ++ (import ../image-python-packages.nix pythonPackages)
  );
  ffmpegPackage = import ../video-ffmpeg-package.nix { inherit pkgs; };
in
{
  domain-media-image-movie-contract = pkgs.runCommand "domain-media-image-movie-contract" { } ''
    export PYTHONDONTWRITEBYTECODE=1
    export MEDIA_MOVIE_FFMPEG=${ffmpegPackage}/bin/ffmpeg
    export MEDIA_MOVIE_FFPROBE=${ffmpegPackage}/bin/ffprobe
    cp -R ${../.} source
    chmod -R u+w source
    cd source
    ${testPython}/bin/python3 -m pytest -q -p no:cacheprovider \
      __tests__/unit/test_image_contract.py \
      __tests__/unit/test_movie_contract.py \
      __tests__/unit/test_movie_jobs.py \
      __tests__/unit/test_media_discovery_cli.py \
      __tests__/unit/test_media_operation_identity.py \
      __tests__/integration/test_image_providers.py \
      __tests__/integration/test_replicate_lifecycle.py \
      __tests__/integration/test_movie_render.py \
      __tests__/integration/test_movie_cli.py \
      __tests__/integration/test_speech_delivery.py
    touch "$out"
  '';
  domain-media-video-contract =
    pkgs.runCommand "domain-media-video-contract"
      {
        nativeBuildInputs = pkgs.lib.optionals pkgs.stdenv.isLinux [ pkgs.procps ];
      }
      ''
        export PYTHONDONTWRITEBYTECODE=1
        cp -R ${../.} source
        chmod -R u+w source
        cd source
        ${testPython}/bin/python3 -m pytest -q -p no:cacheprovider \
          __tests__/unit/test_video_cli.py \
          __tests__/unit/test_video_jobs.py \
          __tests__/unit/test_video_lifecycle.py \
          __tests__/integration/test_video_process.py \
          __tests__/unit/test_video_registration.py \
          __tests__/unit/test_video_verification.py
        touch "$out"
      '';
  domain-media-speech-contract = pkgs.runCommand "domain-media-speech-contract" { } ''
    export PYTHONDONTWRITEBYTECODE=1
    cp -R ${../.} source
    chmod -R u+w source
    cd source
    ${testPython}/bin/python3 -m pytest -q -p no:cacheprovider \
      __tests__/unit/test_speech_contract.py \
      __tests__/unit/test_speech_discovery.py \
      __tests__/unit/test_speech_usage.py \
      __tests__/unit/test_speech_service.py \
      __tests__/integration/test_elevenlabs_adapter.py \
      __tests__/integration/test_elevenlabs_voice_catalog.py \
      __tests__/integration/test_elevenlabs_usage.py
    touch "$out"
  '';
}
