import { readFileSync, realpathSync } from "node:fs";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(
  pathToFileURL(
    `${process.argv[2]}/@earendil-works/pi-coding-agent/package.json`,
  ),
);
const { createJiti } = require("jiti");
const { PluginRuntime } = await createJiti(import.meta.url).import(
  `${process.argv[2]}/pi-agent-plugins/src/runtime.ts`,
);
const pluginName = JSON.parse(
  readFileSync(`${process.argv[3]}/plugin.json`, "utf8"),
).name;
const runtime = new PluginRuntime();
runtime.initializeUser();
const plugin = runtime.find(pluginName);
if (!plugin || realpathSync(plugin.root) !== realpathSync(process.argv[3])) {
  throw new Error(
    "The managed Pi plugin was not discovered at its declared root",
  );
}
const enabled = runtime.setEnabled(pluginName, true);
const trusted = runtime.trust(pluginName);
const errors = [
  ...runtime.allDiagnostics(),
  ...enabled.diagnostics,
  ...trusted.diagnostics,
].filter((diagnostic) => diagnostic.severity === "error");
if (errors.length) {
  throw new Error(JSON.stringify(errors));
}
