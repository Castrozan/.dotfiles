# Console Go drops `function.name` when it translates tool schemas

`claude-go` points Claude Code at `https://opencode.ai/zen/go`, whose Anthropic Messages
endpoint translates the request into the OpenAI wire format each upstream actually speaks.
That translation loses the tool name. Claude Code always sends tools, so on the affected
models the very first message dies before any work happens:

```
API Error: 400 Error from provider (Console Go): Upstream request failed:
[invalid_request_error] Failed to deserialize the JSON body into the target type:
tools[0].function: missing field `name`
```

## Why this is not ours to fix

The same model, the same tool, and the same key succeed when the tool schema is not
translated. Sending OpenAI-format tools to `/v1/chat/completions` returns `tool_calls`
normally, while the Anthropic-format equivalent to `/v1/messages` 400s:

```
curl -X POST https://opencode.ai/zen/go/v1/chat/completions \
  -H "Authorization: Bearer $(cat ~/.secrets/opencode-api-key)" \
  -H 'content-type: application/json' \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"weather in Rio?"}],
       "tools":[{"type":"function","function":{"name":"get_weather","parameters":{"type":"object"}}}]}'
```

Native OpenCode is unaffected for the same reason: it speaks OpenAI directly, so it keeps
the DeepSeek selection in `go-provider.nix`.

Each broken upstream reports the loss in its own words, which is why the failure looks like
several unrelated bugs: DeepSeek says `tools[0].function: missing field name`, Kimi says
`function name is invalid` or `Missing required input field`, and GLM rejects any
non-native tool with `Input should be 'web_search'`.

## What the workaround does

`console-go-anthropic-tool-translation-workaround.nix` holds the list of models whose
translation was verified to survive, and substitutes a tiered replacement for any alias
whose native model is not on it. Only `claude-go` consumes the substituted set; every
other consumer of `go-provider.nix` keeps the native models.

The list was measured against every model the endpoint advertises. Tools survive on the
`qwen3` family, `minimax-m2.5`/`m2.7`, and `gpt-5.6-luna`. They fail on every `deepseek`,
`kimi`, `glm`, `mimo` and `hy3` model, and `grok-4.5` refuses the Anthropic format outright.

## Discarding it

Re-measure with the reproduction above. When an upstream starts accepting translated
tools, add it to `modelsConsoleGoTranslatesToolsCorrectlyFor` and its alias returns to the
native model automatically. When every native model passes, delete this file and inline
`models` back into `claudeCodeModels`.
