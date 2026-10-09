import time
from types import SimpleNamespace


def test_completion_keeps_output_from_working_and_final_observations(transport_package):
    observations = iter(
        [
            transport_package.observation(
                "answer ", True, time.time(), agent_is_busy=True
            ),
            transport_package.observation("", True, time.time(), agent_is_busy=False),
            transport_package.observation(
                "settled", True, time.time(), agent_is_busy=False
            ),
        ]
    )
    backend = SimpleNamespace(
        send_input_text=lambda text: None, observe=lambda: next(observations)
    )
    coordinator = transport_package.coordinator.ActiveTaskCoordinator(
        transport_package.store(), backend
    )
    task, accepted = coordinator.submit_new_task_if_idle("input")
    assert accepted
    coordinator.observe_once_and_apply_to_active_task()
    coordinator.observe_once_and_apply_to_active_task()
    assert task.state == "completed"
    assert task.output_text == "answer settled"


def test_vanished_target_fails_work_and_another_task_can_be_accepted(transport_package):
    backend = SimpleNamespace(
        send_input_text=lambda text: None,
        observe=lambda: transport_package.observation("", False, time.time()),
    )
    coordinator = transport_package.coordinator.ActiveTaskCoordinator(
        transport_package.store(), backend
    )
    task, _ = coordinator.submit_new_task_if_idle("input")
    coordinator.observe_once_and_apply_to_active_task()
    assert task.state == "failed"
    assert "is gone" in task.error_message
    next_task, accepted = coordinator.submit_new_task_if_idle("next")
    assert accepted
    assert next_task.id != task.id


def test_unknown_status_timeout_uses_submission_time_before_stale_pane_activity(
    transport_package,
):
    backend = SimpleNamespace(
        send_input_text=lambda text: None,
        observe=lambda: transport_package.observation("", True, 0, agent_is_busy=None),
    )
    coordinator = transport_package.coordinator.ActiveTaskCoordinator(
        transport_package.store(),
        backend,
        auto_complete_idle_timeout_seconds=30,
    )
    task, _ = coordinator.submit_new_task_if_idle("input")
    coordinator.observe_once_and_apply_to_active_task()
    assert task.state == "working"
    task.created_at_epoch_seconds -= 60
    coordinator.observe_once_and_apply_to_active_task()
    assert task.state == "completed"
