#!/usr/bin/env bats

setup_file() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    load "$REPO_DIR/tests/helpers/home-manager-eval.bash"
    _warm_flake_eval
}

setup() {
    REPO_DIR="$(cd "$BATS_TEST_DIRNAME" && git rev-parse --show-toplevel)"
    load "$REPO_DIR/tests/helpers/home-manager-eval.bash"
}

@test "module: openclaw evaluates without error" {
    run homeManagerModuleConfig openclaw 'builtins.hasAttr "openclaw" cfg'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "module: claude-code evaluates without error" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".claude/settings.json" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "module: codex evaluates without error" {
    run homeManagerModuleConfig codex 'builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "module: default evaluates with all three combined" {
    run homeManagerModuleConfig default \
        'builtins.hasAttr "openclaw" cfg
         && builtins.hasAttr ".claude/settings.json" cfg.home.file
         && builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "default: has openclaw options + claude files + codex files" {
    run homeManagerModuleConfig default \
        'builtins.hasAttr "openclaw" cfg
         && builtins.hasAttr ".claude/settings.json" cfg.home.file
         && builtins.hasAttr ".claude/mcp.json" cfg.home.file
         && builtins.hasAttr ".local/bin/claude" cfg.home.file
         && builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}
