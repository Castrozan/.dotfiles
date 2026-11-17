from unittest.mock import patch

from hypothesis import given
from hypothesis import strategies as st

import review_target
from request_links import ForgeRepository, RequestLink

CURRENT_REPOSITORY = ForgeRepository("gitlab.example", "group/current")
LINKED_REPOSITORIES = [
    ForgeRepository("gitlab.example", "group/site"),
    ForgeRepository("github.com", "owner/host"),
]
REQUEST_NUMBERS = st.integers(min_value=1, max_value=6).map(str)
DETECTED_REQUESTS = st.lists(
    st.builds(
        RequestLink,
        st.sampled_from([CURRENT_REPOSITORY, *LINKED_REPOSITORIES]),
        REQUEST_NUMBERS,
    ),
    max_size=4,
)


def parse_in_current_repository(
    selector: str, detected_requests: list[RequestLink]
) -> RequestLink | None:
    with patch("review_target.origin_repository", return_value=CURRENT_REPOSITORY):
        return review_target.parse_request_target(selector, detected_requests)


@given(
    detected_requests=DETECTED_REQUESTS,
    request_number=REQUEST_NUMBERS,
    number_sigil=st.sampled_from(["", "!", "#"]),
)
def test_number_names_the_first_detected_request_carrying_it_else_the_current_repository(
    detected_requests, request_number, number_sigil
):
    expected_request = next(
        (
            detected_request
            for detected_request in detected_requests
            if detected_request.number == request_number
        ),
        RequestLink(CURRENT_REPOSITORY, request_number),
    )
    assert (
        parse_in_current_repository(
            f"{number_sigil}{request_number}", detected_requests
        )
        == expected_request
    )


@given(detected_requests=DETECTED_REQUESTS, request_number=REQUEST_NUMBERS)
def test_typed_link_names_its_own_repository_whatever_was_detected(
    detected_requests, request_number
):
    typed_link = f"https://gitlab.example/group/typed/-/merge_requests/{request_number}"
    assert parse_in_current_repository(typed_link, detected_requests) == RequestLink(
        ForgeRepository("gitlab.example", "group/typed"), request_number
    )


@given(detected_requests=DETECTED_REQUESTS)
def test_branch_name_is_never_a_request(detected_requests):
    assert parse_in_current_repository("feature/530", detected_requests) is None
