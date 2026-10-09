import assert from "node:assert/strict";
import { readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

const [modules, extension] = process.argv.slice(2);
const { createBashTool } = await import(
  pathToFileURL(join(modules, "@earendil-works/pi-coding-agent/dist/index.js"))
);
const { clampMaxTokensToContext } = await import(
  pathToFileURL(
    join(modules, "@earendil-works/pi-ai/dist/api/simple-options.js"),
  )
);
const smallModel = { contextWindow: 24576, maxTokens: 2048 };
const largeModel = { contextWindow: 131072, maxTokens: 8192 };
const { default: registerRecovery } = await import(pathToFileURL(extension));
let recover;
registerRecovery({
  on(event, handler) {
    assert.equal(event, "tool_result");
    recover = handler;
  },
});

for (const model of [smallModel, largeModel]) {
  for (const input of [
    "ordinary output\n",
    "",
    `${"x".repeat(20000)}TAIL_MARKER`,
    `${"x".repeat(46000)}TAIL_MARKER`,
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
    let repaired;
    try {
      const context = { model };
      repaired = await recover(event, context);
      const maximumOutputBytes = Math.min(51200, model.contextWindow / 2);
      const outputBytes =
        result.details?.truncation?.outputBytes ??
        Buffer.byteLength(result.content[0].text);
      if (
        outputBytes > maximumOutputBytes ||
        (outputBytes === 0 && result.details?.truncation?.totalBytes > 0)
      ) {
        assert(input.includes("TAIL_MARKER"));
        assert(repaired, "oversized Bash output must leave room for the reply");
        assert(repaired.content[0].text.includes("TAIL_MARKER"));
        assert(!repaired.content[0].text.includes("(no output)"));
        assert(!repaired.content[0].text.includes("\ufffd"));
        assert(repaired.details.truncation.outputBytes <= maximumOutputBytes);
        assert(repaired.details.truncation.outputLines >= 1);
        if (model === smallModel && outputBytes > 40000) {
          const requestContext = (content) => ({
            messages: [
              {
                role: "system",
                content: "p".repeat(40000),
                timestamp: Date.now(),
              },
              {
                role: "toolResult",
                toolCallId: "probe",
                toolName: "bash",
                content,
                isError: false,
                timestamp: Date.now(),
              },
            ],
          });
          assert.equal(
            clampMaxTokensToContext(
              model,
              requestContext(result.content),
              model.maxTokens,
            ),
            1,
          );
          assert.equal(
            clampMaxTokensToContext(
              model,
              requestContext(repaired.content),
              model.maxTokens,
            ),
            model.maxTokens,
          );
        }
        if (result.details?.fullOutputPath) {
          assert.equal(
            repaired.details.fullOutputPath,
            result.details.fullOutputPath,
          );
        } else {
          assert.equal(
            (await stat(repaired.details.fullOutputPath)).mode & 0o777,
            0o600,
          );
        }
        assert.equal(
          await readFile(repaired.details.fullOutputPath, "utf8"),
          input,
        );
        assert.equal(
          await recover({ ...event, toolName: "read" }, context),
          undefined,
        );
        assert.equal(
          await recover({ ...event, isError: true }, context),
          undefined,
        );
      } else {
        assert.equal(repaired, undefined);
      }
    } finally {
      for (const outputPath of new Set([
        result.details?.fullOutputPath,
        repaired?.details.fullOutputPath,
      ])) {
        if (outputPath) await rm(outputPath);
      }
    }
  }
}
console.log(
  "Bash output recovery bounds small-model context and preserves UTF-8, full output, and unaffected results",
);
