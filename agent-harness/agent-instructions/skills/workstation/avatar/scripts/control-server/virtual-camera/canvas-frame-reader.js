async function readCanvasFrame(session, jpegQualityPercent) {
  const evaluation = await session.sendAndAwaitResult("Runtime.evaluate", {
    expression: `window.avatarFrameJpeg?.(${jpegQualityPercent / 100})`,
    returnByValue: true,
  });
  const encodedFrame = evaluation?.result?.value;
  return encodedFrame ? Buffer.from(encodedFrame, "base64") : null;
}

module.exports = { readCanvasFrame };
