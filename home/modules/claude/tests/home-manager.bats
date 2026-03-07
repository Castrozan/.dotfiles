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

@test "claude: settings.json in home.file" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".claude/settings.json" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: hooks directory entries in home.file" {
    run homeManagerModuleConfig claude-code \
        'let
           hookFiles = builtins.filter
             (n: builtins.substring 0 14 n == ".claude/hooks/")
             (builtins.attrNames cfg.home.file);
         in builtins.length hookFiles > 0'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: skills directory entries in home.file" {
    run homeManagerModuleConfig claude-code \
        'let
           skillFiles = builtins.filter
             (n: builtins.substring 0 15 n == ".claude/skills/")
             (builtins.attrNames cfg.home.file);
         in builtins.length skillFiles > 0'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: mcp.json in home.file" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".claude/mcp.json" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "claude: .local/bin/claude in home.file" {
    run homeManagerModuleConfig claude-code 'builtins.hasAttr ".local/bin/claude" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}
