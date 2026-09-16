import json
import sys
from types import SimpleNamespace

import pytest


@pytest.mark.parametrize(
    "arguments,method,positionals,keywords,kind",
    [
        (
            ["search", "nix", "-p", "top", "-n", "3"],
            "search_tweet",
            ("nix", "Top"),
            {"count": 3},
            "tweets",
        ),
        (
            ["search", "nix", "-p", "media"],
            "search_tweet",
            ("nix", "Media"),
            {"count": 20},
            "tweets",
        ),
        (["search", "nix"], "search_tweet", ("nix", "Latest"), {"count": 20}, "tweets"),
        (["user", "reader"], "get_user_by_screen_name", ("reader",), {}, "user"),
        (
            ["user-tweets", "reader", "-t", "likes"],
            "get_user_tweets",
            ("user-1", "Likes"),
            {"count": 20},
            "tweets",
        ),
        (["tweet", "tweet-1"], "get_tweet_by_id", ("tweet-1",), {}, "tweet"),
        (
            ["followers", "reader"],
            "get_user_followers",
            ("user-1",),
            {"count": 20},
            "users",
        ),
        (
            ["following", "reader"],
            "get_user_following",
            ("user-1",),
            {"count": 20},
            "users",
        ),
        (["bookmarks"], "get_bookmarks", (), {"count": 20}, "tweets"),
        (["timeline"], "get_timeline", (), {"count": 20}, "tweets"),
        (["whoami"], "user", (), {}, "user"),
        (["trends"], "get_trends", ("trending",), {}, "trends"),
        (
            ["post", "café", "--reply-to", "parent"],
            "create_tweet",
            (),
            {"text": "café", "reply_to": "parent"},
            "tweet",
        ),
    ],
)
def test_commands_preserve_cli_arguments_and_json(
    twitter_modules,
    twitter_user,
    twitter_tweet,
    monkeypatch,
    capsys,
    arguments,
    method,
    positionals,
    keywords,
    kind,
):
    client = twitter_modules.client
    client.get_user_by_screen_name.return_value = twitter_user
    response = {
        "tweets": [twitter_tweet],
        "tweet": twitter_tweet,
        "users": [twitter_user],
        "user": twitter_user,
        "trends": ["Nix"],
    }[kind]
    getattr(client, method).return_value = response
    monkeypatch.setattr(sys, "argv", ["twikit-cli", *arguments])
    twitter_modules.cli.main()
    getattr(client, method).assert_awaited_once_with(*positionals, **keywords)
    result = json.loads(capsys.readouterr().out)
    if kind == "trends":
        assert result == ["Nix"]
    else:
        item = result[0] if isinstance(result, list) else result
        assert item["id"] == ("user-1" if kind in {"user", "users"} else "tweet-1")
        assert item["url"].startswith("https://x.com/reader")
        if kind in {"tweet", "tweets"}:
            assert item["text"] == "café" and item["view_count"] == 10


@pytest.mark.parametrize(
    "command,method,status",
    [
        ("like", "favorite_tweet", "liked"),
        ("retweet", "retweet", "retweeted"),
        ("bookmark", "create_bookmark", "bookmarked"),
        ("dm", "send_dm", "sent"),
    ],
)
def test_write_commands_acknowledge_only_success(
    twitter_modules, monkeypatch, capsys, command, method, status
):
    positionals = ["target", "message"] if command == "dm" else ["target"]
    monkeypatch.setattr(sys, "argv", ["twikit-cli", command, *positionals])
    twitter_modules.cli.main()
    getattr(twitter_modules.client, method).assert_awaited_once_with(*positionals)
    key = "user_id" if command == "dm" else "tweet_id"
    assert json.loads(capsys.readouterr().out) == {"status": status, key: "target"}
    getattr(twitter_modules.client, method).side_effect = RuntimeError("rejected")
    twitter_modules.cli.main()
    failure = json.loads(capsys.readouterr().out)
    assert "rejected" in failure["error"] and "status" not in failure
    assert failure[key] == "target"


@pytest.mark.parametrize(
    "arguments,method",
    [
        (["search", "query"], "search_tweet"),
        (["user", "reader"], "get_user_by_screen_name"),
        (["user-tweets", "reader"], "get_user_by_screen_name"),
        (["followers", "reader"], "get_user_by_screen_name"),
        (["following", "reader"], "get_user_by_screen_name"),
        (["tweet", "id"], "get_tweet_by_id"),
        (["thread", "id"], "get_tweet_by_id"),
        (["replies", "id"], "get_tweet_by_id"),
        (["bookmarks"], "get_bookmarks"),
        (["timeline"], "get_timeline"),
        (["post", "text"], "create_tweet"),
    ],
)
def test_read_failures_emit_json_context(
    twitter_modules, monkeypatch, capsys, arguments, method
):
    getattr(twitter_modules.client, method).side_effect = KeyError("unavailable")
    monkeypatch.setattr(sys, "argv", ["twikit-cli", *arguments])
    twitter_modules.cli.main()
    failure = json.loads(capsys.readouterr().out)
    assert "unavailable" in failure["error"]
    if len(arguments) > 1 and arguments[0] != "post":
        assert arguments[1] in failure.values()


def test_replies_apply_limit_and_thread_omits_duplicate_root(
    twitter_modules, twitter_tweet, monkeypatch, capsys
):
    reply = SimpleNamespace(**{**vars(twitter_tweet), "id": "reply", "user": None})
    nested = SimpleNamespace(**{**vars(twitter_tweet), "id": "nested"})
    reply.replies = [nested]
    twitter_tweet.replies = [reply, nested]
    twitter_tweet.thread = [twitter_tweet, reply]
    twitter_modules.client.get_tweet_by_id.return_value = twitter_tweet
    monkeypatch.setattr(sys, "argv", ["twikit-cli", "replies", "tweet-1", "-n", "2"])
    twitter_modules.cli.main()
    result = json.loads(capsys.readouterr().out)
    assert [item["id"] for item in result] == ["reply", "nested"]
    assert result[0]["url"] is None and result[0]["user"]["id"] is None
    monkeypatch.setattr(sys, "argv", ["twikit-cli", "thread", "tweet-1"])
    twitter_modules.cli.main()
    assert [item["id"] for item in json.loads(capsys.readouterr().out)] == [
        "tweet-1",
        "reply",
    ]
