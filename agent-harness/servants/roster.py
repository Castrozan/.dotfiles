#!/usr/bin/env python3

"""Every Servant a session can be summoned as: one per line, name then personality.

The personality is the character the session plays, injected at SessionStart beside
the name. Write it as a voice to inhabit rather than a biography: temperament, how
they speak, what they notice, how they deliver bad news. The rule that carries it
(core-rules/servant-identity.md) caps reply length elsewhere, so the character has
to fit in word choice rather than added flourish. Give it enough to work with.

To add one, write a line. Blank lines are ignored, and the name must be unique
because it is what other agents address the session by. Never edit an existing
name, including its accents: selection is keyed on the exact name, so changing one
re-draws every live session that holds it.
"""

from __future__ import annotations

from pathlib import Path

SERVANT_ROSTER = Path(__file__).with_name("roster.txt").read_text()
