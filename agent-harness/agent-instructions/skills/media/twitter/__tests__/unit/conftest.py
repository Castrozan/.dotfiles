import importlib
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def twitter_modules(monkeypatch):
    directory = Path(__file__).resolve().parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(directory))
    modules = {
        name: importlib.import_module(f"twikit_cli_{name}")
        for name in (
            "authentication",
            "serializers",
            "read_operations",
            "write_operations",
        )
    }
    specification = importlib.util.spec_from_file_location(
        "twitter_test_cli", directory / "twikit-cli.py"
    )
    cli = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(cli)
    client = SimpleNamespace()
    for name in (
        "search_tweet",
        "get_user_by_screen_name",
        "get_user_tweets",
        "get_tweet_by_id",
        "get_trends",
        "get_user_followers",
        "get_user_following",
        "get_bookmarks",
        "get_timeline",
        "user",
        "create_tweet",
        "favorite_tweet",
        "retweet",
        "create_bookmark",
        "send_dm",
    ):
        setattr(client, name, AsyncMock())
    for name in ("read_operations", "write_operations"):
        monkeypatch.setattr(modules[name], "get_client", AsyncMock(return_value=client))
    return SimpleNamespace(**modules, cli=cli, client=client)


@pytest.fixture
def twitter_user():
    return SimpleNamespace(
        id="user-1",
        name="Reader",
        screen_name="reader",
        description="Profile",
        followers_count=5,
        following_count=3,
        statuses_count=12,
        verified=False,
        created_at="today",
    )


@pytest.fixture
def twitter_tweet(twitter_user):
    return SimpleNamespace(
        id="tweet-1",
        text="café",
        created_at="today",
        user=twitter_user,
        favorite_count=2,
        retweet_count=3,
        reply_count=4,
        view_count=10,
        replies=[],
        thread=[],
    )
