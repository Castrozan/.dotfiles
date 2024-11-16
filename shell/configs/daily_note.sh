#!/usr/bin/env bash
# daily_note.sh
# This script creates a daily note in the Obsidian vault.
# Name the note as Y-m-d-daily-note.md
# When called multiple times in the same day, it will open the same note.
# It should have a header with the date and the note name.
daily_note() {
    local filename fullpath
    filename=$(_get_daily_note_file_name)
    cd "$OBSIDIAN_HOME" || return 1
    fullpath="$OBSIDIAN_HOME/$filename"

    # Check if the file exists; if not, create it
    if [ ! -f "$fullpath" ]; then
        touch "$fullpath"
        _add_note_header "$filename" "$fullpath"
    fi

    _open_daily_note "$fullpath"
}

# Set the header of the daily note
# $1: file name
# $2: file path
_add_note_header() {
    local filename="$1"
    local filepath="$2"
    echo "# $(date "+%Y-%m-%d") Daily Note" >>"$filepath"
    echo "### $filename" >>"$filepath"
}

# Build file name
_get_daily_note_file_name() {
    echo "$(date "+%Y-%m-%d")"_daily-note.md
}

# Open the daily note
# $1: file path
_open_daily_note() {
    $EDITOR "$1"
}

daily_note
