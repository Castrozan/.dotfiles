---
name: personal-skills
description: Discover personal skill vault entries without loading the full personal skill set. Use when work may benefit from personal-only skills and you need to inspect what exists before opening a specific skill.
---

Use this skill to inspect the personal Claude skill vault metadata and locate the top-level `SKILL.md` file for each available personal skill.

Run the metadata script from this skill's base directory:

```bash
python3 scripts/list-personal-skill-vault-metadata.py
```

Optional custom vault path:

```bash
python3 scripts/list-personal-skill-vault-metadata.py /path/to/personal-skill-vault
```

The script returns JSON with each personal skill name, description, directory name, skill directory path, and `SKILL.md` path. Read only the specific personal skill files you actually need after inspecting the list.
