{ pkgs }:
let
  sampleCharacter =
    {
      name,
      sample,
      hash,
      description,
      cloudVoice,
      localVoice,
    }:
    {
      inherit
        name
        description
        cloudVoice
        localVoice
        ;
      model = pkgs.fetchurl {
        name = "${name}.vrm";
        url = "https://raw.githubusercontent.com/madjin/vrm-samples/e16eb187100149a315ad92c3c9968f1d5baa6c7d/vroid/beta/${sample}.vrm";
        inherit hash;
      };
    };
in
map sampleCharacter [
  {
    name = "darkness-shibu";
    description = "Young woman, crimson bob, dark ornate dress; bright playful voice";
    sample = "Darkness_Shibu";
    hash = "sha256-C1BXPS0FTZjApvxaXOhy4bLIv/hxhHb/cqmmjEhnT9g=";
    cloudVoice = "cgSgspJ2msm6clMCkdW9";
    localVoice = "pf_dora";
  }
  {
    name = "sendagaya-shino";
    description = "Young woman, long black hair, school uniform; velvety theatrical voice";
    sample = "Sendagaya_Shino";
    hash = "sha256-Hhd8GnsU94OpxIOVgx24YWJg073dQVTLJ4S3ea3KSbU=";
    cloudVoice = "pFZP5JQG7iQjIQuC4Bku";
    localVoice = "pf_dora";
  }
  {
    name = "victoria-rubin";
    description = "Young woman, blonde ponytail, frilled white dress; knowledgeable professional voice";
    sample = "Victoria_Rubin";
    hash = "sha256-sTchMb2/Iz9GMgFG1WXzQqfk9vS48q77MB8aKD7Afh4=";
    cloudVoice = "XrExE9yKIg1WjnnlVkGX";
    localVoice = "pf_dora";
  }
  {
    name = "vita";
    description = "Young woman, short silver hair, futuristic armor; clear engaging voice";
    sample = "Vita";
    hash = "sha256-8r948ook4vdfXKC2w7ZGZUw5TksDWS36oNBjPvCXK00=";
    cloudVoice = "Xb7hH8MSUJpSbSDYk0k2";
    localVoice = "pf_dora";
  }
  {
    name = "vivi";
    description = "Girl, brown bob, folk dress; quirky enthusiastic voice";
    sample = "Vivi";
    hash = "sha256-6vkC4EGnqBDxQjWZrnVoL2EYSrbvAgbamo7ZyqjsOp0=";
    cloudVoice = "FGY2WhTYpPnrIDTdsKH5";
    localVoice = "pf_dora";
  }
  {
    name = "sakurada-fumiriya";
    description = "Young man, light brown hair, school vest; energetic voice";
    sample = "Sakurada_Fumiriya";
    hash = "sha256-2PsF8z43ffAoy2udWMRBzmgybEH6I/bHNdQMZa49xxA=";
    cloudVoice = "TX3LPaxmHKxFdv7VOQHJ";
    localVoice = "pm_alex";
  }
  {
    name = "hair-sample-male";
    description = "Young man, black hair, white hoodie; relaxed optimistic voice";
    sample = "HairSample_Male";
    hash = "sha256-euyhQtq7wmug9bnJmMjzy23zQSh9Z3iEJ6yDciN4Wj8=";
    cloudVoice = "bIHbv24MWmeRgasZH58o";
    localVoice = "pm_santa";
  }
]
