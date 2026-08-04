# Why claude-go runs through a local translation proxy

Console Go's Anthropic Messages endpoint translates every request into the OpenAI wire
format its upstreams actually speak, and that translation loses the tool name. Claude Code
always sends tools, so the first message of a session dies before any work happens:

```
API Error: 400 Error from provider (Console Go): Upstream request failed:
[invalid_request_error] Failed to deserialize the JSON body into the target type:
tools[0].function: missing field `name`
```

The loss is upstream and not ours to repair. The same model, the same tool and the same
key all succeed when the schema reaches Console Go already in OpenAI form, which is how
the fault gets located:

```
curl -X POST https://opencode.ai/zen/go/v1/chat/completions \
  -H "Authorization: Bearer $(cat ~/.secrets/opencode-api-key)" \
  -H 'content-type: application/json' \
  -d '{"model":"deepseek-v4-flash","messages":[{"role":"user","content":"weather in Rio?"}],
       "tools":[{"type":"function","function":{"name":"get_weather","parameters":{"type":"object"}}}]}'
```

Each upstream words the same loss differently, which makes one bug look like several:
DeepSeek reports the missing field outright, Kimi calls the function name invalid, and GLM
rejects any non-native tool by insisting the only acceptable one is its own web search.

So `claude-go` performs the translation itself. The proxy this module runs exposes an
Anthropic Messages endpoint on the loopback interface, converts each request to OpenAI form
locally, and forwards it to Console Go's OpenAI endpoint, which keeps tool names intact.
Native OpenCode needs none of this, because it speaks OpenAI to that endpoint directly, so
both surfaces still read their model tiers from the one shared definition in
`home/base/opencode/go-provider.nix` and stay on the same selection.

The proxy needs the plan's API key, and a key written into a Nix store file would be world
readable, so the service renders its configuration at start from a store template plus the
agenix secret and keeps the result readable only by its owner.

Once Console Go carries tool names through its own Anthropic translation, re-running the
reproduction above against the Messages endpoint rather than the completions one will
succeed, and this whole module collapses back to pointing Claude Code at that endpoint
directly.
