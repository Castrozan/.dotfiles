---
name: speed-read
description: Display text using RSVP speed reading. Use when presenting explanations, summaries, or any text the user should read quickly. Spawns dedicated terminal window for focused reading.
---

# Speed Read Skill

Display text using RSVP (Rapid Serial Visual Presentation) for faster reading comprehension. The user can read at 400-900+ WPM using this method.

## When to Use

Use this skill when:
- Presenting explanations or summaries
- The user requests speed-read output
- Delivering any substantial text response that benefits from focused reading

## How to Use

When this skill is invoked, you MUST:

1. Write the text to display to a temporary file
2. Spawn a dedicated terminal window running speed-read
3. Inform user to switch to the speed-read window when ready

## Implementation

```bash
# Spawn dedicated terminal window for focused reading
CONTENT="Your text here without punctuation for smoother reading"
echo "$CONTENT" > /tmp/sr-msg.txt
wezterm --config 'font_size=48' start --class speed-read-popup -- speed-read --wait --wait-end /tmp/sr-msg.txt &
```

## Keyboard Controls (for user reference)

- SPACE / p: Pause/resume
- q / ESC: Quit
- +/-: Adjust speed by 50 WPM
- r: Restart from beginning

## Example Usage

When user says "/speed-read" or you determine speed-read output is appropriate:

1. Prepare the text content (plain text, minimal punctuation)
2. Use Bash to spawn terminal window with speed-read
3. Tell user to switch to the speed-read window

## Notes

- Default speed is 400 WPM, adjustable with --wpm flag
- Use plain text without punctuation for smoothest reading flow
- Spawns separate terminal window so user can focus entirely on reading
- Window class is speed-read-popup for potential window manager rules
