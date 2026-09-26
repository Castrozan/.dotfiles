import assert from "node:assert/strict";
import { join } from "node:path";
import { pathToFileURL } from "node:url";
import { checkRegistration, readDocument } from "./package_checks.mjs";

const [mode, target, root, verdrRoot, executable] = process.argv.slice(2);
const registration = await checkRegistration(root, target);
if (mode === "registration") {
  process.stdout.write(JSON.stringify(registration));
} else {
  assert.equal(mode, "discovery");
  const inventory = await readDocument(
    join(root, "plugin/artifact-inventory.json"),
  );
  const manifest = await readDocument(join(root, "plugin/plugin.json"));
  const load = (path) =>
    import(pathToFileURL(join(verdrRoot, "dist/native", path)).href);
  const limits = {
    timeoutMs: 60000,
    maxOutputBytes: 4194304,
    maxArtifactBytes: 67108864,
    maxArtifactEntries: 10000,
  };
  const input = {
    root,
    profile: process.env.HOME,
    workspace: process.cwd(),
    limits,
  };
  let evidence;
  if (target === "codex") {
    const { discoverCodexPlugin } = await load("codex/discovery.js");
    const result = await discoverCodexPlugin(
      {
        kind: "codex-discovery",
        package: "plugin",
        marketplace: ".agents/plugins/marketplace.json",
        plugin: manifest.name,
        executable,
      },
      input,
    );
    evidence = JSON.parse(result.output);
  } else if (target === "opencode") {
    const { inspectOpenCode } = await load("opencode/skills.js");
    const result = await inspectOpenCode(
      {
        kind: "opencode-discovery",
        package: "plugin",
        configuration: ".opencode/opencode.jsonc",
        executable,
      },
      input,
    );
    evidence = result.metadata;
  } else {
    assert.equal(target, "pi");
    const { inspectPi } = await load("pi/skills.js");
    const result = await inspectPi(
      {
        kind: "pi-discovery",
        package: "plugin",
        registration: `.pi/plugins/${manifest.name}`,
        runtimeModules: join(verdrRoot, "node_modules"),
      },
      input,
    );
    evidence = result.metadata;
  }
  const expected = inventory.discovery.skills
    .map((name) => (target === "codex" ? `${manifest.name}:${name}` : name))
    .sort();
  assert.ok(expected.length > 0, "Expected native skill inventory is empty");
  assert.deepEqual(
    evidence.skills.map((skill) => skill.name).sort(),
    expected,
    "Native discovery differs from the expected package inventory",
  );
  process.stdout.write(
    JSON.stringify({ ...evidence, expectedSkills: expected.length }),
  );
}
