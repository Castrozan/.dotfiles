### Process science

Control-flow, data, resource, and exception vocabulary comes from the [Workflow
Patterns](http://www.workflowpatterns.com/) initiative by van der Aalst, ter Hofstede, Russell, and colleagues. Notation
and gateway semantics come from OMG [BPMN 2.0.2](https://www.omg.org/spec/BPMN/2.0.2/); adaptive stages, discretionary
tasks, and sentries from [CMMN 1.1](https://www.omg.org/spec/CMMN/1.1/); explicit decision tables from
[DMN](https://www.omg.org/spec/DMN/).

Agent-specific extensions are argued in [Towards Modeling Human-Agentic Collaborative
Workflows](https://arxiv.org/abs/2412.05958) and the [Agentic BPM research manifesto](https://arxiv.org/abs/2603.18916).

### Agent design patterns

Workflow and agent patterns come from Anthropic's [Building effective
agents](https://www.anthropic.com/engineering/building-effective-agents) and the [Agent Design Pattern
Catalogue](https://arxiv.org/abs/2405.10467). Node memory and action spaces come from
[CoALA](https://arxiv.org/abs/2309.02427), and collaboration structures from the [multi-agent collaboration
survey](https://arxiv.org/abs/2501.06322).

The ledger manager is [Magentic-One](https://arxiv.org/abs/2411.04468). SOP roles with typed artifacts are
[MetaGPT](https://arxiv.org/abs/2308.00352). The volunteer blackboard is [LLM-based multi-agent blackboard
systems](https://arxiv.org/abs/2510.01285).

### Automated workflow search

The operator palette converges across [AFlow](https://arxiv.org/abs/2410.10762),
[ADAS](https://arxiv.org/abs/2408.08435), [MaAS](https://arxiv.org/abs/2502.04180), and
[MASS](https://arxiv.org/abs/2502.02533). The last two also supply early exit and the finding that prompt optimization
outweighs topology.

### Reliability and scale

The failure taxonomy is [MAST](https://arxiv.org/abs/2503.13657), and the scale evidence is [Towards a Science of
Scaling Agent Systems](https://arxiv.org/abs/2512.08296). Voting versus debate comes from [Debate or
Vote](https://arxiv.org/abs/2508.17536).

Token cost, effort scaling, delegation briefs, and evaluation come from Anthropic's [multi-agent research
system](https://www.anthropic.com/engineering/multi-agent-research-system). The single-writer rule comes from
Cognition's [Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents) and [Multi-Agents: What's
Actually Working](https://cognition.com/blog/multi-agents-working). The pre-mortem is Gary Klein's [project
premortem](https://hbr.org/2007/09/performing-a-project-premortem).

### Practitioner catalogs

Pattern selection and anti-patterns come from Azure's [AI agent orchestration
patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns), Google Cloud's
[agentic design pattern guide](https://docs.cloud.google.com/architecture/choose-design-pattern-agentic-ai-system), and
the community catalog [agentic-patterns.com](https://agentic-patterns.com). The co-design gate follows the brainstorming
and subagent skills in [superpowers](https://github.com/obra/superpowers).

### Visualization

Shapes and edges follow [Mermaid flowchart syntax](https://mermaid.js.org/syntax/flowchart.html), which renders on
[GitHub](https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams)
and in terminals through renderers such as [mermaid-ascii](https://github.com/AlexanderGrooff/mermaid-ascii). Framework
vocabulary follows the [LangGraph graph API](https://docs.langchain.com/oss/python/langgraph/graph-api). The terminal
view follows the [C4 model dynamic diagram](https://c4model.com/diagrams/dynamic).

### Toolbox practice

Block evidence comes from Anthropic's [building effective
agents](https://www.anthropic.com/engineering/building-effective-agents), [multi-agent research
system](https://www.anthropic.com/engineering/multi-agent-research-system), and [long-running
harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents).

Context, evaluation, and parallel-writer practice follow [context
engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents), [agent
evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents), and the [parallel compiler
build](https://www.anthropic.com/engineering/building-c-compiler).

Counterpoints come from Cognition's [don't build multi-agents](https://cognition.com/blog/dont-build-multi-agents) and
[what's actually working](https://cognition.com/blog/multi-agents-working), [12-factor
agents](https://github.com/humanlayer/12-factor-agents), and [Manus context
engineering](https://manus.im/blog/Context-Engineering-for-AI-Agents-Lessons-from-Building-Manus).

Use and avoid lists follow the [Azure agent orchestration
patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns), and the sandbox
block follows [Claude Code sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing).

### Toolbox limits and precedents

Judging and voting limits come from [self-correction](https://arxiv.org/abs/2310.01798), [LLM as a
judge](https://arxiv.org/abs/2306.05685), and [voting or consensus](https://arxiv.org/abs/2502.19130). Typed ports
follow [Langflow components](https://docs.langflow.org/concepts-components).

Comparable catalogs are the [Agent Design Pattern Catalogue](https://arxiv.org/abs/2405.10467), [CC Workflow
Studio](https://github.com/breaking-brake/cc-wf-studio), and the [BPMN human-agentic
extension](https://arxiv.org/abs/2412.05958); none combines per-block instructions, typed ports, and harness mapping.

### Toolbox harnesses and standards

Harness mechanics follow the Claude Code docs on [subagents](https://code.claude.com/docs/en/sub-agents), [agent
teams](https://code.claude.com/docs/en/agent-teams), [workflows](https://code.claude.com/docs/en/workflows), and
[scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks).

Hooks and habits follow [hooks](https://code.claude.com/docs/en/hooks-guide) and [best
practices](https://code.claude.com/docs/en/best-practices), plus [Codex
subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) and [OpenCode
agents](https://opencode.ai/docs/agents/).

Standards: [Agent Skills](https://agentskills.io/specification) for block instructions,
[A2A](https://a2a-protocol.org/latest/topics/key-concepts/) for peers,
[MCP](https://modelcontextprotocol.io/specification/2025-11-25) for shared tools, and [OpenTelemetry generative AI
conventions](https://github.com/open-telemetry/semantic-conventions-genai) for traces.
