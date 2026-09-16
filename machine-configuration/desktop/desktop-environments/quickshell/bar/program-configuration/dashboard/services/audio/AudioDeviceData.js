function audioDeviceListsAreEqual(oldList, newList) {
  if (oldList.length !== newList.length) return false;
  for (let i = 0; i < oldList.length; i++) {
    const oldItem = oldList[i];
    const newItem = newList[i];
    if (
      oldItem.name !== newItem.name ||
      oldItem.volume !== newItem.volume ||
      oldItem.mute !== newItem.mute ||
      oldItem.state !== newItem.state ||
      oldItem.description !== newItem.description
    )
      return false;
  }
  return true;
}

function extractVolumePercent(volumeObject) {
  if (!volumeObject) return 0;
  const channels = Object.values(volumeObject);
  if (channels.length === 0) return 0;
  const percentString = channels[0].value_percent ?? "0%";
  return Number.parseInt(percentString) || 0;
}

function extractPortType(ports, activePortName) {
  if (!ports || !activePortName) return "";
  for (const port of ports)
    if (port.name === activePortName) return port.type ?? "";
  return "";
}
