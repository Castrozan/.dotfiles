#!/usr/bin/env bats

readonly SKILL_FILE="$(cd "$(dirname "$BATS_TEST_FILENAME")/../../../.." && pwd)/agents/skills/browser/SKILL.md"

setup() {
    if [ ! -f "$SKILL_FILE" ]; then
        skip "browser SKILL.md not found"
    fi
}

@test "skill file does not reference nonexistent uv run atendimento-browser commands" {
    run grep -c 'uv run atendimento-browser' "$SKILL_FILE"
    [ "$status" -ne 0 ] || [ "$output" = "0" ]
}

@test "skill file does not reference nonexistent atendimento-browser commands" {
    run grep -c 'atendimento-browser' "$SKILL_FILE"
    [ "$status" -ne 0 ] || [ "$output" = "0" ]
}

@test "skill file references pinchtab-ensure-running" {
    run grep -q 'pinchtab-ensure-running' "$SKILL_FILE"
    [ "$status" -eq 0 ]
}

@test "skill file references pinchtab-navigate-and-snapshot" {
    run grep -q 'pinchtab-navigate-and-snapshot' "$SKILL_FILE"
    [ "$status" -eq 0 ]
}

@test "skill file references pinchtab-act-and-snapshot" {
    run grep -q 'pinchtab-act-and-snapshot' "$SKILL_FILE"
    [ "$status" -eq 0 ]
}

@test "skill file references pinchtab-fill-form" {
    run grep -q 'pinchtab-fill-form' "$SKILL_FILE"
    [ "$status" -eq 0 ]
}

@test "skill file references pinchtab-screenshot" {
    run grep -q 'pinchtab-screenshot' "$SKILL_FILE"
    [ "$status" -eq 0 ]
}

@test "skill file references pinchtab-switch-mode" {
    run grep -q 'pinchtab-switch-mode' "$SKILL_FILE"
    [ "$status" -eq 0 ]
}
