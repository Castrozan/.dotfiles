import { open } from "node:fs/promises";

export default function bashOutputRecovery(pi) {
  pi.on("tool_result", async (event) => {
    const { truncation, fullOutputPath } = event.details ?? {};
    if (
      event.toolName !== "bash" ||
      event.isError ||
      !truncation?.truncated ||
      truncation.outputBytes !== 0 ||
      !(truncation.totalBytes > 0) ||
      typeof fullOutputPath !== "string"
    ) {
      return;
    }

    const outputFile = await open(fullOutputPath, "r");
    try {
      const { size } = await outputFile.stat();
      const buffer = Buffer.alloc(Math.min(size, 50 * 1024));
      const { bytesRead } = await outputFile.read(
        buffer,
        0,
        buffer.length,
        size - buffer.length,
      );
      let start = 0;
      while (start < bytesRead && (buffer[start] & 0xc0) === 0x80) start++;
      const content = buffer.subarray(start, bytesRead).toString("utf8");
      if (!content) return;

      const outputLines =
        content.split("\n").length - Number(content.endsWith("\n"));
      const outputBytes = Buffer.byteLength(content);
      return {
        content: [
          {
            type: "text",
            text: `${content}\n\n[Showing last ${outputBytes} of ${size} bytes. Full output: ${fullOutputPath}]`,
          },
        ],
        details: {
          ...event.details,
          truncation: {
            ...truncation,
            content,
            outputLines,
            outputBytes,
            lastLinePartial: size > outputBytes,
          },
        },
      };
    } finally {
      await outputFile.close();
    }
  });
}
