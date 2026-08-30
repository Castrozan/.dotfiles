from unittest.mock import MagicMock, call, patch

import pytest

import nix_gc


class TestParseArguments:
    def test_defaults_to_all_scope(self):
        assert nix_gc.parse_arguments([]) == ("all", False)

    @pytest.mark.parametrize(
        ("argument", "scope"),
        [
            ("--all", "all"),
            ("--user", "user"),
            ("--system", "system"),
        ],
    )
    def test_parses_scope(self, argument, scope):
        assert nix_gc.parse_arguments([argument]) == (scope, False)

    def test_parses_dry_run(self):
        assert nix_gc.parse_arguments(["--system", "--dry-run"]) == ("system", True)

    def test_help_exits_zero(self):
        with pytest.raises(SystemExit, match="0"):
            nix_gc.parse_arguments(["--help"])

    def test_unknown_option_exits_one(self):
        with pytest.raises(SystemExit, match="1"):
            nix_gc.parse_arguments(["--bogus"])


class TestEnsureNixInPath:
    def test_returns_true_when_nix_collect_garbage_available(self):
        with patch("nix_gc.shutil.which", return_value="/nix/bin/nix-collect-garbage"):
            assert nix_gc.ensure_nix_in_path_or_source_daemon_profile() is True

    def test_sources_daemon_profile_when_not_in_path(self):
        locations = iter([None, "/nix/bin/nix-collect-garbage"])
        daemon_environment = MagicMock(stdout="PATH=/nix/bin:/usr/bin\n")

        with patch("nix_gc.shutil.which", side_effect=lambda _: next(locations)):
            with patch("nix_gc.NIX_DAEMON_PROFILE") as daemon_profile:
                daemon_profile.is_file.return_value = True
                daemon_profile.__str__ = lambda _: (
                    "/nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh"
                )
                with patch(
                    "nix_gc.subprocess.run", return_value=daemon_environment
                ) as run:
                    assert nix_gc.ensure_nix_in_path_or_source_daemon_profile() is True
                    assert run.call_args.kwargs["check"] is True

    def test_returns_false_when_nothing_available(self):
        with patch("nix_gc.shutil.which", return_value=None):
            with patch("nix_gc.NIX_DAEMON_PROFILE") as daemon_profile:
                daemon_profile.is_file.return_value = False
                assert nix_gc.ensure_nix_in_path_or_source_daemon_profile() is False


class TestCollectGarbage:
    @pytest.mark.parametrize(
        ("sudo", "prefix"),
        [(False, []), (True, ["sudo"])],
    )
    def test_deletes_old_generations_before_collecting(self, sudo, prefix):
        with patch(
            "nix_gc.resolve_nix_collect_garbage_path",
            return_value="/nix/bin/nix-collect-garbage",
        ):
            with patch("nix_gc.subprocess.run") as run:
                nix_gc.collect_garbage(False, sudo=sudo)

        run.assert_called_once_with(
            prefix + ["/nix/bin/nix-collect-garbage", "--delete-old"], check=True
        )

    @pytest.mark.parametrize(
        ("sudo", "prefix"),
        [(False, []), (True, ["sudo"])],
    )
    def test_dry_run_previews_generations_and_dead_paths(self, sudo, prefix, capsys):
        dead_paths = MagicMock(stdout="/nix/store/a\n/nix/store/b\n")

        with patch(
            "nix_gc.resolve_nix_collect_garbage_path",
            return_value="/nix/bin/nix-collect-garbage",
        ):
            with patch(
                "nix_gc.subprocess.run", side_effect=[MagicMock(), dead_paths]
            ) as run:
                nix_gc.collect_garbage(True, sudo=sudo)

        assert run.call_args_list == [
            call(
                prefix
                + [
                    "/nix/bin/nix-collect-garbage",
                    "--delete-old",
                    "--dry-run",
                ],
                check=True,
            ),
            call(
                prefix + ["nix-store", "--gc", "--print-dead"],
                capture_output=True,
                text=True,
                check=True,
            ),
        ]
        assert "2 dead store paths" in capsys.readouterr().out


class TestMain:
    def test_exits_when_nix_not_available(self):
        with patch(
            "nix_gc.ensure_nix_in_path_or_source_daemon_profile",
            return_value=False,
        ):
            with pytest.raises(SystemExit, match="1"):
                nix_gc.main()

    @pytest.mark.parametrize(
        ("arguments", "expected_calls"),
        [
            ([], [call(False, sudo=False), call(False, sudo=True)]),
            (["--user"], [call(False, sudo=False)]),
            (["--system"], [call(False, sudo=True)]),
            (["--all", "--dry-run"], [call(True, sudo=False), call(True, sudo=True)]),
        ],
    )
    def test_runs_selected_scope(self, arguments, expected_calls):
        with patch(
            "nix_gc.ensure_nix_in_path_or_source_daemon_profile",
            return_value=True,
        ):
            with patch("nix_gc.sys.argv", ["nix-gc", *arguments]):
                with patch("nix_gc.collect_garbage") as collect_garbage:
                    nix_gc.main()

        assert collect_garbage.call_args_list == expected_calls
