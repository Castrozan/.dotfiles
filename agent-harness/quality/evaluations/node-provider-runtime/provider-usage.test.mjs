import { test } from "node:test";
import assert from "node:assert/strict";

import { claudeResultOutcome } from "./provider-adapters.mjs";

test("claude normalizes cumulative model usage", () => {
  assert.deepEqual(
    claudeResultOutcome({
      type: "result",
      subtype: "success",
      is_error: false,
      result: "OK",
      modelUsage: {
        "claude-sonnet": {
          inputTokens: 10,
          outputTokens: 5,
          cacheReadInputTokens: 4,
          cacheCreationInputTokens: 2,
        },
        "claude-haiku": {
          inputTokens: 3,
          outputTokens: 1,
          cacheReadInputTokens: 2,
          cacheCreationInputTokens: 1,
        },
      },
    }),
    {
      output: "OK",
      error: null,
      usage: {
        input_tokens: 13,
        cached_input_tokens: 6,
        cache_write_input_tokens: 3,
        output_tokens: 6,
        reasoning_output_tokens: 0,
      },
    },
  );
});
