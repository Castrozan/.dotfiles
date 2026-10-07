import assert from "node:assert/strict";
import { readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [modules, extension] = process.argv.slice(2);
const { createBashTool } = await import(
  pathToFileURL(join(modules, "@earendil-works/pi-coding-agent/dist/index.js"))
);
const { default: registerRecovery } = await import(pathToFileURL(extension));
let recover;
registerRecovery({
  on(event, handler) {
    assert.equal(event, "tool_result");
    recover = handler;
  },
});

for (const input of [
  "ordinary output\n",
  "",
  `${"x".repeat(300000)}TAIL_MARKER`,
  `${"x".repeat(300000)}TAIL_MARKER\n`,
  `header\n${"界".repeat(100000)}TAIL_MARKER\n`,
  `${"x".repeat(300000)}TAIL_MARKER\ncomplete final line\n`,
]) {
  const tool = createBashTool(tmpdir(), {
    operations: {
      async exec(_command, _cwd, { onData }) {
        const bytes = Buffer.from(input);
        for (let offset = 0; offset < bytes.length; offset += 16384) {
          onData(bytes.subarray(offset, offset + 16384));
        }
        return { exitCode: 0 };
      },
    },
  });
  const result = await tool.execute("probe", { command: "fixture" });
  const event = {
    type: "tool_result",
    toolName: "bash",
    toolCallId: "probe",
    input: { command: "fixture" },
    isError: false,
    ...result,
  };
  try {
    const repaired = await recover(event);
    if (result.details?.truncation.outputBytes === 0) {
      assert(input.includes("TAIL_MARKER"));
      assert(repaired.content[0].text.includes("TAIL_MARKER"));
      assert(!repaired.content[0].text.includes("(no output)"));
      assert(!repaired.content[0].text.includes("\ufffd"));
      assert(repaired.details.truncation.outputBytes <= 51200);
      assert(repaired.details.truncation.outputLines >= 1);
      assert.equal(
        repaired.details.fullOutputPath,
        result.details.fullOutputPath,
      );
      assert.equal(
        await readFile(result.details.fullOutputPath, "utf8"),
        input,
      );
      assert.equal(await recover({ ...event, toolName: "read" }), undefined);
      assert.equal(await recover({ ...event, isError: true }), undefined);
    } else {
      assert.equal(repaired, undefined);
    }
  } finally {
    if (result.details?.fullOutputPath) await rm(result.details.fullOutputPath);
  }
}
console.log(
  "Bash output recovery preserves long-line tails, UTF-8, complete output, and unaffected results",
);
