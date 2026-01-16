# Research: Building AI Agents, Rules, and Skills (2025-2026)

> Research compiled January 2026. Sources: Anthropic docs, promptingguide.ai, IBM, Google ADK, Microsoft, AWS.

## Part 1: Agent Architecture Fundamentals

### Core Architecture Components
1. **Perception Module** - NLP, vision, APIs for environmental awareness
2. **Cognitive Module** - Reasoning engine (LLM) for planning and decision-making
3. **Memory Module** - State persistence across turns and sessions
4. **Action Module** - Tool execution and environment interaction
5. **Feedback Loop** - Self-critique and iterative improvement

### Agent Design Patterns (Ranked by Complexity)

| Pattern | Use Case | Complexity |
|---------|----------|------------|
| Task-Oriented | Well-defined workflows, bounded autonomy | Low |
| ReAct | Reason-act loops, tool-using agents | Medium |
| Reflective | Self-critique, quality improvement | Medium |
| Human-in-the-Loop | Compliance, approval workflows | Medium |
| Hierarchical | Long-horizon planning, multi-layer control | High |
| Multi-Agent | Specialized collaboration, microservices-style | High |

### Single vs Multi-Agent Decision Matrix
- **Single agent**: Simpler, easier to debug, but becomes bottleneck for complex tasks
- **Multi-agent**: Scalable, specialized, but harder to coordinate
- **Rule**: Start single, split only when complexity demands it

---

## Part 2: Prompt Engineering Techniques

### Core Techniques

**1. Chain-of-Thought (CoT)**
- Break complex tasks into sequential reasoning steps
- Zero-shot: Add "Let's think step by step"
- Few-shot: Provide reasoning examples

**2. Few-Shot Prompting**
- Curate diverse, canonical examples (3-5 optimal)
- Examples > exhaustive rule lists
- "Pictures worth a thousand words"

**3. Role/Persona Prompting**
- Assign explicit identity and expertise domain
- Improves relevance, tone, and domain focus

**4. Self-Consistency**
- Generate multiple reasoning paths
- Select most consistent answer
- Reduces single-path errors

**5. Meta Prompting**
- Focus on structure and format over content
- Abstract patterns for token efficiency

### XML Tags Best Practices

**Benefits**: Clarity, accuracy, flexibility, parseability

**Core Tags**:
```xml
<instructions>Task directives</instructions>
<context>Background information</context>
<examples>Few-shot demonstrations</examples>
<thinking>Reasoning process (hidden from user)</thinking>
<answer>Final output</answer>
<formatting>Output structure requirements</formatting>
```

**Rules**:
- Be consistent with tag names throughout
- Nest tags for hierarchy (max 3 levels)
- Reference tags in instructions: "Using the data in <context>..."
- Place context first, instructions last in long prompts

### Claude-Specific Patterns

**Explicit Instructions**: Claude 4.x follows precise instructions. Specify exactly what you want.

**Context Over Quantity**: Quality tokens beat volume. Find minimal high-signal context.

**Parallel Tool Calls**: Claude excels at parallel execution. Enable with explicit instruction.

**Thinking Sensitivity**: With extended thinking disabled, avoid "think" - use "consider", "evaluate".

**Proactive Action**: Add `<default_to_action>` tag to make Claude implement rather than suggest.

---

## Part 3: Context Engineering

### Core Principle
> "Claude is already smart enough—intelligence is not the bottleneck, context is."

### Context Window Management

**Hierarchy** (in priority order):
1. System instructions (always retain)
2. Current task specification
3. Relevant code/data being processed
4. Recent conversation turns
5. Background context (summarize or drop)

### State Management Layers

| Layer | Purpose | Example |
|-------|---------|---------|
| System | Core identity, capabilities | Agent role definition |
| Task | Current objective | "Fix authentication bug" |
| Tool | Available actions | Tool descriptions, constraints |
| Memory | Historical context | Progress notes, decisions |

### Memory Strategies

**Short-term**: Keep last N turns, summarize older content

**Long-term**:
- External files (NOTES.md, progress.txt)
- Structured state (tests.json, todo.json)
- Git for checkpoint/restore

**Compaction**: Summarize conversation segments preserving:
- Architectural decisions
- Unresolved issues
- File paths and constraints
- Implementation details

### Sub-Agent Architecture
- Each sub-agent gets clean context window
- Main agent coordinates, sub-agents explore deeply
- Return condensed summaries (1,000-2,000 tokens)
- Prevents context pollution

### KV-Cache Optimization
- Keep prompt prefix stable (single token change invalidates cache)
- Critical for latency and cost in production

---

## Part 4: Tool Design

### Design Principles
1. **Self-contained**: Tools work independently
2. **Unambiguous**: If humans can't pick the right tool, neither can AI
3. **Minimal overlap**: Avoid functional duplication
4. **Token-efficient**: Return only essential information
5. **Error-informative**: Clear failure messages aid recovery

### Tool Description Structure
```markdown
**Name**: tool_name
**Purpose**: Single sentence describing what it does
**When to use**: Specific scenarios
**When NOT to use**: Common misuses
**Parameters**:
  - param1: Description, type, constraints
**Returns**: Expected output format
**Examples**: 1-2 usage examples
```

---

## Part 5: SKILL.md Specification

### File Structure
```
skill-name/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: helper scripts
├── templates/        # Optional: output templates
└── data/             # Optional: reference data
```

