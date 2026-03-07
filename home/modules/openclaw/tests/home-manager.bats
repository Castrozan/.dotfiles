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

@test "openclaw: config option namespace exists" {
    run homeManagerModuleConfig openclaw 'builtins.hasAttr "agents" cfg.openclaw'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "openclaw: agents attr accepts submodule type" {
    run homeManagerModuleConfigWithAgents openclaw 'builtins.hasAttr "eval-bot" cfg.openclaw.agents'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}

@test "openclaw: agent config evaluates with test agent" {
    run homeManagerModuleConfigWithAgents openclaw \
        'cfg.openclaw.agents.eval-bot.enable == true
         && cfg.openclaw.defaultAgent == "eval-bot"'
    [ "$status" -eq 0 ]
    [ "$output" = "true" ]
}
