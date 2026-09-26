import assert from "node:assert/strict";
import { readFile, realpath } from "node:fs/promises";
import { join } from "node:path";

export async function readDocument(path) {
  return JSON.parse(await readFile(path, "utf8"));
}

export async function checkRegistration(root, target) {
  const packageRoot = await realpath(join(root, "plugin"));
  const manifest = await readDocument(join(packageRoot, "plugin.json"));
  let registered;
  if (target === "claude" || target === "codex") {
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
    registered = join(
      root,
      target === "claude" ? entry.source : entry.source.path,
    );
  } else if (target === "opencode") {
    const configuration = await readDocument(
      join(root, ".opencode/opencode.jsonc"),
    );
    assert.deepEqual(
      await Promise.all(
        configuration.skills.paths.map((path) => realpath(path)),
      ),
      [join(packageRoot, "skills")],
    );
    registered = join(root, ".agents/plugins", manifest.name);
  } else {
    assert.ok(["pi", "hermes"].includes(target), "Unknown native target");
    registered = join(root, `.${target}/plugins`, manifest.name);
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
