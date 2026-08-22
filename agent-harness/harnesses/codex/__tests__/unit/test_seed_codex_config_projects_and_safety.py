import json
import threading

from seed_codex_config_test_support import read_live_config, run_seed


def test_seed_trusts_direct_children_of_repo_directories(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    default_repo_directory = tmp_path / "repo"
    first_project = default_repo_directory / "first-project"
    second_project = default_repo_directory / "second-project"
    nested_project = first_project / "nested-project"
    nested_project.mkdir(parents=True)
    second_project.mkdir()
    hidden_project = default_repo_directory / ".hidden-project"
    hidden_project.mkdir()
    declared_hidden_project = default_repo_directory / ".declared-hidden-project"
    declared_hidden_project.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        f"""
model = "current-model"

[projects."{declared_hidden_project}"]
trust_level = "trusted"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (default_repo_directory / "not-a-project").write_text("file", encoding="utf-8")
    (codex_directory / "config.toml").write_text(
        f"""
[projects."{first_project}"]
trust_level = "untrusted"

[projects."{hidden_project}"]
trust_level = "trusted"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    extra_repo_directory = tmp_path / "extra-repo"
    extra_project = extra_repo_directory / "extra-project"
    extra_project.mkdir(parents=True)

    result = run_seed(
        tmp_path,
        {
            "CODEX_TRUSTED_PROJECT_PARENT_DIRECTORIES": "\n".join(
                (str(default_repo_directory), str(extra_repo_directory))
            )
        },
    )

    assert result.returncode == 0, result.stderr
    trusted_projects = read_live_config(tmp_path)["projects"]
    assert set(trusted_projects) == {
        str(first_project),
        str(second_project),
        str(extra_project),
        str(declared_hidden_project),
    }
    assert trusted_projects[str(first_project)] == {"trust_level": "untrusted"}
    assert trusted_projects[str(second_project)] == {"trust_level": "trusted"}
    assert trusted_projects[str(extra_project)] == {"trust_level": "trusted"}


def test_seed_rejects_invalid_nix_source_without_touching_live_config(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        "[invalid", encoding="utf-8"
    )
    live_config_path = codex_directory / "config.toml"
    live_config_path.write_text('model = "keep-me"\n', encoding="utf-8")

    result = run_seed(tmp_path)

    assert result.returncode != 0
    assert live_config_path.read_text(encoding="utf-8") == 'model = "keep-me"\n'


def test_seed_leaves_invalid_live_config_untouched_without_failing(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        'model = "current-model"\n', encoding="utf-8"
    )
    live_config_path = codex_directory / "config.toml"
    invalid_live_config = '[projects."/keep"]\ntrust_level = "trusted"\n[invalid'
    live_config_path.write_text(invalid_live_config, encoding="utf-8")

    result = run_seed(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "leaving it untouched" in result.stderr
    assert live_config_path.read_text(encoding="utf-8") == invalid_live_config


def test_seed_injects_http_bearer_token_from_secret_file(tmp_path):
    codex_directory = tmp_path / ".codex"
    codex_directory.mkdir()
    (codex_directory / "config.toml.nix-source").write_text(
        """
[mcp_servers.sourcebot]
url = "https://sourcebot.example/api/mcp"
""".strip()
        + "\n",
        encoding="utf-8",
    )
    secret_path = tmp_path / "sourcebot-token"
    secret_writer = threading.Timer(
        0.2,
        secret_path.write_text,
        args=("secret-token\n",),
        kwargs={"encoding": "utf-8"},
    )
    secret_writer.start()

    result = run_seed(
        tmp_path,
        {
            "CODEX_MCP_SERVER_BEARER_TOKEN_FILES": json.dumps(
                {"sourcebot": str(secret_path)}
            )
        },
    )
    secret_writer.join()

    assert result.returncode == 0, result.stderr
    sourcebot = read_live_config(tmp_path)["mcp_servers"]["sourcebot"]
    assert sourcebot["http_headers"] == {"Authorization": "Bearer secret-token"}
