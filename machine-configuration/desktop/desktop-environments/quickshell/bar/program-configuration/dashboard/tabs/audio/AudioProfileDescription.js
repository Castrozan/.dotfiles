function shorten(description) {
  if (description.includes("SBC-XQ")) return "SBC-XQ";
  if (description.includes("SBC")) return "SBC";
  if (description.includes("AAC")) return "AAC";
  if (description.includes("mSBC")) return "mSBC";
  if (description.includes("CVSD")) return "CVSD";
  if (description.includes("LDAC")) return "LDAC";
  if (description.includes("aptX HD")) return "aptX HD";
  if (description.includes("aptX")) return "aptX";
  if (description.includes("A2DP")) return "A2DP";
  if (description.includes("HSP") || description.includes("HFP"))
    return "HSP/HFP";
  if (description.includes("Headset Head Unit")) return "Headset";
  if (description.includes("High Fidelity")) return "HiFi";
  return description.length > 12
    ? description.substring(0, 10) + "…"
    : description;
}
