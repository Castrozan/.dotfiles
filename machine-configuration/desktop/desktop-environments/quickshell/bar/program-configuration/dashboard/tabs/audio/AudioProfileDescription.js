function shorten(description) {
  const codecGroup = shortenPrimaryCodec(description);
  if (codecGroup) return codecGroup;
  const additionalCodec = shortenAdditionalCodec(description);
  if (additionalCodec) return additionalCodec;
  const profile = shortenAudioProfile(description);
  if (profile) return profile;
  const deviceDescription = shortenDeviceDescription(description);
  if (deviceDescription) return deviceDescription;
  return shortenFallbackDescription(description);
}

function shortenFallbackDescription(description) {
  return description.length > 12
    ? description.substring(0, 10) + "…"
    : description;
}

function shortenPrimaryCodec(description) {
  if (description.includes("SBC-XQ")) return "SBC-XQ";
  if (description.includes("SBC")) return "SBC";
  if (description.includes("AAC")) return "AAC";
  return "";
}

function shortenAdditionalCodec(description) {
  if (description.includes("mSBC")) return "mSBC";
  if (description.includes("CVSD")) return "CVSD";
  if (description.includes("LDAC")) return "LDAC";
  return "";
}

function shortenAudioProfile(description) {
  if (description.includes("aptX HD")) return "aptX HD";
  if (description.includes("aptX")) return "aptX";
  if (description.includes("A2DP")) return "A2DP";
  if (hasHandsFreeProfile(description)) return "HSP/HFP";
  return "";
}

function hasHandsFreeProfile(description) {
  return description.includes("HSP") || description.includes("HFP");
}

function shortenDeviceDescription(description) {
  if (description.includes("Headset Head Unit")) return "Headset";
  if (description.includes("High Fidelity")) return "HiFi";
  return "";
}
