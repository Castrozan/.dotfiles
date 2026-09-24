import { mkdtempSync, mkdirSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const modules = process.argv[2];
const profile = mkdtempSync(join(tmpdir(), "pi-loader-check-"));
process.env.HOME = profile;
process.env.PI_AGENT_DIR = join(profile, "agent");
process.env.PI_CODING_AGENT_DIR = process.env.PI_AGENT_DIR;
mkdirSync(join(profile, "agent/extensions"), { recursive: true });
for (const name of ["pi-agent-plugins", "pi-mcp-adapter"]) {
  symlinkSync(join(modules, name), join(profile, "agent/extensions", name));
}
const { DefaultResourceLoader } = await import(
  pathToFileURL(join(modules, "@earendil-works/pi-coding-agent/dist/index.js"))
    .href
);
const loader = new DefaultResourceLoader({
  cwd: profile,
  agentDir: process.env.PI_AGENT_DIR,
});
await loader.reload();
const result = loader.getExtensions();
if (result.errors.length || result.extensions.length !== 2) {
  throw new Error(
    JSON.stringify({ errors: result.errors, count: result.extensions.length }),
  );
}
