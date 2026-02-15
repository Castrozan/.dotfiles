---
name: crewai
description: Multi-agent framework for production workflows with CrewAI. Use when orchestrating multiple specialized agents that need shared context and automatic task handoff. Also use when building agent pipelines, crew-based automation, or coordinating researcher + writer or analyst + coder patterns.
---

# CrewAI - Multi-Agent Framework

Production-ready framework for orchestrating role-based AI agents working together like a team.

## What is CrewAI?

Multi-agent framework with defined roles, goals, and automatic context passing between tasks.

**vs OpenClaw:** CrewAI = shared context + automatic handoff. OpenClaw = isolated workers.

## Installation

```bash
pip install crewai crewai-tools
```

## Core Concepts

- **Agents** = Roles (e.g., "Researcher", "Writer") with tools
- **Tasks** = Work with expected outputs assigned to agents  
- **Crews** = Teams with process (sequential/hierarchical)
- **Tools** = Functions agents use (search, files, APIs)
- **Flows** = Event-driven (`@start`, `@listen`, `@router`)

## Example: Research & Writing Team

```python
from crewai import Agent, Task, Crew, Process

# Define agents
researcher = Agent(
    role='Senior Researcher',
    goal='Find and analyze technical information',
    tools=[SerperDevTool()], verbose=True)

writer = Agent(
    role='Content Writer',
    goal='Craft engaging content', verbose=True)

# Define tasks
research = Task(
    description='Research {topic}',
    expected_output='5 key findings',
    agent=researcher)

article = Task(
    description='Write article on {topic}',
    expected_output='Markdown article',
    agent=writer,
    context=[research])  # Gets researcher output automatically

# Run crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research, article],
    process=Process.sequential)

result = crew.kickoff(inputs={'topic': 'AI agents'})
print(result)
```

## When to Use

**Use CrewAI when:**
- Agents need **shared context** (avoid manual file passing)
- Clear **role delegation** (researcher → analyst → writer)
- **Sequential workflows** with automatic handoff
- **Production workflows** with crew memory

**Use OpenClaw skills when:**
- **Independent** parallel tasks
- Need **isolation** (prevent context bloat)
- **One-off work** (diagnostics, file ops)
- **Fresh context** per task (no carryover)

## Integration with OpenClaw

Run CrewAI **inside** OpenClaw agents:

```python
crew = Crew(agents=[researcher, analyst, writer], tasks=[...])
result = crew.kickoff(inputs=params)
with open('output.md', 'w') as f:
    f.write(result)
```

**Benefits:** OpenClaw isolates tasks + manages tokens, CrewAI coordinates roles within task.

**Performance:** 5.76x faster than LangGraph (verified benchmark).

## Resources

- Docs: https://docs.crewai.com | GitHub: https://github.com/crewAIInc/crewAI
- Course: https://www.deeplearning.ai/short-courses/multi-ai-agent-systems-with-crewai/
