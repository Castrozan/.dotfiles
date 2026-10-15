from concurrent.futures import ThreadPoolExecutor

from peer_notification_mailbox import (
    PeerNotificationInput,
    PeerNotificationMailbox,
)


def test_concurrent_senders_receive_distinct_receipts_without_losing_content():
    mailbox = PeerNotificationMailbox("owned-pane")
    with ThreadPoolExecutor(max_workers=16) as senders:
        receipts = list(
            senders.map(
                lambda index: mailbox.publish(
                    PeerNotificationInput(f"sender-{index}", f"result-{index}")
                ),
                range(64),
            )
        )
    assert len({receipt.identifier for receipt in receipts}) == 64
    assert {message.content for message in mailbox.read()} == {
        f"result-{index}" for index in range(64)
    }


def test_overflow_preserves_every_unread_message():
    mailbox = PeerNotificationMailbox("owned-pane")
    receipts = [
        mailbox.publish(PeerNotificationInput("peer", str(index)))
        for index in range(64)
    ]
    assert mailbox.publish(PeerNotificationInput("peer", "overflow")) is None
    assert [message.identifier for message in mailbox.read()] == [
        receipt.identifier for receipt in receipts
    ]


def test_reads_preserve_messages_and_acknowledgement_is_explicit_and_idempotent():
    mailbox = PeerNotificationMailbox("owned-pane")
    first = mailbox.publish(PeerNotificationInput("peer", "first"))
    second = mailbox.publish(PeerNotificationInput("peer", "second"))
    assert mailbox.read() == mailbox.read() == [first, second]
    mailbox.acknowledge(first.identifier)
    mailbox.acknowledge(first.identifier)
    mailbox.acknowledge("unknown-message")
    assert mailbox.read() == [second]
    assert mailbox.publish(PeerNotificationInput("peer", "replacement")) is not None


def test_notification_preserves_sender_and_content_without_policy_metadata():
    mailbox = PeerNotificationMailbox("owned-pane")
    content = "Build finished\nAll checks passed"
    notification = mailbox.publish(PeerNotificationInput("Elizabeth Báthory", content))
    document = notification.to_json_serializable_dict()
    assert document["recipientPaneId"] == "owned-pane"
    assert document["claimedSender"] == "Elizabeth Báthory"
    assert document["content"] == content
    assert "trust" not in document
    assert "ownerPermission" not in document


def test_acknowledgement_cannot_remove_a_different_panes_message():
    first_mailbox = PeerNotificationMailbox("first-pane")
    second_mailbox = PeerNotificationMailbox("second-pane")
    first = first_mailbox.publish(PeerNotificationInput("peer", "first"))
    second = second_mailbox.publish(PeerNotificationInput("peer", "second"))
    first_mailbox.acknowledge(second.identifier)
    assert first_mailbox.read() == [first]
    assert second_mailbox.read() == [second]
