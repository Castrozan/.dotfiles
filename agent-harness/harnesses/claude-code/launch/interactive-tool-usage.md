### Tool selection

Use a dedicated tool when it can perform the operation. Read, not cat, head, or tail, inspects files; Glob, not find
or ls, discovers files; Grep, not grep or rg, searches content; and Edit, not Write, changes an existing file. Use Bash
only when no dedicated tool can perform the operation. Use Write only to create a new file.

Before changing existing code, use Read on the relevant file and a direct caller, dependency, or test. Do not substitute
Grep, Glob, or Bash output for those reads. For a bug investigation, complete those reads before editing.
