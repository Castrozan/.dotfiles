import { readFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";
import { requiredEvidenceIds } from "./evidence_inputs.mjs";

export function incompleteEvidence(overview) {
  return requiredEvidenceIds.filter((id) => {
    const matches = overview.evidence.filter((item) => item.id === id);
    return matches.length !== 1 || !matches[0].usable;
  });
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  const payload = JSON.parse(await readFile(process.argv[2], "utf8"));
  const missing = incompleteEvidence(payload.overview);
  if (missing.length) {
    console.error(`Required evidence unavailable: ${missing.join(", ")}`);
    process.exitCode = 1;
  } else {
    console.log(
      `${requiredEvidenceIds.length}/${requiredEvidenceIds.length} required evidence items are usable`,
    );
  }
}
