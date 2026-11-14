{ pkgs }:
let
  models = import ./models.nix { inherit pkgs; };
  woman =
    attributes:
    attributes
    // {
      gender = "female";
      localVoice = "pf_dora";
    };
  man = attributes: attributes // { gender = "male"; };
in
[
  (woman {
    name = "darkness-shibu";
    description = "Young woman, crimson bob, dark ornate dress; bright playful voice";
    model = models.darkness-shibu;
    cloudVoice = "cgSgspJ2msm6clMCkdW9";
    liveVoice = "delta";
  })
  (woman {
    name = "sendagaya-shino";
    description = "Young woman, long black hair, school uniform; velvety theatrical voice";
    model = models.sendagaya-shino;
    cloudVoice = "pFZP5JQG7iQjIQuC4Bku";
    liveVoice = "willow";
  })
  (woman {
    name = "sendagaya-shibu";
    description = "Young woman, black bob, school uniform; mature confident voice";
    model = models.sendagaya-shibu;
    cloudVoice = "EXAVITQu4vr4xnSDxMaL";
    liveVoice = "quartz";
  })
  (woman {
    name = "victoria-rubin";
    description = "Young woman, blonde ponytail, frilled white dress; knowledgeable professional voice";
    model = models.victoria-rubin;
    cloudVoice = "XrExE9yKIg1WjnnlVkGX";
    liveVoice = "gleam";
  })
  (woman {
    name = "vita";
    description = "Young woman, short silver hair, futuristic armor; clear engaging voice";
    model = models.vita;
    cloudVoice = "Xb7hH8MSUJpSbSDYk0k2";
    liveVoice = "bossa";
  })
  (woman {
    name = "vivi";
    description = "Girl, brown bob, folk dress; quirky enthusiastic voice";
    model = models.vivi;
    cloudVoice = "FGY2WhTYpPnrIDTdsKH5";
    liveVoice = "delta";
  })
  (woman {
    name = "hair-sample-female";
    description = "Young woman, black twin tails, cat ears; clear engaging voice";
    model = models.hair-sample-female;
    cloudVoice = "Xb7hH8MSUJpSbSDYk0k2";
    liveVoice = "willow";
  })
  (woman {
    name = "avatar-sample-a";
    description = "Young woman, short brown hair, gentle face; warm bright voice";
    model = models.avatar-sample-a;
    cloudVoice = "hpp4J3VqNfWAUOO0d1Us";
    liveVoice = "bossa";
  })
  (woman {
    name = "avatar-sample-b";
    description = "Young woman, long purple hair, horns and star clips; playful bright voice";
    model = models.avatar-sample-b;
    cloudVoice = "cgSgspJ2msm6clMCkdW9";
    liveVoice = "gleam";
  })
  (man {
    name = "sakurada-fumiriya";
    description = "Young man, light brown hair, school vest; energetic voice";
    model = models.sakurada-fumiriya;
    cloudVoice = "TX3LPaxmHKxFdv7VOQHJ";
    localVoice = "pm_alex";
    liveVoice = "meridian";
  })
  (man {
    name = "sakurada-fumiriya-chris";
    description = "Young man, light brown hair, school vest; charming down-to-earth voice";
    model = models.sakurada-fumiriya;
    cloudVoice = "iP95p4xoKVk53GoZ742B";
    localVoice = "pm_santa";
    liveVoice = "stone";
  })
  (man {
    name = "sakurada-fumiriya-callum";
    description = "Young man, light brown hair, school vest; husky trickster voice";
    model = models.sakurada-fumiriya;
    cloudVoice = "N2lVS1w4EtoT3dr4eOWO";
    localVoice = "pm_alex";
    liveVoice = "vesper";
  })
  (man {
    name = "sakurada-fumiriya-charlie";
    description = "Young man, light brown hair, school vest; deep confident energetic voice";
    model = models.sakurada-fumiriya;
    cloudVoice = "IKne3meq5aSn9XLyUdCD";
    localVoice = "pm_santa";
    liveVoice = "ripple";
  })
  (man {
    name = "hair-sample-male";
    description = "Young man, black hair, white hoodie; relaxed optimistic voice";
    model = models.hair-sample-male;
    cloudVoice = "bIHbv24MWmeRgasZH58o";
    localVoice = "pm_santa";
    liveVoice = "tempo";
  })
  (man {
    name = "hair-sample-male-roger";
    description = "Young man, black hair, white hoodie; laid-back resonant voice";
    model = models.hair-sample-male;
    cloudVoice = "CwhRBWXzGAHq8TQ4Fs17";
    localVoice = "pm_alex";
    liveVoice = "cinder";
  })
  (man {
    name = "hair-sample-male-eric";
    description = "Young man, black hair, white hoodie; smooth trustworthy voice";
    model = models.hair-sample-male;
    cloudVoice = "cjVigY5qzO86Huf0OWal";
    localVoice = "pm_santa";
    liveVoice = "beacon";
  })
  (man {
    name = "hair-sample-male-daniel";
    description = "Young man, black hair, white hoodie; steady broadcaster voice";
    model = models.hair-sample-male;
    cloudVoice = "onwK4e9ZLuTAKqWW03F9";
    localVoice = "pm_alex";
    liveVoice = "meridian";
  })
  (man {
    name = "avatar-sample-c";
    description = "Young man, dark shaggy hair, red eyes, black coat; fierce warrior voice";
    model = models.avatar-sample-c;
    cloudVoice = "SOYHLrjzK2X1ezoPC6cr";
    localVoice = "pm_santa";
    liveVoice = "stone";
  })
  (man {
    name = "avatar-sample-c-george";
    description = "Young man, dark shaggy hair, red eyes, black coat; warm storyteller voice";
    model = models.avatar-sample-c;
    cloudVoice = "JBFqnCBsd6RMkjVDRZzb";
    localVoice = "pm_alex";
    liveVoice = "vesper";
  })
  (man {
    name = "avatar-sample-c-brian";
    description = "Young man, dark shaggy hair, red eyes, black coat; deep resonant comforting voice";
    model = models.avatar-sample-c;
    cloudVoice = "nPczCjzI2devNBz1zQrb";
    localVoice = "pm_santa";
    liveVoice = "tempo";
  })
  (man {
    name = "avatar-sample-c-adam";
    description = "Young man, dark shaggy hair, red eyes, black coat; dominant firm voice";
    model = models.avatar-sample-c;
    cloudVoice = "pNInz6obpgDQGcFmaJgB";
    localVoice = "pm_alex";
    liveVoice = "ripple";
  })
]
