{ pkgs }:
let
  sampleModel =
    name: sample: hash:
    pkgs.fetchurl {
      name = "${name}.vrm";
      url = "https://raw.githubusercontent.com/madjin/vrm-samples/e16eb187100149a315ad92c3c9968f1d5baa6c7d/vroid/${sample}.vrm";
      inherit hash;
    };
in
{
  darkness-shibu =
    sampleModel "darkness-shibu" "beta/Darkness_Shibu"
      "sha256-C1BXPS0FTZjApvxaXOhy4bLIv/hxhHb/cqmmjEhnT9g=";
  sendagaya-shino =
    sampleModel "sendagaya-shino" "beta/Sendagaya_Shino"
      "sha256-Hhd8GnsU94OpxIOVgx24YWJg073dQVTLJ4S3ea3KSbU=";
  sendagaya-shibu =
    sampleModel "sendagaya-shibu" "beta/Sendagaya_Shibu"
      "sha256-t7ytXliQq8TXxl+a/DHaJEXbAxl9RPHsEER/nbWr6v8=";
  victoria-rubin =
    sampleModel "victoria-rubin" "beta/Victoria_Rubin"
      "sha256-sTchMb2/Iz9GMgFG1WXzQqfk9vS48q77MB8aKD7Afh4=";
  vita = sampleModel "vita" "beta/Vita" "sha256-8r948ook4vdfXKC2w7ZGZUw5TksDWS36oNBjPvCXK00=";
  vivi = sampleModel "vivi" "beta/Vivi" "sha256-6vkC4EGnqBDxQjWZrnVoL2EYSrbvAgbamo7ZyqjsOp0=";
  hair-sample-female =
    sampleModel "hair-sample-female" "beta/HairSample_Female"
      "sha256-rf0kIxeqq8dz8x9//3sBOXn7tbqkfpdCeniRPZy06Xk=";
  avatar-sample-a =
    sampleModel "avatar-sample-a" "stable/AvatarSample_A"
      "sha256-uGsLimbUiRFDHW+SClIRqXQib4OqZy7KPz363lisNG4=";
  avatar-sample-b =
    sampleModel "avatar-sample-b" "stable/AvatarSample_B"
      "sha256-Sicb07Wj0Z4FT9ET7hVGNbcucUH0qMy826PH+c6m7o0=";
  sakurada-fumiriya =
    sampleModel "sakurada-fumiriya" "beta/Sakurada_Fumiriya"
      "sha256-2PsF8z43ffAoy2udWMRBzmgybEH6I/bHNdQMZa49xxA=";
  hair-sample-male =
    sampleModel "hair-sample-male" "beta/HairSample_Male"
      "sha256-euyhQtq7wmug9bnJmMjzy23zQSh9Z3iEJ6yDciN4Wj8=";
  avatar-sample-c =
    sampleModel "avatar-sample-c" "stable/AvatarSample_C"
      "sha256-OV1bBGluiI8HvIVq4Bv3KpdLfncxMsdEPcWdFogEW4o=";
}
