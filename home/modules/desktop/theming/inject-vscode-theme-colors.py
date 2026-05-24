#!/usr/bin/env python3
"""Merge a colors JSON file into VS Code settings.json under
workbench.colorCustomizations. Argv: settings_path, colors_path."""

import json
import sys

settings_path = sys.argv[1]
colors_path = sys.argv[2]

with open(settings_path) as f:
    settings = json.load(f)

with open(colors_path) as f:
    colors = json.load(f)

settings["workbench.colorCustomizations"] = colors

with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2)
    f.write("\n")
