import { cp, mkdir, readFile, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { artifactInputs } from "./artifact_inputs.mjs";
import { conventionalInputs } from "./evidence_inputs.mjs";
import { remainingGaps } from "./remaining_gaps.mjs";

const [verdrLocation, contextLocation, downloadsLocation, outputLocation] =
  process.argv.slice(2);
const reportArtifactBaseUrlError =
  "REPORT_ARTIFACT_BASE_URL must be credential-free HTTPS ending in a slash";

function hasReportBaseUrlShape(value) {
  return (
    typeof value === "string" &&
    value.startsWith("https://") &&
    value.endsWith("/")
  );
}

function isForbiddenBaseUrlCharacter(character) {
  const characterCode = character.codePointAt(0);
  return (
    characterCode <= 32 || characterCode === 127 || "\\?#".includes(character)
  );
}

function hasUsableReportAuthority(address, value) {
  const authority = value.slice("https://".length).split("/", 1)[0];
  return (
    Boolean(address.hostname) &&
    authority !== "" &&
    !authority.includes("@") &&
    address.port !== "0"
  );
}

function parseReportBaseUrl(value) {
  try {
    return new URL(value);
  } catch {
    throw new Error(reportArtifactBaseUrlError);
  }
}

function configuredReportArtifactBaseUrl(value) {
  if (
    !hasReportBaseUrlShape(value) ||
    Array.from(value).some(isForbiddenBaseUrlCharacter)
  ) {
    throw new Error(reportArtifactBaseUrlError);
  }
  const address = parseReportBaseUrl(value);
  if (!hasUsableReportAuthority(address, value)) {
    throw new Error(reportArtifactBaseUrlError);
  }
  return value;
}

const reportArtifactBaseUrl = configuredReportArtifactBaseUrl(
  process.env.REPORT_ARTIFACT_BASE_URL,
);
const context = JSON.parse(await readFile(contextLocation, "utf8"));
const downloads = resolve(downloadsLocation);
const output = resolve(outputLocation);
const load = (path) =>
  import(pathToFileURL(join(resolve(verdrLocation), "dist", path)).href);
const { overviewManifestSchema } = await load("overview/manifest.js");
const { buildOverview } = await load("overview/build.js");
const { workflow } = context;
const detailsBaseUrl = `${reportArtifactBaseUrl}overview/${workflow.runId}/${workflow.runAttempt}/`;
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
await Object.entries(context.artifacts).reduce(
  async (previous, [name, selection]) => {
    await previous;
    if (!selection.id) return;
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
  },
  Promise.resolve(),
);
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
