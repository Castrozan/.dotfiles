import { open } from "node:fs/promises";

function hasDiscardedOutput(truncation) {
  return (
    truncation?.truncated &&
    truncation.outputBytes === 0 &&
    truncation.totalBytes > 0
  );
}

async function readOutputTail(fullOutputPath) {
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
    return {
      content: buffer.subarray(start, bytesRead).toString("utf8"),
      size,
    };
  } finally {
    await outputFile.close();
  }
}

async function recoverDiscardedOutput(details) {
  const { truncation, fullOutputPath } = details;
  if (!hasDiscardedOutput(truncation) || typeof fullOutputPath !== "string") {
    return;
  }

  const { content, size } = await readOutputTail(fullOutputPath);
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
      ...details,
      truncation: {
        ...truncation,
        content,
        outputLines,
        outputBytes,
        lastLinePartial: size > outputBytes,
      },
    },
  };
}

export default function bashOutputRecovery(pi) {
  pi.on("tool_result", (event) => {
    if (event.toolName !== "bash" || event.isError) return;
    return recoverDiscardedOutput(event.details ?? {});
  });
}
