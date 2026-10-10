### Session titles

When a native hook supplies a `Codex session title command`, infer a concise 3–7-word title from the conversation's goal
and run that command with the quoted task title as its final argument before your first substantive task tool call.
Supply only the task title; the command adds your Servant name. Set this metadata silently and continue the user's task.
If the command reports that the title is already set or changed, or fails, continue without retrying this turn.
