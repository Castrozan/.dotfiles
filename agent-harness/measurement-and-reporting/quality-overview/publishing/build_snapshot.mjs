import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { artifactInputs } from "./artifact_inputs.mjs";
import { conventionalInputs } from "./evidence_inputs.mjs";
import { remainingGaps } from "./remaining_gaps.mjs";

const [verdrLocation, contextLocation, downloadsLocation, outputLocation] =
  process.argv.slice(2);
const context = JSON.parse(await readFile(contextLocation, "utf8"));
const downloads = resolve(downloadsLocation);
const output = resolve(outputLocation);
const load = (path) =>
  import(pathToFileURL(join(resolve(verdrLocation), "dist", path)).href);
const { overviewManifestSchema } = await load("overview/manifest.js");
const { buildOverview } = await load("overview/build.js");
const { workflow } = context;
const detailsBaseUrl = `https://storage.googleapis.com/zg-url-shortener-2026-dotfiles-usage-snapshots/reports/overview/${workflow.runId}/${workflow.runAttempt}/`;
const artifact = await artifactInputs(
  context,
  downloads,
  detailsBaseUrl,
  overviewManifestSchema,
);
const manifest = overviewManifestSchema.parse({
  schemaVersion: 1,
  name: "Dotfiles quality overview",
  subject: {
    repository: workflow.repository,
    revision: workflow.revision,
    artifactDigest: artifact.artifactDigest,
  },
  inputs: [
    ...artifact.inputs,
    ...conventionalInputs(context, detailsBaseUrl),
    ...remainingGaps(context),
  ],
});
await mkdir(output);
await mkdir(join(output, "raw"));
for (const [name, selection] of Object.entries(context.artifacts)) {
  if (!selection.id) continue;
  const source =
    name === "verdr-artifact-evidence"
      ? join(downloads, name, "artifact-evidence")
      : join(downloads, name);
  const target =
    name === "verdr-artifact-evidence"
      ? join(output, "raw", name, "artifact-evidence")
      : join(output, "raw", name);
  try {
    await cp(source, target, {
      recursive: true,
      errorOnExist: true,
      force: false,
    });
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
}
await mkdir(join(output, "configuration"));
await writeFile(
  join(output, "configuration/manifest.json"),
  JSON.stringify(manifest, null, 2),
  { flag: "wx" },
);
const site = join(output, "site");
const overview = await buildOverview(
  manifest,
  site,
  join(output, "configuration"),
);
await cp(join(output, "raw"), join(site, "raw"), { recursive: true });
await writeFile(
  join(output, "payload.json"),
  JSON.stringify({ overview, workflow, detailsBaseUrl }, null, 2),
  { flag: "wx" },
);
console.log(
  `${overview.evidence.length} independent evidence items retained for ${workflow.runId}/${workflow.runAttempt}`,
);
