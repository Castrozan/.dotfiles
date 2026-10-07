import { randomUUID } from "node:crypto";
import { open, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

function outputByteLimit(model) {
  const contextWindow = model?.contextWindow;
  if (!Number.isFinite(contextWindow) || contextWindow <= 0) return 50 * 1024;
  return Math.min(50 * 1024, Math.max(1, Math.floor(contextWindow / 2)));
}

function needsOutputTail(truncation, maximumBytes) {
  return (
    truncation?.totalBytes > 0 &&
    (truncation.outputBytes === 0 || truncation.outputBytes > maximumBytes)
  );
}

function outputDetails(event) {
  const details = event.details ?? {};
  if (details.truncation) return details;
  const content = event.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("\n");
  const outputBytes = Buffer.byteLength(content);
  const outputLines =
    content.split("\n").length - Number(content.endsWith("\n"));
  return {
    ...details,
    truncation: {
      content,
      totalBytes: outputBytes,
      totalLines: outputLines,
      outputBytes,
      outputLines,
    },
  };
}

async function completeOutputPath(details) {
  if (typeof details.fullOutputPath === "string") return details.fullOutputPath;
  const fullOutputPath = join(tmpdir(), `pi-bash-${randomUUID()}.log`);
  await writeFile(fullOutputPath, details.truncation.content, {
    mode: 0o600,
    flag: "wx",
  });
  return fullOutputPath;
}

async function readOutputTail(fullOutputPath, maximumBytes) {
  const outputFile = await open(fullOutputPath, "r");
  try {
    const { size } = await outputFile.stat();
    const buffer = Buffer.alloc(Math.min(size, maximumBytes));
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

async function recoverOutputTail(details, maximumBytes) {
  const { truncation } = details;
  if (!needsOutputTail(truncation, maximumBytes)) return;

  const fullOutputPath = await completeOutputPath(details);
  const { content, size } = await readOutputTail(fullOutputPath, maximumBytes);
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
      fullOutputPath,
      truncation: {
        ...truncation,
        content,
        truncated: true,
        truncatedBy: "bytes",
        maxBytes: maximumBytes,
        outputLines,
        outputBytes,
        lastLinePartial: size > outputBytes,
      },
    },
  };
}

export default function bashOutputRecovery(pi) {
  pi.on("tool_result", (event, context) => {
    if (event.toolName !== "bash" || event.isError) return;
    return recoverOutputTail(
      outputDetails(event),
      outputByteLimit(context.model),
    );
  });
}
