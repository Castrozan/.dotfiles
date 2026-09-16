#!/usr/bin/env python3
"""twikit-cli: CLI wrapper for twikit, optimized for agent use.

Outputs JSON for machine consumption. Loads cookies from
~/.config/twikit/cookies.json (login once, reuse forever).
Credentials read from agenix-managed secret files.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from twikit_cli_authentication import command_login  # noqa: E402
from twikit_cli_read_operations import (  # noqa: E402
    command_bookmarks,
    command_followers,
    command_following,
    command_replies,
    command_search,
    command_thread,
    command_timeline,
    command_trends,
    command_tweet,
    command_user,
    command_user_tweets,
    command_whoami,
)
from twikit_cli_write_operations import (  # noqa: E402
    command_bookmark,
    command_dm,
    command_like,
    command_post,
    command_retweet,
)


def build_argument_parser():
    parser = argparse.ArgumentParser(
        prog="twikit-cli",
        description="X/Twitter CLI for agents, JSON output, cookie-based auth",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser(
        "login", help="Login (auto from secrets or interactive)"
    )
    login_parser.add_argument("--totp", help="TOTP secret for 2FA")

    subparsers.add_parser("whoami", help="Show authenticated user")

    search_parser = subparsers.add_parser("search", help="Search tweets")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "-n", "--limit", type=int, default=20, help="Max results"
    )
    search_parser.add_argument(
        "-p", "--product", choices=["latest", "top", "media"], default="latest"
    )

    user_parser = subparsers.add_parser("user", help="Get user profile")
    user_parser.add_argument("username", help="X username (without @)")

    user_tweets_parser = subparsers.add_parser("user-tweets", help="Get user tweets")
    user_tweets_parser.add_argument("username", help="X username")
    user_tweets_parser.add_argument("-n", "--limit", type=int, default=20)
    user_tweets_parser.add_argument(
        "-t",
        "--type",
        choices=["tweets", "replies", "media", "likes"],
        default="tweets",
    )

    tweet_parser = subparsers.add_parser("tweet", help="Get tweet by ID")
    tweet_parser.add_argument("tweet_id", help="Tweet ID")

    replies_parser = subparsers.add_parser("replies", help="Get tweet replies")
    replies_parser.add_argument("tweet_id", help="Tweet ID")
    replies_parser.add_argument("-n", "--limit", type=int, default=20)

    thread_parser = subparsers.add_parser("thread", help="Get tweet self-thread")
    thread_parser.add_argument("tweet_id", help="Tweet ID (first tweet in thread)")

    subparsers.add_parser("trends", help="Get trending topics")

    timeline_parser = subparsers.add_parser("timeline", help="Home timeline")
    timeline_parser.add_argument("-n", "--limit", type=int, default=20)

    followers_parser = subparsers.add_parser("followers", help="Get followers")
    followers_parser.add_argument("username")
    followers_parser.add_argument("-n", "--limit", type=int, default=20)

    following_parser = subparsers.add_parser("following", help="Get following")
    following_parser.add_argument("username")
    following_parser.add_argument("-n", "--limit", type=int, default=20)

    post_parser = subparsers.add_parser("post", help="Create a tweet")
    post_parser.add_argument("text", help="Tweet text")
    post_parser.add_argument("--reply-to", help="Tweet ID to reply to")

    like_parser = subparsers.add_parser("like", help="Like a tweet")
    like_parser.add_argument("tweet_id")

    retweet_parser = subparsers.add_parser("retweet", help="Retweet")
    retweet_parser.add_argument("tweet_id")

    bookmark_parser = subparsers.add_parser("bookmark", help="Bookmark a tweet")
    bookmark_parser.add_argument("tweet_id")

    bookmarks_parser = subparsers.add_parser("bookmarks", help="Get bookmarks")
    bookmarks_parser.add_argument("-n", "--limit", type=int, default=20)

    dm_parser = subparsers.add_parser("dm", help="Send DM")
    dm_parser.add_argument("user_id", help="User ID to DM")
    dm_parser.add_argument("text", help="Message text")

    return parser


def build_command_dispatch_table():
    return {
        "login": command_login,
        "whoami": command_whoami,
        "search": command_search,
        "user": command_user,
        "user-tweets": command_user_tweets,
        "tweet": command_tweet,
        "replies": command_replies,
        "thread": command_thread,
        "trends": command_trends,
        "timeline": command_timeline,
        "followers": command_followers,
        "following": command_following,
        "post": command_post,
        "like": command_like,
        "retweet": command_retweet,
        "bookmark": command_bookmark,
        "bookmarks": command_bookmarks,
        "dm": command_dm,
    }


def main():
    parser = build_argument_parser()
    args = parser.parse_args()
    dispatch_table = build_command_dispatch_table()
    asyncio.run(dispatch_table[args.command](args))


if __name__ == "__main__":
    main()
