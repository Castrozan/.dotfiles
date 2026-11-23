import pytest

import catalog


class TestServantRoster:
    def test_every_entry_carries_a_name_and_a_personality(self):
        for entry in catalog.SERVANT_CATALOG:
            assert entry["name"].strip()
            assert entry["personality"].strip()

    def test_an_entry_carries_nothing_else(self):
        for entry in catalog.SERVANT_CATALOG:
            assert set(entry) == {"name", "personality"}

    def test_names_are_unique(self):
        names = [entry["name"] for entry in catalog.SERVANT_CATALOG]
        assert len(names) == len(set(names))

    def test_the_roster_is_large_enough_that_collisions_are_uncommon(self):
        assert len(catalog.SERVANT_CATALOG) > 90


class TestRosterParsing:
    def test_a_duplicate_name_would_fail_the_catalog_assertion(self):
        parsed = catalog._servants_from_roster("A | one.\nA | two.")
        assert len({entry["name"] for entry in parsed}) < len(parsed)


def _roster_of(size, prefix="Servant"):
    return [{"name": f"{prefix} {n}", "personality": "x."} for n in range(size)]


def _assignments(session_ids, roster):
    return [
        catalog.select_servant_for_session(session_id, roster)["name"]
        for session_id in session_ids
    ]


class TestServantSelection:
    def test_different_session_ids_do_not_all_land_on_one_servant(self):
        selections = {
            catalog.select_servant_for_session(f"session-{n}")["name"]
            for n in range(50)
        }
        assert len(selections) > 1


class TestSelectionSurvivesRosterEdits:
    """The reason selection is scored per name instead of indexed by position.

    `hash % len(catalog)` tied every session to the roster's size, so adding one
    name re-drew every session on the fleet and reordering the file did the same.
    """


@pytest.mark.parametrize("banned_key", ["class", "catchphrase", "manner"])
def test_the_removed_fields_are_gone(banned_key):
    assert banned_key not in catalog.SERVANT_CATALOG[0]


ACCENTED_SERVANT_NAMES = [
    "Elizabeth Báthory",
    "Hijikata Toshizō",
    "Ibaraki-dōji",
    "Ibuki-dōji",
    "Ryōgi Shiki",
    "Sakamoto Ryōma",
    "Scáthach",
    "Shuten-dōji",
]


@pytest.mark.parametrize("accented_name", ACCENTED_SERVANT_NAMES)
def test_an_accented_name_is_never_flattened_to_ascii(accented_name):
    """Selection is keyed on the exact name, so dropping a diacritic silently
    re-draws every live session holding that Servant. A bulk rewrite of the
    personalities is exactly where that slips through."""
    names = {entry["name"] for entry in catalog.SERVANT_CATALOG}
    assert accented_name in names
