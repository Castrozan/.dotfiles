import dataclasses
import threading
import time
import uuid

MAXIMUM_UNREAD_NOTIFICATION_COUNT = 64
MAXIMUM_NOTIFICATION_REQUEST_BYTES = 8192


@dataclasses.dataclass(frozen=True)
class PeerNotificationInput:
    claimed_sender: str
    content: str


@dataclasses.dataclass(frozen=True)
class PeerNotification:
    identifier: str
    recipient_pane_id: str
    claimed_sender: str
    content: str
    created_at_epoch_seconds: float
    delivery_state: str = "pending"

    def to_json_serializable_dict(self) -> dict:
        return {
            "id": self.identifier,
            "recipientPaneId": self.recipient_pane_id,
            "claimedSender": self.claimed_sender,
            "content": self.content,
            "createdAt": self.created_at_epoch_seconds,
            "deliveryState": self.delivery_state,
        }


class PeerNotificationMailbox:
    def __init__(self, recipient_pane_id: str) -> None:
        self._recipient_pane_id = recipient_pane_id
        self._unread_notifications_by_identifier: dict[str, PeerNotification] = {}
        self._lock = threading.Lock()

    def publish(
        self, notification_input: PeerNotificationInput
    ) -> PeerNotification | None:
        with self._lock:
            if (
                len(self._unread_notifications_by_identifier)
                >= MAXIMUM_UNREAD_NOTIFICATION_COUNT
            ):
                return None
            notification = PeerNotification(
                identifier=str(uuid.uuid4()),
                recipient_pane_id=self._recipient_pane_id,
                claimed_sender=notification_input.claimed_sender,
                content=notification_input.content,
                created_at_epoch_seconds=time.time(),
            )
            self._unread_notifications_by_identifier[notification.identifier] = (
                notification
            )
            return notification

    def read(self) -> list[PeerNotification]:
        with self._lock:
            return list(self._unread_notifications_by_identifier.values())

    def acknowledge(self, notification_identifier: str) -> None:
        with self._lock:
            self._unread_notifications_by_identifier.pop(notification_identifier, None)

    def claim(self, identifiers: list[str]) -> bool:
        """Fence the batch before external input; an interrupted attempt stays uncertain."""
        with self._lock:
            if not all(self._is_pending(identifier) for identifier in identifiers):
                return False
            self._set_delivery_state(identifiers, "uncertain")
            return True

    def defer(self, identifiers: list[str]) -> None:
        """Only the coordinator's definite pre-input refusal permits another attempt."""
        with self._lock:
            self._set_delivery_state(identifiers, "pending")

    def _is_pending(self, identifier: str) -> bool:
        notification = self._unread_notifications_by_identifier.get(identifier)
        return notification is not None and notification.delivery_state == "pending"

    def _set_delivery_state(self, identifiers: list[str], state: str) -> None:
        for identifier in identifiers:
            notification = self._unread_notifications_by_identifier.get(identifier)
            if notification is not None:
                self._unread_notifications_by_identifier[identifier] = (
                    dataclasses.replace(notification, delivery_state=state)
                )
