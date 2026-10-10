import dataclasses
import threading
import time
import uuid

MAXIMUM_UNREAD_NOTIFICATION_COUNT = 64
MAXIMUM_NOTIFICATION_REQUEST_BYTES = 8192


@dataclasses.dataclass(frozen=True)
class PeerNotificationInput:
    claimed_sender: str
    untrusted_content: str


@dataclasses.dataclass(frozen=True)
class PeerNotification:
    identifier: str
    recipient_pane_id: str
    claimed_sender: str
    untrusted_content: str
    created_at_epoch_seconds: float

    def to_json_serializable_dict(self) -> dict:
        return {
            "id": self.identifier,
            "recipientPaneId": self.recipient_pane_id,
            "claimedSender": self.claimed_sender,
            "content": self.untrusted_content,
            "createdAt": self.created_at_epoch_seconds,
            "trust": "untrusted_peer_data",
            "ownerPermission": False,
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
                untrusted_content=notification_input.untrusted_content,
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
