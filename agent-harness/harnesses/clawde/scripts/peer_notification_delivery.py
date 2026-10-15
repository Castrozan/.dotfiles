import json

from .active_task_coordinator import ActiveTaskCoordinator
from .peer_notification_mailbox import PeerNotificationMailbox

MAXIMUM_NOTIFICATION_BATCH_BYTES = 32768


class PeerNotificationDelivery:
    def __init__(
        self, mailbox: PeerNotificationMailbox, coordinator: ActiveTaskCoordinator
    ) -> None:
        self._mailbox = mailbox
        self._coordinator = coordinator

    def flush_once(self) -> None:
        batch = []
        encoded_batch = ""
        for notification in self._mailbox.read():
            candidate = json.dumps(
                {"messages": batch + [notification.to_json_serializable_dict()]}
            )
            if len(candidate.encode("utf-8")) > MAXIMUM_NOTIFICATION_BATCH_BYTES:
                break
            batch.append(notification.to_json_serializable_dict())
            encoded_batch = candidate
        if not batch:
            return
        if not self._coordinator.deliver_notification_if_idle(encoded_batch):
            return
        for notification in batch:
            self._mailbox.acknowledge(notification["id"])
