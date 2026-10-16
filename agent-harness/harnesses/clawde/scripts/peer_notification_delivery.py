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
        identifiers = [notification.identifier for notification in batch]
        if not self._mailbox.claim(identifiers):
            return
        self._deliver_claimed(identifiers, content)

    def _deliver_claimed(self, identifiers: list[str], content: str) -> None:
        try:
            accepted = self._coordinator.deliver_notification_if_idle(content)
        except Exception:
            # Input may already have reached the harness. Never replay on an ACK error.
            return
        if not accepted:
            self._mailbox.defer(identifiers)
            return
        for identifier in identifiers:
            self._mailbox.acknowledge(identifier)

    def _pending_batch(self) -> tuple[list[PeerNotification], str]:
        batch = []
        content = ""
        for notification in self._mailbox.read():
            if notification.delivery_state != "pending":
                continue
            message = f"From {notification.claimed_sender}:\n{notification.content}"
            candidate = "\n\n".join(filter(None, (content, message)))
            if len(candidate.encode("utf-8")) > MAXIMUM_NOTIFICATION_BATCH_BYTES:
                break
            batch.append(notification)
            content = candidate
        return batch, content
