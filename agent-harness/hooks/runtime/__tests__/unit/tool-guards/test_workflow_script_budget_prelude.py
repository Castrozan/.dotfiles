from workflow_budget_test_support import (
    COUNTING_WORKFLOW_SCRIPT,
    guarded_script_of,
    interactive_session_with_isolated_state,
    run_guarded_script_under_node,
    workflow_budget_guard_handler,
    workflow_hook_input,
    workflow_script_budget_prelude,
)

__all__ = ["interactive_session_with_isolated_state"]


def test_installs_the_prelude_right_after_the_meta_declaration():
    guarded_script = workflow_script_budget_prelude.script_with_budget_prelude(
        COUNTING_WORKFLOW_SCRIPT, 3, 1000
    )
    meta_end = COUNTING_WORKFLOW_SCRIPT.index("};") + 2
    assert guarded_script[:meta_end] == COUNTING_WORKFLOW_SCRIPT[:meta_end]
    assert (
        guarded_script[meta_end:]
        .lstrip()
        .startswith(workflow_script_budget_prelude.PRELUDE_START_MARKER)
    )
    assert guarded_script.endswith(COUNTING_WORKFLOW_SCRIPT[meta_end:])


def test_the_agent_ceiling_stops_agents_at_runtime(
    interactive_session_with_isolated_state,
):
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": COUNTING_WORKFLOW_SCRIPT})
    )
    assert run_guarded_script_under_node(guarded_script_of(result)) == [
        "done",
        "done",
        "refused",
        "refused",
        "refused",
    ]


def test_the_output_token_ceiling_stops_agents_at_runtime():
    guarded_script = workflow_script_budget_prelude.script_with_budget_prelude(
        COUNTING_WORKFLOW_SCRIPT, agent_ceiling=10, output_token_ceiling=100
    )
    assert run_guarded_script_under_node(
        guarded_script, output_tokens_per_agent=60
    ) == ["done", "done", "refused", "refused", "refused"]


def counting_script_pinned_to(model_name):
    return COUNTING_WORKFLOW_SCRIPT.replace(
        "(attempt ${attempt})`)",
        f'(attempt ${{attempt}})`, {{ model: "{model_name}" }})',
    )


def test_haiku_output_counts_at_its_price_weight():
    guarded_script = workflow_script_budget_prelude.script_with_budget_prelude(
        counting_script_pinned_to("haiku"), agent_ceiling=10, output_token_ceiling=100
    )
    assert (
        run_guarded_script_under_node(guarded_script, output_tokens_per_agent=60)
        == ["done"] * 5
    )


def test_an_opus_pin_counts_at_full_weight():
    guarded_script = workflow_script_budget_prelude.script_with_budget_prelude(
        counting_script_pinned_to("claude-opus-5-5"),
        agent_ceiling=10,
        output_token_ceiling=100,
    )
    assert run_guarded_script_under_node(
        guarded_script, output_tokens_per_agent=60
    ) == ["done", "done", "refused", "refused", "refused"]


def test_guarding_a_guarded_script_keeps_exactly_one_prelude(
    interactive_session_with_isolated_state,
):
    once_guarded = workflow_script_budget_prelude.script_with_budget_prelude(
        COUNTING_WORKFLOW_SCRIPT, 3, 1000
    )
    result = workflow_budget_guard_handler.handle(
        workflow_hook_input({"script": once_guarded})
    )
    assert (
        guarded_script_of(result).count(
            workflow_script_budget_prelude.PRELUDE_START_MARKER
        )
        == 1
    )


def test_ignores_bypass_names_inside_strings_and_comments():
    assert (
        workflow_script_budget_prelude.prelude_bypassing_constructs(
            COUNTING_WORKFLOW_SCRIPT
            + "// globalThis.agent\nawait agent(`call workflow('x') and eval(y)`);\n"
        )
        == []
    )


def test_finds_bypass_names_inside_template_expressions():
    assert workflow_script_budget_prelude.prelude_bypassing_constructs(
        "await agent(`${globalThis.agent}`);"
    ) == ["globalThis"]
