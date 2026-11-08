import copy
from datetime import datetime, timezone

from application.apply import ApplyRequest
from application.card_actions import CardActionContext
from proposals.cards import example_cards_document
from proposals.propose import ProposalContext, propose_groups

PROPOSED_AT = datetime(2026, 11, 8, 12, 0, tzinfo=timezone.utc)
EXTENDED_AT = datetime(2026, 11, 8, 15, 0, tzinfo=timezone.utc)
LUCAS_NOTE = "use this on clawde"


def propose_example_group(repository, vault, write_capture, forge):
    group = copy.deepcopy(example_cards_document()["groups"][0])
    inbox = vault / "ReadItLater Inbox"
    for card in group["cards"]:
        write_capture(
            inbox,
            card["capture"],
            f"[[ReadItLater]] [[Tweet]]\n\n# [x]({card['origin_url']})\n\n{LUCAS_NOTE}\n",
        )
    propose_groups(ProposalContext(repository, inbox, forge, PROPOSED_AT), [group])
    return group, inbox


def request_for(repository, vault, inbox, forge, launcher, comment_id) -> ApplyRequest:
    actions = CardActionContext(
        inbox, vault, launcher, "ril-test", datetime(2026, 11, 8, 18, 0)
    )
    return ApplyRequest(1, comment_id, repository, forge, actions)
