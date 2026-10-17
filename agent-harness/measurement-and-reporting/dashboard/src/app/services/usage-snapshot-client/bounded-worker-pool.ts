export async function mapWithBoundedWorkerPool<Input, Output>(
  inputs: readonly Input[],
  maximumInFlight: number,
  transform: (input: Input) => Promise<Output>,
): Promise<Output[]> {
  const outputs = new Array<Output>(inputs.length);
  let nextInputIndex = 0;
  const runWorker = async (): Promise<void> => {
    while (nextInputIndex < inputs.length) {
      const inputIndex = nextInputIndex++;
      outputs[inputIndex] = await transform(inputs[inputIndex]);
    }
  };
  const workerCount = Math.min(maximumInFlight, inputs.length);
  await Promise.all(Array.from({ length: workerCount }, runWorker));
  return outputs;
}
