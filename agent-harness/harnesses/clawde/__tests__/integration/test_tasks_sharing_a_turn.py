import itertools

import pytest

TIMEOUT_LONG_ENOUGH_THAT_ONLY_THE_REPORTED_TURN_COMPLETES_A_TASK = 3600.0


class ScriptedBackend:
    def __init__(self, transport_package):
        self._observation = transport_package.observation
        self.agent_is_busy = False
        self.is_alive = True
        self.pending_output = ""
        self.delivered = []
        self.interruptions = 0

    def send_input_text(self, text):
        self.delivered.append(text)

    def observe(self):
        output, self.pending_output = self.pending_output, ""
        return self._observation(
            output, self.is_alive, 0, agent_is_busy=self.agent_is_busy
        )

    def cancel_gracefully(self):
        self.interruptions += 1


def scripted_coordinator(transport_package):
    backend = ScriptedBackend(transport_package)
    coordinator = transport_package.coordinator.ActiveTaskCoordinator(
        transport_package.store(),
        backend,
        auto_complete_idle_timeout_seconds=(
            TIMEOUT_LONG_ENOUGH_THAT_ONLY_THE_REPORTED_TURN_COMPLETES_A_TASK
        ),
    )
    return coordinator, backend


def observe_target(coordinator, backend, agent_is_busy):
    backend.agent_is_busy = agent_is_busy
    coordinator.observe_once_and_apply_to_active_task()


def test_each_task_collects_only_the_output_produced_after_its_delivery(
    transport_package,
):
    coordinator, backend = scripted_coordinator(transport_package)
    first = coordinator.submit_new_task("first")
    backend.pending_output = "before second "
    backend.agent_is_busy = True
    second = coordinator.submit_new_task("second")
    backend.pending_output = "after second"
    observe_target(coordinator, backend, agent_is_busy=True)
    observe_target(coordinator, backend, agent_is_busy=False)
    assert (first.state, first.output_text) == (
        "completed",
        "before second after second",
    )
    assert (second.state, second.output_text) == ("completed", "after second")


def test_a_vanished_target_fails_every_task_it_was_carrying(transport_package):
    coordinator, backend = scripted_coordinator(transport_package)
    tasks = [coordinator.submit_new_task(text) for text in ("first", "second")]
    backend.is_alive = False
    coordinator.observe_once_and_apply_to_active_task()
    assert [task.state for task in tasks] == ["failed", "failed"]
    assert all("is gone" in task.error_message for task in tasks)
    assert not coordinator.is_holding_an_unfinished_task()


def statuses_observed_after_delivery(events, position):
    reported_status = "idle"
    observed = []
    for event_position, event in enumerate(events):
        if event != "submit":
            reported_status = event
        if event_position > position:
            observed.append(reported_status)
    return observed


@pytest.mark.parametrize(
    "events",
    [
        events
        for length in range(1, 6)
        for events in itertools.product(("submit", "busy", "idle"), repeat=length)
    ],
)
def test_a_task_completes_exactly_when_a_turn_observed_after_its_delivery_ends(
    transport_package, events
):
    coordinator, backend = scripted_coordinator(transport_package)
    submissions = []
    for position, event in enumerate(events):
        if event == "submit":
            submissions.append((position, coordinator.submit_new_task(str(position))))
            continue
        observe_target(coordinator, backend, agent_is_busy=event == "busy")
    assert backend.delivered == [str(position) for position, _ in submissions]
    for position, task in submissions:
        observed = statuses_observed_after_delivery(events, position)
        a_turn_ended_after_delivery = (
            "busy" in observed and "idle" in observed[observed.index("busy") :]
        )
        assert task.state == (
            "completed" if a_turn_ended_after_delivery else "working"
        ), (events, position)
