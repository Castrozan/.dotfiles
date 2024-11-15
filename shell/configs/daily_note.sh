#!/usr/bin/env bash

# daily_note.sh
# This script creates a daily note in the Obsidian vault.
# Name the note as Y-m-d-daily-note.md
# When called multiple times in the same day, it will open the same note.
daily_note() {
    local file_name="daily-note"

    formatted_file_name=$(date "+%Y-%m-%d")_${file_name}.md
    cd "$OBSIDIAN_HOME" || exit
    touch "${formatted_file_name}"
    $EDITOR "${formatted_file_name}"
}

daily_note
