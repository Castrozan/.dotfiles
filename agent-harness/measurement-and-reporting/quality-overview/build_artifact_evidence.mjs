import { mkdir, realpath, writeFile } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";
import { unmeasuredCapabilities } from "./unmeasured_capabilities.mjs";

const [verdrLocation, bundleLocation, outputLocation, python, codex] =
  process.argv.slice(2);
const verdrRoot = await realpath(verdrLocation);
const bundle = await realpath(bundleLocation);
const output = resolve(outputLocation);
const scripts = dirname(fileURLToPath(import.meta.url));
const load = (path) =>
  import(pathToFileURL(join(verdrRoot, "dist", path)).href);
const { digest, snapshotArtifact } = await load("artifact.js");
const { runSuite } = await load("runner.js");
const { suiteSchema } = await load("suite/schema.js");
const targets = ["claude", "codex", "opencode", "pi", "hermes"];
const limits = {
  timeoutMs: 120000,
  maxOutputBytes: 4194304,
  maxArtifactBytes: 67108864,
  maxArtifactEntries: 10000,
};
const subject = {
  repository: process.env.GITHUB_REPOSITORY,
  revision: process.env.GITHUB_SHA,
  artifactDigest: (await snapshotArtifact(bundle, limits)).digest,
};
if (!subject.repository || !/^[a-f0-9]{40}$/.test(subject.revision ?? ""))
  throw new Error("Exact GitHub subject identity is required");
const runUrl = `https://github.com/${subject.repository}/actions/runs/${process.env.GITHUB_RUN_ID}`;
const provenance = {
  repository: subject.repository,
  revision: subject.revision,
  scope: "ci-emitted-complete-package",
};
const scope = {
  name: "CI emitted complete production package",
  tier: "artifact",
  platform: process.platform,
  exclusions: [
    "deployed host profiles",
    "model turns",
    "MCP invocation",
    "browser processes",
    "instruction adherence",
  ],
};
const inputs = [];
await mkdir(output);
await mkdir(join(output, "suites"));
const base = {
  schemaVersion: 1,
  artifact: {
    root: bundle,
    packages: ["plugin"],
    digest: subject.artifactDigest,
    provenance,
    requiredFiles: [
      { path: "plugin/artifact-inventory.json" },
      { path: "plugin/mcp.json" },
    ],
  },
  limits,
};
const jsonAssertion = [{ type: "is-json" }];
const source = {
  id: "source-preservation",
  kind: "command",
  command: python,
  args: [join(scripts, "source_inventory.py"), "{artifact}"],
  assert: jsonAssertion,
};
const suites = [
  {
    id: "source-preservation",
    label: "Source bytes and executable modes",
    target: null,
    cases: [source],
  },
];
for (const target of targets) {
  const executable =
    target === "codex" ? codex : join(verdrRoot, "node_modules/.bin/opencode");
  const command = (mode) => ({
    id: `${target}-${mode}`,
    kind: "command",
    command: process.execPath,
    args: [
      join(scripts, "native_discovery.mjs"),
      mode,
      target,
      "{artifact}",
      verdrRoot,
      executable,
    ],
    assert: jsonAssertion,
  });
  const cases = [command("registration")];
  if (["codex", "opencode", "pi"].includes(target))
    cases.push(command("discovery"));
  suites.push({
    id: `${target}-artifact`,
    label: `${target} emitted registration${cases.length > 1 ? " and native discovery" : ""}`,
    target,
    cases,
  });
}
let failed = false;
for await (const descriptor of suites) {
  const suite = suiteSchema.parse({
    ...base,
    name: descriptor.label,
    cases: descriptor.cases,
  });
  const suiteDigest = digest(JSON.stringify(suite));
  await writeFile(
    join(output, "suites", `${descriptor.id}.json`),
    JSON.stringify(suite, null, 2),
    { flag: "wx" },
  );
  inputs.push({
    id: descriptor.id,
    label: descriptor.label,
    target: descriptor.target,
    scope,
    maxAgeSeconds: 172800,
    format: "verdr",
    path: `${descriptor.id}/report.json`,
    sourceUri: `../${descriptor.id}/report.json`,
    runUrl,
    suiteDigest,
    cases: suite.cases.map(({ id, kind }) => ({
      id,
      kind,
      target: descriptor.target,
    })),
  });
}
await writeFile(
  join(output, "manifest.json"),
  JSON.stringify(
    {
      schemaVersion: 1,
      name: "Dotfiles CI artifact evidence",
      subject,
      inputs: [...inputs, ...unmeasuredCapabilities(targets, scope)],
    },
    null,
    2,
  ),
  { flag: "wx" },
);
for await (const descriptor of suites) {
  const suite = suiteSchema.parse({
    ...base,
    name: descriptor.label,
    cases: descriptor.cases,
  });
  const report = await runSuite(suite, join(output, descriptor.id));
  failed ||= report.gate !== "pass";
}
process.exitCode = failed ? 1 : 0;
