function format(lengthSeconds) {
  if (lengthSeconds < 0) return "-1:-1";

  const hours = Math.floor(lengthSeconds / 3600);
  const mins = Math.floor((lengthSeconds % 3600) / 60);
  const secs = Math.floor(lengthSeconds % 60)
    .toString()
    .padStart(2, "0");

  if (hours > 0) return `${hours}:${mins.toString().padStart(2, "0")}:${secs}`;
  return `${mins}:${secs}`;
}
