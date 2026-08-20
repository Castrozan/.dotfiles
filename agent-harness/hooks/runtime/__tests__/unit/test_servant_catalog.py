import servant_catalog


class TestServantCatalog:
    def test_every_entry_carries_name_class_catchphrase_and_manner(self):
        for entry in servant_catalog.SERVANT_CATALOG:
            assert entry["name"].strip()
            assert entry["class"].strip()
            assert entry["catchphrase"].strip()
            assert entry["manner"].strip()

    def test_name_class_keys_are_unique(self):
        keys = [
            (entry["name"], entry["class"]) for entry in servant_catalog.SERVANT_CATALOG
        ]
        assert len(keys) == len(set(keys))

    def test_catalog_has_more_than_one_candidate(self):
        assert len(servant_catalog.SERVANT_CATALOG) > 10

    def test_selection_is_deterministic_per_session_id(self):
        for session_id in ("a", "b", "same-session"):
            first = servant_catalog.select_servant_for_session(session_id)
            second = servant_catalog.select_servant_for_session(session_id)
            assert first == second

    def test_different_session_ids_do_not_all_land_on_one_servant(self):
        selections = {
            (
                servant_catalog.select_servant_for_session(f"session-{n}")["name"],
                servant_catalog.select_servant_for_session(f"session-{n}")["class"],
            )
            for n in range(50)
        }
        assert len(selections) > 1


class TestServantTemporaryDirectory:
    def test_the_ambient_tmpdir_wins(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TMPDIR", str(tmp_path))
        assert servant_catalog.servant_temporary_directory() == tmp_path

    def test_without_a_tmpdir_it_falls_back_to_tmp(self, monkeypatch):
        monkeypatch.delenv("TMPDIR", raising=False)
        assert str(servant_catalog.servant_temporary_directory()) == "/tmp"
