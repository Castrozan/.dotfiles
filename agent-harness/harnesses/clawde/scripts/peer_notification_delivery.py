from .active_task_coordinator import ActiveTaskCoordinator
from .peer_notification_mailbox import PeerNotification, PeerNotificationMailbox

MAXIMUM_NOTIFICATION_BATCH_BYTES = 32768


class PeerNotificationDelivery:
    def __init__(
        self, mailbox: PeerNotificationMailbox, coordinator: ActiveTaskCoordinator
    ) -> None:
        self._mailbox = mailbox
        self._coordinator = coordinator

    def flush_once(self) -> None:
        batch, content = self._pending_batch()
        if not batch:
            return
        if not self._coordinator.deliver_notification_if_idle(content):
            return
        for notification in batch:
            self._mailbox.acknowledge(notification.identifier)

    def _pending_batch(self) -> tuple[list[PeerNotification], str]:
        batch = []
        content = ""
        for notification in self._mailbox.read():
            message = f"From {notification.claimed_sender}:\n{notification.content}"
            candidate = "\n\n".join(filter(None, (content, message)))
            if len(candidate.encode("utf-8")) > MAXIMUM_NOTIFICATION_BATCH_BYTES:
                break
            batch.append(notification)
            content = candidate
        return batch, content
