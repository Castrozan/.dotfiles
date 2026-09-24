import { realpathSync } from "node:fs";
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
const runtime = new PluginRuntime();
runtime.initializeUser();
const plugin = runtime.find("dotfiles");
if (!plugin || realpathSync(plugin.root) !== realpathSync(process.argv[3])) {
  throw new Error(
    "The managed Pi plugin was not discovered at its declared root",
  );
}
runtime.setEnabled("dotfiles", true);
runtime.trust("dotfiles");
const errors = runtime
  .allDiagnostics()
  .filter((diagnostic) => diagnostic.severity === "error");
if (errors.length) {
  throw new Error(JSON.stringify(errors));
}
