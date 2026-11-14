import { readdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";

// Verdr emits generated evidence as indented JSON; compact only these derived
// documents so the original, hashed source artifacts remain byte-for-byte intact.
export async function compactEvidence(site) {
  const directory = join(site, "evidence");
  for (const name of await readdir(directory)) {
    if (!name.endsWith(".json")) continue;
    const path = join(directory, name);
    const value = JSON.parse(await readFile(path, "utf8"));
    await writeFile(path, JSON.stringify(value));
  }
}
