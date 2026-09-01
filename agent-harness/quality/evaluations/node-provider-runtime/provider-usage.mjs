const EMPTY_USAGE = {
  input_tokens: 0,
  cached_input_tokens: 0,
  cache_write_input_tokens: 0,
  output_tokens: 0,
  reasoning_output_tokens: 0,
};

export function normalizeClaudeModelUsage(modelUsage) {
  if (!modelUsage || Object.keys(modelUsage).length === 0) return null;
  return Object.values(modelUsage).reduce(
    (total, usage) => ({
      input_tokens: total.input_tokens + usage.inputTokens,
      cached_input_tokens:
        total.cached_input_tokens + usage.cacheReadInputTokens,
      cache_write_input_tokens:
        total.cache_write_input_tokens + usage.cacheCreationInputTokens,
      output_tokens: total.output_tokens + usage.outputTokens,
      reasoning_output_tokens: total.reasoning_output_tokens,
    }),
    { ...EMPTY_USAGE },
  );
}

export function normalizeOpenCodeUsage(tokens) {
  if (!tokens) return null;
  return {
    input_tokens: tokens.input,
    cached_input_tokens: tokens.cache.read,
    cache_write_input_tokens: tokens.cache.write,
    output_tokens: tokens.output,
    reasoning_output_tokens: tokens.reasoning,
  };
}
