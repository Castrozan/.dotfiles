from unittest.mock import MagicMock, patch

import nix_gc


class TestComputeGenerationsToRemove:
    def test_removes_oldest_when_exceeds_keep_count(self):
        result = nix_gc.compute_generations_to_remove(3, ["1", "2", "3", "4", "5"])
        assert result == ["1", "2"]

    def test_returns_empty_when_at_keep_count(self):
        result = nix_gc.compute_generations_to_remove(3, ["1", "2", "3"])
        assert result == []

    def test_returns_empty_when_below_keep_count(self):
        result = nix_gc.compute_generations_to_remove(5, ["1", "2"])
        assert result == []

    def test_returns_empty_for_empty_list(self):
        result = nix_gc.compute_generations_to_remove(5, [])
        assert result == []

    def test_removes_all_but_one(self):
        result = nix_gc.compute_generations_to_remove(1, ["10", "20", "30"])
        assert result == ["10", "20"]


class TestParseArguments:
    def test_defaults_to_all_scope(self):
        scope, keep, dry_run = nix_gc.parse_arguments([])
        assert scope == "all"
        assert keep == 3
        assert dry_run is False

    def test_all_scope(self):
        scope, _, _ = nix_gc.parse_arguments(["-a"])
        assert scope == "all"

    def test_system_scope(self):
        scope, _, _ = nix_gc.parse_arguments(["--system"])
        assert scope == "system"

    def test_user_scope_explicit(self):
        scope, _, _ = nix_gc.parse_arguments(["-u"])
        assert scope == "user"

    def test_keep_count(self):
        _, keep, _ = nix_gc.parse_arguments(["-k", "3"])
        assert keep == 3

    def test_dry_run(self):
        _, _, dry_run = nix_gc.parse_arguments(["--dry-run"])
        assert dry_run is True

    def test_combined_flags(self):
        scope, keep, dry_run = nix_gc.parse_arguments(["-a", "-k", "2", "-d"])
        assert scope == "all"
        assert keep == 2
        assert dry_run is True

    def test_help_exits_zero(self):
        try:
            nix_gc.parse_arguments(["--help"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 0

    def test_unknown_option_exits_one(self):
        try:
            nix_gc.parse_arguments(["--bogus"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1

    def test_keep_without_value_exits_one(self):
        try:
            nix_gc.parse_arguments(["-k"])
            assert False, "Should have raised SystemExit"
        except SystemExit as e:
            assert e.code == 1


class TestEnsureNixInPath:
    def test_returns_true_when_nix_collect_garbage_available(self):
        with patch("nix_gc.shutil.which", return_value="/nix/bin/nix-collect-garbage"):
            assert nix_gc.ensure_nix_in_path_or_source_daemon_profile() is True

    def test_sources_daemon_profile_when_not_in_path(self):
        call_count = {"n": 0}

        def which_side_effect(cmd):
            call_count["n"] += 1
            if call_count["n"] <= 1:
                return None
            return "/nix/bin/nix-collect-garbage"

        mock_result = MagicMock(stdout="PATH=/nix/bin:/usr/bin\n")

        with patch("nix_gc.shutil.which", side_effect=which_side_effect):
            with patch("nix_gc.NIX_DAEMON_PROFILE") as mock_path:
                mock_path.is_file.return_value = True
                mock_path.__str__ = lambda _: (
                    "/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh"
                )
                with patch("nix_gc.subprocess.run", return_value=mock_result):
                    assert nix_gc.ensure_nix_in_path_or_source_daemon_profile() is True

    def test_returns_false_when_nothing_available(self):
        with patch("nix_gc.shutil.which", return_value=None):
            with patch("nix_gc.NIX_DAEMON_PROFILE") as mock_path:
                mock_path.is_file.return_value = False
                assert nix_gc.ensure_nix_in_path_or_source_daemon_profile() is False


class TestListNixEnvGenerations:
    def test_parses_generation_ids(self):
        mock_result = MagicMock(
            stdout=(
                "  1064   2026-03-15 03:22:36   \n"
                "  1065   2026-03-21 12:42:49   \n"
                "  1066   2026-03-21 12:49:13   (current)\n"
            )
        )
        with patch("nix_gc.subprocess.run", return_value=mock_result):
            result = nix_gc.list_nix_env_generations("/some/profile")
            assert result == ["1064", "1065", "1066"]

    def test_uses_sudo_when_requested(self):
        mock_result = MagicMock(stdout="")
        with patch("nix_gc.subprocess.run", return_value=mock_result) as mock_run:
            nix_gc.list_nix_env_generations("/some/profile", sudo=True)
            assert mock_run.call_args[0][0][0] == "sudo"

    def test_no_sudo_by_default(self):
        mock_result = MagicMock(stdout="")
        with patch("nix_gc.subprocess.run", return_value=mock_result) as mock_run:
            nix_gc.list_nix_env_generations("/some/profile")
            assert mock_run.call_args[0][0][0] == "nix-env"


class TestDeleteNixEnvGenerations:
    def test_deletes_each_generation(self):
        with patch("nix_gc.subprocess.run") as mock_run:
            nix_gc.delete_nix_env_generations("/some/profile", ["10", "20"])
            assert mock_run.call_count == 2
            assert "10" in mock_run.call_args_list[0][0][0]
            assert "20" in mock_run.call_args_list[1][0][0]

    def test_dry_run_does_not_delete(self, capsys):
        with patch("nix_gc.subprocess.run") as mock_run:
            nix_gc.delete_nix_env_generations(
                "/some/profile", ["10", "20"], dry_run=True
            )
            mock_run.assert_not_called()
            output = capsys.readouterr().out
            assert "[DRY RUN]" in output

    def test_uses_sudo_when_requested(self):
        with patch("nix_gc.subprocess.run") as mock_run:
            nix_gc.delete_nix_env_generations("/some/profile", ["10"], sudo=True)
            assert mock_run.call_args[0][0][0] == "sudo"


class TestCleanSystemGenerations:
    def test_skips_when_no_system_profile(self, capsys):
        with patch("nix_gc.SYSTEM_PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = False
            nix_gc.clean_system_generations(3, False)
            output = capsys.readouterr().out
            assert "not NixOS" in output

    def test_removes_old_system_generations(self, capsys):
        with patch("nix_gc.SYSTEM_PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.__str__ = lambda _: "/nix/var/nix/profiles/system"
            with patch(
                "nix_gc.list_nix_env_generations",
                return_value=["100", "101", "102", "103", "104"],
            ):
                with patch("nix_gc.delete_nix_env_generations") as mock_delete:
                    nix_gc.clean_system_generations(3, False)
                    mock_delete.assert_called_once_with(
                        "/nix/var/nix/profiles/system",
                        ["100", "101"],
                        sudo=True,
                        dry_run=False,
                    )

    def test_nothing_to_remove(self, capsys):
        with patch("nix_gc.SYSTEM_PROFILE_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.__str__ = lambda _: "/nix/var/nix/profiles/system"
            with patch(
                "nix_gc.list_nix_env_generations",
                return_value=["100", "101"],
            ):
                nix_gc.clean_system_generations(3, False)
                output = capsys.readouterr().out
                assert "Nothing to remove" in output


class TestCleanHomeManagerGenerationsViaCli:
    def test_removes_old_generations(self, capsys):
        generations_output = MagicMock(
            stdout=(
                "2026-03-10 10:00 : id 1 -> /nix/store/...\n"
                "2026-03-10 11:00 : id 2 -> /nix/store/...\n"
                "2026-03-10 12:00 : id 3 -> /nix/store/...\n"
            )
        )

        with patch(
            "nix_gc.subprocess.run",
            side_effect=[generations_output, MagicMock()],
        ) as mock_run:
            nix_gc.clean_home_manager_generations_via_cli(2, False)

            assert mock_run.call_count == 2
            remove_call = mock_run.call_args_list[1]
            assert remove_call[0][0] == [
                "home-manager",
                "remove-generations",
                "1",
            ]

    def test_skips_when_at_keep_count(self, capsys):
        generations_output = MagicMock(
            stdout=(
                "2026-03-10 10:00 : id 1 -> /nix/store/...\n"
                "2026-03-10 11:00 : id 2 -> /nix/store/...\n"
            )
        )

        with patch("nix_gc.subprocess.run", return_value=generations_output):
            nix_gc.clean_home_manager_generations_via_cli(5, False)

            output = capsys.readouterr().out
            assert "Nothing to remove" in output

    def test_dry_run_shows_would_remove(self, capsys):
        generations_output = MagicMock(
            stdout=(
                "2026-03-10 10:00 : id 10 -> /nix/store/...\n"
                "2026-03-10 11:00 : id 20 -> /nix/store/...\n"
                "2026-03-10 12:00 : id 30 -> /nix/store/...\n"
            )
        )

        with patch("nix_gc.subprocess.run", return_value=generations_output):
            nix_gc.clean_home_manager_generations_via_cli(1, True)

            output = capsys.readouterr().out
            assert "[DRY RUN]" in output
            assert "10" in output
            assert "20" in output


class TestCleanHomeManagerGenerations:
    def test_uses_cli_when_available(self, capsys):
        with patch("nix_gc.shutil.which", return_value="/bin/home-manager"):
            with patch("nix_gc.clean_home_manager_generations_via_cli") as mock_cli:
                nix_gc.clean_home_manager_generations(5, False)
                mock_cli.assert_called_once_with(5, False)

    def test_uses_nix_env_when_no_cli_but_profile_exists(self, capsys):
        with patch("nix_gc.shutil.which", return_value=None):
            with patch("nix_gc.HOME_MANAGER_PROFILE_PATH") as mock_path:
                mock_path.exists.return_value = True
                mock_path.__str__ = lambda _: "/some/profile"
                with patch(
                    "nix_gc.list_nix_env_generations", return_value=["1", "2", "3"]
                ):
                    with patch("nix_gc.delete_nix_env_generations") as mock_delete:
                        nix_gc.clean_home_manager_generations(2, False)
                        mock_delete.assert_called_once()

    def test_skips_when_nothing_available(self, capsys):
        with patch("nix_gc.shutil.which", return_value=None):
            with patch("nix_gc.HOME_MANAGER_PROFILE_PATH") as mock_path:
                mock_path.exists.return_value = False
                nix_gc.clean_home_manager_generations(5, False)
                output = capsys.readouterr().out
                assert "No home-manager profile found" in output


class TestCollectGarbage:
    def test_runs_nix_collect_garbage_for_user(self, capsys):
        with patch(
            "nix_gc.resolve_nix_collect_garbage_path",
            return_value="/nix/bin/nix-collect-garbage",
        ):
            with patch("nix_gc.subprocess.run") as mock_run:
                nix_gc.collect_garbage(False, sudo=False)
                mock_run.assert_called_once_with(["/nix/bin/nix-collect-garbage"])

    def test_runs_with_sudo_for_system(self, capsys):
        with patch(
            "nix_gc.resolve_nix_collect_garbage_path",
            return_value="/nix/bin/nix-collect-garbage",
        ):
            with patch("nix_gc.subprocess.run") as mock_run:
                nix_gc.collect_garbage(False, sudo=True)
                mock_run.assert_called_once_with(
                    ["sudo", "/nix/bin/nix-collect-garbage"]
                )

    def test_dry_run_counts_dead_paths(self, capsys):
        dead_output = MagicMock(stdout="/nix/store/a\n/nix/store/b\n")

        with patch(
            "nix_gc.resolve_nix_collect_garbage_path",
            return_value="/nix/bin/nix-collect-garbage",
        ):
            with patch("nix_gc.subprocess.run", return_value=dead_output):
                nix_gc.collect_garbage(True)
                output = capsys.readouterr().out
                assert "[DRY RUN]" in output
                assert "2" in output


class TestMain:
    def test_exits_when_nix_not_available(self):
        with patch(
            "nix_gc.ensure_nix_in_path_or_source_daemon_profile",
            return_value=False,
        ):
            try:
                nix_gc.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_runs_all_scope_by_default(self, capsys):
        with patch(
            "nix_gc.ensure_nix_in_path_or_source_daemon_profile",
            return_value=True,
        ):
            with patch("nix_gc.sys.argv", ["cmd"]):
                with patch("nix_gc.clean_home_manager_generations") as mock_hm:
                    with patch("nix_gc.collect_garbage") as mock_gc:
                        with patch("nix_gc.clean_system_generations") as mock_sys:
                            nix_gc.main()
                            mock_hm.assert_called_once_with(3, False)
                            mock_sys.assert_called_once_with(3, False)
                            assert mock_gc.call_count == 2

    def test_user_scope_skips_system(self, capsys):
        with patch(
            "nix_gc.ensure_nix_in_path_or_source_daemon_profile",
            return_value=True,
        ):
            with patch("nix_gc.sys.argv", ["cmd", "-u"]):
                with patch("nix_gc.clean_home_manager_generations"):
                    with patch("nix_gc.collect_garbage") as mock_gc:
                        with patch("nix_gc.clean_system_generations") as mock_sys:
                            nix_gc.main()
                            mock_sys.assert_not_called()
                            mock_gc.assert_called_once_with(False, sudo=False)

    def test_system_scope_only(self, capsys):
        with patch(
            "nix_gc.ensure_nix_in_path_or_source_daemon_profile",
            return_value=True,
        ):
            with patch("nix_gc.sys.argv", ["cmd", "-s"]):
                with patch("nix_gc.clean_home_manager_generations") as mock_hm:
                    with patch("nix_gc.collect_garbage") as mock_gc:
                        with patch("nix_gc.clean_system_generations") as mock_sys:
                            nix_gc.main()
                            mock_hm.assert_not_called()
                            mock_sys.assert_called_once_with(3, False)
                            mock_gc.assert_called_once_with(False, sudo=True)
