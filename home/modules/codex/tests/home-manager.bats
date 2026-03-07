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

@test "codex: .local/bin/codex in home.file" {
    run homeManagerModuleConfig codex 'builtins.hasAttr ".local/bin/codex" cfg.home.file'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "codex: skills directory entries in home.file" {
    run homeManagerModuleConfig codex \
        'let
           skillFiles = builtins.filter
             (n: builtins.substring 0 14 n == ".codex/skills/")
             (builtins.attrNames cfg.home.file);
         in builtins.length skillFiles > 0'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}
