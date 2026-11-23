# Glyph: Nothing OS rice for Hyprland and Quickshell

**Bundle goal:** Keep one GitHub repository, a Nothing OS styled Hyprland and Quickshell rice, as design reference beside Lucas's own Impasto Quickshell shell; nothing in Lucas's setup changes.

| # | Capture | TL;DR | Action | Why | Already covered | Second Brain direction | Systems | Local | Lucas's note |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [GitHub - Nebelung-cloudglyph-rice Glyph a Nothing OS rice for Hyprland + Quickshell, black, white dots and one red](https://github.com/Nebelung-cloud/glyph-rice) | GPL-3.0 rice with Bar, Home, Launcher, Quick settings, a bottom-edge Deck dashboard, screen-edge OSDs, Shot, Clip, Walls, Lock and an SDDM login theme, in black, white dots and one red accent, with a Style picker that takes colour from Nothing, the wallpaper or named palettes. | file → Nebelung - Glyph Nothing OS rice for Hyprland and Quickshell (Design & Digital Art MOC) | Lucas already runs his own Quickshell shell, so installing this would replace it for no gain; the screen-edge OSD idea, the wallpaper-driven Style source and the red-marks-the-one-live-thing rule are worth keeping as reference. The origin README was read, the code was not. | machine-configuration/desktop/desktop-environments/quickshell/ already holds Lucas's own Quickshell shell (bar, impasto, overview, window-switcher), most recently touched in b9c9d066b; The README targets Arch with an install.sh and Hyprland 0.56 Lua config; it says NixOS needs the /usr/lib agent paths and the Papirus path changed by hand | - | dotfiles | no | - |

Answer on the pull request in plain language: approve the table as it stands, change any card ("drop 3", "session for 2 on kira"), or ask. Captures added after your approval need a new one.

<details><summary>Card data</summary>

<!-- ril-cards -->
```json
{
  "topic_slug": "glyph-quickshell-rice",
  "title": "Glyph: Nothing OS rice for Hyprland and Quickshell",
  "bundle_goal": "Keep one GitHub repository, a Nothing OS styled Hyprland and Quickshell rice, as design reference beside Lucas's own Impasto Quickshell shell; nothing in Lucas's setup changes.",
  "cards": [
    {
      "linked_urls": [
        "https://github.com/Nebelung-cloud/glyph-rice"
      ],
      "covered_evidence": [
        "machine-configuration/desktop/desktop-environments/quickshell/ already holds Lucas's own Quickshell shell (bar, impasto, overview, window-switcher), most recently touched in b9c9d066b",
        "The README targets Arch with an install.sh and Hyprland 0.56 Lua config; it says NixOS needs the /usr/lib agent paths and the Papirus path changed by hand"
      ],
      "second_brain_direction": [],
      "systems": [
        "dotfiles"
      ],
      "runs_locally_on_chise": false,
      "capture": "GitHub - Nebelung-cloudglyph-rice Glyph a Nothing OS rice for Hyprland + Quickshell, black, white dots and one red.md",
      "tldr": "GPL-3.0 rice with Bar, Home, Launcher, Quick settings, a bottom-edge Deck dashboard, screen-edge OSDs, Shot, Clip, Walls, Lock and an SDDM login theme, in black, white dots and one red accent, with a Style picker that takes colour from Nothing, the wallpaper or named palettes.",
      "origin_url": "https://github.com/Nebelung-cloud/glyph-rice",
      "lucas_note": "",
      "action": "file",
      "reason": "Lucas already runs his own Quickshell shell, so installing this would replace it for no gain; the screen-edge OSD idea, the wallpaper-driven Style source and the red-marks-the-one-live-thing rule are worth keeping as reference. The origin README was read, the code was not.",
      "entry": {
        "title": "Nebelung - Glyph Nothing OS rice for Hyprland and Quickshell",
        "theme_moc": "Design & Digital Art MOC",
        "tags": [
          "topic/design"
        ],
        "why": "A complete Quickshell shell with one strict visual rule: black, white dot matrix and a single red accent that marks whatever is live.",
        "what_to_steal": [
          "screen edges as OSD for volume, brightness, notifications and progress instead of popups",
          "one Style setting that draws colour from a fixed palette, the wallpaper through Material You variants, or a named theme, with terminal and GTK files regenerated from it",
          "reserve the accent colour for the one live thing on screen"
        ],
        "reuse_for": "design of the Impasto Quickshell shell",
        "creator": "Nebelung-cloud",
        "platform": "GitHub"
      },
      "added_at": "2026-11-23T02:46:23+00:00"
    }
  ]
}
```

</details>
