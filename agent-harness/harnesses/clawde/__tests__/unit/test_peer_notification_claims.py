from concurrent.futures import ThreadPoolExecutor

from peer_notification_mailbox import PeerNotificationInput, PeerNotificationMailbox


def test_batch_claim_is_atomic_across_concurrent_delivery_workers():
    mailbox = PeerNotificationMailbox("owned-pane")
    message = mailbox.publish(PeerNotificationInput("peer", "result"))
    with ThreadPoolExecutor(max_workers=8) as workers:
        outcomes = list(
            workers.map(lambda _: mailbox.claim([message.identifier]), range(8))
        )
    assert outcomes.count(True) == 1
    assert mailbox.read()[0].delivery_state == "uncertain"


def test_stale_overlapping_batch_cannot_claim_a_distinct_message():
    mailbox = PeerNotificationMailbox("owned-pane")
    first = mailbox.publish(PeerNotificationInput("peer", "first"))
    second = mailbox.publish(PeerNotificationInput("peer", "second"))
    assert mailbox.claim([first.identifier])
    assert not mailbox.claim([first.identifier, second.identifier])
    assert mailbox.read()[1].delivery_state == "pending"
    assert mailbox.claim([second.identifier])


def test_acknowledged_message_cannot_be_resurrected_by_deferred_delivery():
    mailbox = PeerNotificationMailbox("owned-pane")
    message = mailbox.publish(PeerNotificationInput("peer", "result"))
    assert mailbox.claim([message.identifier])
    mailbox.acknowledge(message.identifier)
    mailbox.defer([message.identifier])
    assert mailbox.read() == []
    assert not mailbox.claim([message.identifier])


def test_definite_pre_input_deferral_preserves_identity_for_one_later_claim():
    mailbox = PeerNotificationMailbox("owned-pane")
    message = mailbox.publish(PeerNotificationInput("peer", "result"))
    assert mailbox.claim([message.identifier])
    mailbox.defer([message.identifier])
    assert mailbox.read() == [message]
    assert mailbox.claim([message.identifier])
    assert not mailbox.claim([message.identifier])
