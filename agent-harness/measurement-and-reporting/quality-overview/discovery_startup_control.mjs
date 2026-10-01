import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  mkdir,
  mkdtemp,
  readFile,
  rm,
  symlink,
  writeFile,
  access,
} from "node:fs/promises";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
const [verdrRoot, output, codexExecutable] = process.argv.slice(2);
const { runSuite } = await import(
  pathToFileURL(join(verdrRoot, "dist/runner.js")).href
);
const runtime = join(verdrRoot, "node_modules");
const directory = await mkdtemp(join(output, "discovery-startup-"));
const artifact = join(directory, "emitted");
const packageRoot = join(artifact, ".agents/plugins/startup-control");
const marker = join(directory, "server-started");
await Promise.all(
  [join(packageRoot, "skills/probe"), join(artifact, ".pi/plugins")].map(
    (path) => mkdir(path, { recursive: true }),
  ),
);
await symlink(".agents/plugins/startup-control", join(artifact, "plugin"));
await symlink("../../plugin", join(artifact, ".pi/plugins/startup-control"));
await writeFile(
  join(packageRoot, "plugin.json"),
  JSON.stringify({
    $schema: "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    name: "startup-control",
    version: "1.0.0",
  }),
);
await writeFile(
  join(packageRoot, "skills/probe/SKILL.md"),
  "---\nname: probe\ndescription: Verify isolated discovery.\n---\n\nOwned startup control.\n",
);
const argumentsList = [
  "-e",
  'require("node:fs").writeFileSync(process.argv[1], "started")',
  marker,
];
const direct = spawnSync(process.execPath, argumentsList, { timeout: 5000 });
assert.equal(direct.status, 0);
assert.equal(await readFile(marker, "utf8"), "started");
await rm(marker);
await writeFile(
  join(packageRoot, "mcp.json"),
  JSON.stringify({
    $schema: "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
    mcpServers: {
      probe: { type: "stdio", command: process.execPath, args: argumentsList },
    },
  }),
);
await writeFile(
  join(artifact, ".agents/plugins/marketplace.json"),
  JSON.stringify({
    name: "startup-control-marketplace",
    owner: { name: "Verdr" },
    plugins: [
      {
        name: "startup-control",
        source: { source: "local", path: "./.agents/plugins/startup-control" },
      },
    ],
  }),
);
await writeFile(
  join(artifact, "opencode.json"),
  JSON.stringify({
    $schema: "https://opencode.ai/config.json",
    skills: { paths: [join(packageRoot, "skills")] },
    mcp: {
      probe: {
        type: "local",
        command: [process.execPath, ...argumentsList],
        enabled: true,
      },
    },
  }),
);
const common = {
  package: "plugin",
  assert: [{ type: "contains", value: "probe" }],
};
const suite = {
  schemaVersion: 1,
  name: "Discovery startup boundary",
  artifact: {
    root: artifact,
    packages: ["plugin"],
    requiredFiles: [{ path: "plugin/mcp.json" }],
  },
  cases: [
    {
      ...common,
      id: "codex",
      kind: "codex-discovery",
      marketplace: ".agents/plugins/marketplace.json",
      plugin: "startup-control",
      executable: codexExecutable,
    },
    {
      ...common,
      id: "opencode",
      kind: "opencode-discovery",
      configuration: "opencode.json",
      executable: join(runtime, ".bin/opencode"),
    },
    {
      ...common,
      id: "pi",
      kind: "pi-discovery",
      registration: ".pi/plugins/startup-control",
      runtimeModules: runtime,
    },
  ],
  limits: { timeoutMs: 60000, maxOutputBytes: 4194304 },
};
await writeFile(join(directory, "suite.json"), JSON.stringify(suite, null, 2));
const report = await runSuite(suite, join(directory, "report"));
await assert.rejects(access(marker), { code: "ENOENT" });
assert.equal(report.gate, "pass", JSON.stringify(report));
await writeFile(
  join(directory, "receipt.json"),
  JSON.stringify(
    {
      scope: "owned startup fixture only",
      markerPositive: true,
      discovery: report.cases,
      serverStarted: false,
      artifactBefore: report.artifact.before,
      artifactAfter: report.artifact.after,
    },
    null,
    2,
  ),
);
console.log(directory);
