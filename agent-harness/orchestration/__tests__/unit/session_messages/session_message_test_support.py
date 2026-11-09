CONTRACT = """## Contract

```
ssh chise orchestrator decision file --to Ibaraki --sender Mozart --reply-host kira
ssh chise orchestrator report file --to Ibaraki --sender Mozart --reply-host kira
```
"""


def brief(
    done_when="- Rehearsal evidence comes from GitLab on the VPN",
    words="",
    context="Lucas's rehearsal on kira; results stay on the work GitLab.",
):
    return f"""# Brief: GitLab evidence for the rehearsal

## Goal

The rehearsal reads the work GitLab without glab inside its sandbox.

## Context

{context}

## Done when

{done_when}

## Constraints

- Leave the VPN as Lucas set it.

## Workspace and worktree

kira, `~/clawde`.

## Lucas's words

> a script outside the sandbox fetches GitLab (safe)
{words}

{CONTRACT}"""
