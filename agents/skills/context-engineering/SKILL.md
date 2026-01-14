---
name: context-engineering
description: Context management and prompt engineering. Use when optimizing prompts, managing conversation context, reducing token usage, structuring agent workflows, or improving AI task performance.
---

# Context Engineering Skill

You are a context engineering specialist focused on optimizing AI interactions.

## Core Principles

### Token Efficiency
- Front-load critical information
- Use structured formats (YAML, JSON) over prose for data
- Remove redundant context between turns
- Summarize long outputs before including in context

### Context Structure
- System prompts: Define role, constraints, output format
- User context: Task-specific information, examples
- Conversation history: Prune irrelevant exchanges

### Prompt Patterns

**Task Decomposition**:
```
Given: [context]
Task: [high-level goal]
Steps:
1. [subtask with clear output]
2. [subtask depending on step 1]
...
Output: [expected format]
```

**Few-Shot Examples**:
```
Examples:
Input: X1 -> Output: Y1
Input: X2 -> Output: Y2

Now process:
Input: X3 -> Output: ?
```

**Chain of Thought**:
```
Think step by step:
1. First, analyze...
2. Then, determine...
3. Finally, produce...
```

## Context Window Management

### Prioritization
1. System instructions (always retain)
2. Current task specification
3. Relevant code/data being processed
4. Recent conversation turns
5. Background context (summarize or drop)

### Summarization Strategy
- After completing subtask, summarize outcome
- Replace detailed logs with summary + key findings
- Keep error messages verbatim, summarize successful operations

## Agent Workflow Design

### State Management
- Define explicit state between agent steps
- Use structured handoff format
- Include only state needed for next step

### Error Recovery
- Include rollback instructions in context
- Define failure modes and recovery paths
- Preserve error context for debugging

## Anti-Patterns to Avoid

- Repeating full file contents when small edits suffice
- Including entire conversation history
- Vague instructions requiring clarification rounds
- Missing output format specification
