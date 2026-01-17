---
name: speed-read
description: Display text using RSVP speed reading. Use when presenting explanations, summaries, or any text the user should read quickly. Launches speed-read script with the provided text.
---
<!-- @agent-architect owns this file. Delegate changes, don't edit directly. -->

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
2. Execute speed-read with that file
3. Wait for the user to finish reading

## Implementation

```bash
# Write content to temp file and run speed-read
CONTENT="Your text here"
TMPFILE=$(mktemp /tmp/speed-read-XXXXXX.txt)
echo "$CONTENT" > "$TMPFILE"
speed-read "$TMPFILE"
rm "$TMPFILE"
```

## Keyboard Controls (for user reference)

- SPACE / p: Pause/resume
- q / ESC: Quit
- +/-: Adjust speed
- r: Restart

## Example Usage

When user says "/speed-read" or you determine speed-read output is appropriate:

1. Prepare the text content (plain text, no markdown formatting)
2. Use Bash to write to temp file and execute speed-read
3. Inform user the speed-read session is starting

## Notes

- Default speed is 400 WPM, adjustable with --wpm flag
- Remove markdown formatting from text (speed-read strips basic formatting but plain text works best)
- Keep text concise - speed-read works best for focused content
- The script requires a terminal that supports ANSI colors
