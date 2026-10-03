import assert from "node:assert/strict";
import { readFile, realpath } from "node:fs/promises";
import { join } from "node:path";

export async function readDocument(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

async function marketplaceRegistration(root, target, manifest) {
  const location = target === "claude" ? ".claude-plugin" : ".agents/plugins";
  const marketplace = await readDocument(
    join(root, location, "marketplace.json"),
  );
  const plugins = marketplace.plugins.filter(
    (item) => item.name === manifest.name,
  );
  assert.equal(
    plugins.length,
    1,
    "Expected one emitted marketplace registration",
  );
  const entry = plugins[0];
  if (target === "codex") assert.equal(entry.source.source, "local");
  return join(root, target === "claude" ? entry.source : entry.source.path);
}

async function openCodeRegistration(root, packageRoot, manifest) {
  const configuration = await readDocument(
    join(root, ".opencode/opencode.jsonc"),
  );
  assert.deepEqual(
    await Promise.all(configuration.skills.paths.map((path) => realpath(path))),
    [join(packageRoot, "skills")],
  );
  return join(root, ".agents/plugins", manifest.name);
}

async function directNativeRegistration(root, target, manifest) {
  assert.ok(["pi", "hermes"].includes(target), "Unknown native target");
  return join(root, `.${target}/plugins`, manifest.name);
}

export async function checkRegistration(root, target) {
  const packageRoot = await realpath(join(root, "plugin"));
  const manifest = await readDocument(join(packageRoot, "plugin.json"));
  let registered;
  if (target === "claude" || target === "codex") {
    registered = await marketplaceRegistration(root, target, manifest);
  } else if (target === "opencode") {
    registered = await openCodeRegistration(root, packageRoot, manifest);
  } else {
    registered = await directNativeRegistration(root, target, manifest);
  }
  assert.equal(
    await realpath(registered),
    packageRoot,
    "Registration origin differs",
  );
  return {
    target,
    scope: "emitted-registration-origin",
    packageRoot,
    registered,
  };
}
