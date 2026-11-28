#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

SERVANT_ROSTER = Path(__file__).with_name("roster.txt").read_text()