### SKILL.md Format
```markdown
---
name: skill-name
description: Single sentence for AI discovery
user-invocable: true  # Show in /skills menu (optional)
---

# Skill Title

Instructions for the AI on how to use this skill.

## When to Use
- Trigger condition 1
- Trigger condition 2

## Capabilities
- What this skill can do

## Workflow
1. Step one
2. Step two

## Examples
<example>
Input: X
Output: Y
</example>
```

### Key Differences: Skills vs Commands vs Agents

| Type | Trigger | Context | Use Case |
|------|---------|---------|----------|
| Skill | Auto (AI decides) | Current conversation | Guidance, workflows |
| Command | Manual (/command) | Current conversation | Explicit actions |
| Agent | Manual (@agent) | Isolated context | Deep exploration |

---

## Part 6: Rules Design

### File Structure
```markdown
---
description: Single line describing when rule applies
alwaysApply: false  # true = always loaded, false = contextual
globs:              # Optional: path-based activation
  - "**/*.tsx"
---

Concise, dense instructions. Token-efficient prose.
Focus on what AI MUST do, not explanations.
```

### Rules Best Practices
- Keep rules minimal - only what's needed
- Use imperative voice: "Do X" not "You should do X"
- Group related rules in single file
- Use `alwaysApply: true` sparingly (consumes context every session)
- Path-based rules via globs for file-type specific guidance

---

## Part 7: Agent Instructions Design

### Structure Template
```markdown
---
name: agent-name
description: "Single-line with \n escapes for newlines and examples"
model: opus
color: cyan
---

You are an expert in [domain]. [Core identity statement].

## Core Expertise Areas
**Area 1**: Brief description of capability
**Area 2**: Brief description of capability

## Key Knowledge
### Topic 1
- Essential fact
- Essential fact

### Topic 2
Tables, code blocks, or lists for reference data

## Working Methodology
1. Step one
2. Step two

## Problem-Solving Approach
When [situation]:
- Action to take
- Action to take

## Communication Style
[How agent should communicate]
```

### Description Field Pattern (YAML Frontmatter)
Must be single-line with `\n` escapes:
```yaml
description: "Use this agent when [trigger conditions].\n\nExamples:\n\n<example>\nContext: [situation]\nuser: \"[question]\"\nassistant: \"[response indicating agent use]\"\n<commentary>\n[Why this triggers the agent]\n</commentary>\n</example>"
```

### Examples in Description
Include 2-4 examples showing:
- Context (situation)
- User message (trigger)
- Assistant response (action)
- Commentary (reasoning)

---

## Part 8: Multi-Agent Orchestration

### Patterns

**1. Sequential Pipeline**
- Linear chain: Agent A → Agent B → Agent C
- Each agent processes previous output
- Use for: document processing, data transformation

**2. Hub-and-Spoke (Supervisor)**
- Central orchestrator delegates to specialists
- Orchestrator synthesizes final response
- Use for: complex queries requiring multiple domains

**3. Adaptive Mesh**
- No central control, agents coordinate directly
- Task transfer based on expertise
- Use for: real-time, low-latency environments

**4. Hierarchical**
- High-level planning separated from execution
- Upper layers: goals, decomposition
- Lower layers: action execution
- Use for: long-running workflows

### Communication Protocols (2025)
- **MCP (Model Context Protocol)**: Tool and data connectivity
- **A2A (Agent-to-Agent)**: Inter-agent communication (Google-led, 50+ companies)
- **Skills Standard**: Capability definition (Anthropic-led, open standard)

---

## Part 9: Safety and Guardrails

### Defense Layers
1. **Input validation**: Sanitize user inputs
2. **Permission scoping**: Limit agent capabilities
3. **Action validation**: Verify before execution
4. **Output filtering**: Check responses before returning
5. **Sandboxing**: Isolate execution environments

### Human-in-the-Loop Triggers
- Irreversible actions (delete, send, publish)
- Financial transactions
- External communications
- Compliance-sensitive operations

### Error Recovery
- Keep failed attempts in context (shifts model away from repeating)
- Clear error messages with actionable guidance
- Graceful degradation for partial failures

---

## Part 10: Testing and Iteration

### Evaluation Questions
1. Does agent have sufficient information access?
2. Can formal rules prevent repeated failures?
3. Would alternative tools help?
4. Is performance stable across test sets?

### Improvement Loop
1. Observe failures in real usage
2. Diagnose: context, tools, or instructions?
3. Make minimal targeted changes
4. Test across representative scenarios
5. Measure before/after metrics

### Metrics
- Task completion rate
- Time to completion
- Token consumption
- Error rate
- Human intervention frequency

---

## Sources

- [Anthropic: Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)
- [Anthropic: Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic: Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Docs: Prompt Engineering](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Claude Docs: XML Tags](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/use-xml-tags)
- [Claude Code Docs: Skills](https://code.claude.com/docs/en/skills)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [IBM: Prompt Engineering 2026](https://www.ibm.com/think/prompt-engineering)
- [Google: Multi-Agent Patterns](https://developers.googleblog.com/developers-guide-to-multi-agent-patterns-in-adk/)
- [Microsoft: AI Agent Design Patterns](https://learn.microsoft.com/en-us/azure/architecture/ai-ml/guide/ai-agent-design-patterns)
- [AWS: Multi-Agent Orchestration](https://aws.amazon.com/solutions/guidance/multi-agent-orchestration-on-aws/)
- [Awesome AI System Prompts](https://github.com/dontriskit/awesome-ai-system-prompts)
- [K2View: Prompt Engineering Techniques 2026](https://www.k2view.com/blog/prompt-engineering-techniques/)
