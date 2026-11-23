import background_wait_shape_classifier as sut
from hypothesis import given, settings
from hypothesis import strategies as st

STATE_READS_BY_EVENT_SOURCE_TARGET = {
    "file-content": ("grep -q DONE /tmp/run.log", "[ -s /tmp/out.json ]"),
    "process-exit": ("! pgrep -f rebuild >/dev/null", "kill -0 $PID 2>/dev/null"),
    "ci-run": ("gh run view 123 --json conclusion | grep -q success",),
    "peer-agent": (
        "orchestrator heartbeat show Reviewer | grep -q done",
        "a2a status reviewer 7e79 | grep -q completed",
    ),
    "pane-output": ("herdr pane read w1:p2 --lines 40 | grep -q READY",),
    "service-state": ("systemctl is-active -q app.service",),
    "local-endpoint": ("curl -sf http://localhost:8080/health",),
    "desktop-window": ("hyprctl clients -j | grep -q Steam",),
    "browser-page": ("chrome-devtools take_snapshot 4 | grep -q Loaded",),
    "background-task-output": ("grep -q DONE /tmp/claude/tasks/b1x2.output",),
}
REMOTE_STATE_READS = (
    "curl -sf https://api.example.com/status | grep -q ready",
    "glab mr view 4 -F json | jq -e .merged_at",
)
POLLING_LOOP_TEMPLATES = (
    "until {read}; do {delay}; done",
    "while ! {read}; do {delay}; done",
    "for i in $(seq 1 60); do {read} && break; {delay}; done",
    "n=0\nuntil {read} || [ $n -ge 40 ]\ndo\n  {delay}; n=$((n+1))\ndone",
    "while true; do {read} && break; {delay}; done",
    "while {delay}; do {read} && break; done",
)
CONTEXTS = (("Bash", False), ("Bash", True), ("Monitor", False))
INERT_TEMPLATES = (
    "echo 'sleep {seconds}'",
    "git commit -m 'stop using sleep {seconds} to wait'",
    "grep -rn 'sleep {seconds}' agent-harness",
    "cat > /tmp/poll.sh <<'EOF'\nuntil {read}; do sleep {seconds}; done\nEOF",
    "python3 - <<'PY'\nimport time\nfor attempt in range(3):\n    time.sleep({seconds})\nPY",
    "sleep infinity & echo kept-alive",
    'printf "%s\\n" "while true; do sleep {seconds}; done"',
)

waiting_durations = st.one_of(
    st.integers(min_value=1, max_value=900).map(str),
    st.floats(min_value=1, max_value=600).map(lambda seconds: f"{seconds:.1f}"),
    st.sampled_from(["$INTERVAL", "${DELAY:-5}", "1m", "2s"]),
)
sub_second_durations = st.integers(min_value=1, max_value=99).map(
    lambda hundredths: f"0.{hundredths:02d}"
)
numeric_durations = st.integers(min_value=1, max_value=900).map(str)
event_source_reads = st.sampled_from(
    [
        (target_name, state_read)
        for target_name, state_reads in STATE_READS_BY_EVENT_SOURCE_TARGET.items()
        for state_read in state_reads
    ]
)


@st.composite
def delay_commands(draw, durations):
    duration = draw(durations)
    delay_forms = [f"sleep {duration}", f"timeout 900 sleep {duration}"]
    if duration.replace(".", "", 1).isdigit():
        delay_forms.append(f'python3 -c "import time; time.sleep({duration})"')
    return draw(st.sampled_from(delay_forms))


@st.composite
def polling_loops(draw, state_read):
    loop = draw(st.sampled_from(POLLING_LOOP_TEMPLATES)).format(
        read=state_read,
        delay=draw(delay_commands(st.one_of(waiting_durations, sub_second_durations))),
    )
    wrapped = draw(st.sampled_from(["{}", "timeout 600 bash -c '{}'", "cd /tmp && {}"]))
    return wrapped.format(loop)


@settings(deadline=None)
@given(event_source_reads, st.data(), st.sampled_from(CONTEXTS))
def test_a_delay_in_a_polling_loop_over_an_event_source_is_denied_everywhere(
    target_and_read, data, context
):
    target_name, state_read = target_and_read
    command = data.draw(polling_loops(state_read))
    assert sut.find_denied_delay_wait(command, *context) == sut.DelayWait(
        "sleep-paced-loop", target_name
    )


@settings(deadline=None)
@given(event_source_reads, delay_commands(waiting_durations), st.sampled_from(CONTEXTS))
def test_a_fixed_delay_before_reading_state_is_denied_everywhere(
    target_and_read, delay_command, context
):
    target_name, state_read = target_and_read
    command = f"{delay_command}; {state_read}"
    assert sut.find_denied_delay_wait(command, *context) == sut.DelayWait(
        "fixed-delay", target_name
    )


@settings(deadline=None)
@given(st.sampled_from(REMOTE_STATE_READS), st.data())
def test_a_remote_poll_is_allowed_only_off_the_session_as_a_safety_net(
    state_read, data
):
    command = data.draw(polling_loops(state_read))
    assert sut.find_denied_delay_wait(command, "Bash", False) is not None
    assert sut.find_denied_delay_wait(command, "Bash", True) is None
    assert sut.find_denied_delay_wait(command, "Monitor", False) is None


@settings(deadline=None)
@given(
    st.lists(sub_second_durations, min_size=1, max_size=4),
    st.sampled_from(CONTEXTS),
)
def test_sub_second_input_pacing_outside_a_polling_loop_is_allowed(durations, context):
    paced_inputs = "; ".join(
        f"xdotool key k{index}; sleep {duration}"
        for index, duration in enumerate(durations)
    )
    item_loop = (
        f"for point in a b c; do xdotool mousemove $point; sleep {durations[0]}; done"
    )
    assert sut.find_denied_delay_wait(paced_inputs, *context) is None
    assert sut.find_denied_delay_wait(item_loop, *context) is None


@settings(deadline=None)
@given(
    st.sampled_from(INERT_TEMPLATES),
    numeric_durations,
    event_source_reads,
    st.sampled_from(CONTEXTS),
)
def test_delay_text_the_shell_never_executes_is_never_denied(
    template, seconds, target_and_read, context
):
    command = template.format(seconds=seconds, read=target_and_read[1])
    assert sut.find_denied_delay_wait(command, *context) is None
