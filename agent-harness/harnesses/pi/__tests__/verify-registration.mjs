import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import {
  mkdtempSync,
  mkdirSync,
  readFileSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const [modules, registration] = process.argv.slice(2);
const root = mkdtempSync(join(tmpdir(), "pi-registration-check-"));
const plugin = join(root, "plugin");
mkdirSync(plugin);
writeFileSync(
  join(plugin, "plugin.json"),
  JSON.stringify({
    $schema: "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
    name: "dotfiles",
    version: "1.0.0",
  }),
);
writeFileSync(
  join(plugin, "mcp.json"),
  JSON.stringify({
    $schema: "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
    mcpServers: { probe: { type: "stdio", command: "./server" } },
  }),
);
writeFileSync(join(plugin, "server"), "#!/bin/sh\nexit 0\n", { mode: 0o755 });

for (const malformed of [false, true]) {
  const profile = join(root, malformed ? "malformed" : "valid");
  const agent = join(profile, "agent");
  mkdirSync(join(agent, "plugins"), { recursive: true });
  symlinkSync(plugin, join(agent, "plugins/dotfiles"));
  const configuration = join(agent, "mcp.json");
  const foreign = { command: "/foreign/server" };
  writeFileSync(
    configuration,
    malformed ? "{broken" : JSON.stringify({ mcpServers: { foreign } }),
  );
  const result = spawnSync(process.execPath, [registration, modules, plugin], {
    cwd: profile,
    env: {
      ...process.env,
      HOME: profile,
      PI_AGENT_DIR: agent,
      PI_CODING_AGENT_DIR: agent,
    },
    timeout: 30000,
    encoding: "utf8",
  });
  assert.ifError(result.error);
  if (malformed) {
    assert.notEqual(
      result.status,
      0,
      "Malformed native MCP config was accepted",
    );
    assert.equal(readFileSync(configuration, "utf8"), "{broken");
  } else {
    assert.equal(result.status, 0, result.stderr);
    const configured = JSON.parse(readFileSync(configuration, "utf8"));
    assert.deepEqual(configured.mcpServers.foreign, foreign);
    assert.ok(configured.mcpServers.dotfiles__probe);
  }
}
