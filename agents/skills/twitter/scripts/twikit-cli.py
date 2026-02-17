#!/usr/bin/env python3
"""twikit-cli — CLI wrapper for twikit, optimized for agent use.

Outputs JSON for machine consumption. Loads cookies from
~/.config/twikit/cookies.json (login once, reuse forever).
Credentials read from agenix-managed secret files.
"""

import asyncio
import argparse
import json
import sys
import os
from pathlib import Path

COOKIES_PATH = Path(os.environ.get("TWIKIT_COOKIES_PATH", str(Path.home() / ".config" / "twikit" / "cookies.json")))
USERNAME_FILE = os.environ.get("TWIKIT_USERNAME_FILE", "")
EMAIL_FILE = os.environ.get("TWIKIT_EMAIL_FILE", "")
PASSWORD_FILE = os.environ.get("TWIKIT_PASSWORD_FILE", "")


def read_secret_file(filepath):
    """Read a secret from an agenix-managed file."""
    if not filepath or not Path(filepath).exists():
        return None
    return Path(filepath).read_text().strip()


def serialize_tweet(tweet):
    """Extract structured data from a Tweet object."""
    return {
        "id": tweet.id,
        "text": tweet.text,
        "created_at": tweet.created_at,
        "user": {
            "id": tweet.user.id if tweet.user else None,
            "name": tweet.user.name if tweet.user else None,
            "username": tweet.user.screen_name if tweet.user else None,
        },
        "favorite_count": tweet.favorite_count,
        "retweet_count": tweet.retweet_count,
        "reply_count": tweet.reply_count,
        "view_count": tweet.view_count,
        "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}" if tweet.user else None,
    }


def serialize_user(user):
    """Extract structured data from a User object."""
    return {
        "id": user.id,
        "name": user.name,
        "username": user.screen_name,
        "description": user.description,
        "followers_count": user.followers_count,
        "following_count": user.following_count,
        "tweet_count": user.statuses_count,
        "verified": user.verified,
        "created_at": user.created_at,
        "url": f"https://x.com/{user.screen_name}",
    }


def output_json(data):
    """Print JSON to stdout."""
    print(json.dumps(data, ensure_ascii=False, default=str))


async def get_client():
    """Create and authenticate a twikit client. Auto-login from secrets if no cookies."""
    from twikit import Client

    client = Client("en-US")

    if COOKIES_PATH.exists():
        client.load_cookies(str(COOKIES_PATH))
        return client

    username = read_secret_file(USERNAME_FILE)
    email = read_secret_file(EMAIL_FILE)
    password = read_secret_file(PASSWORD_FILE)

    if not all([username, email, password]):
        print(
            json.dumps({"error": "No cookies and no credentials found. Run: twikit-cli login"}),
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[twikit-cli] No cookies found. Logging in as {username}...", file=sys.stderr)

    COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)

    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
    )

    client.save_cookies(str(COOKIES_PATH))
    os.chmod(str(COOKIES_PATH), 0o600)
    print(f"[twikit-cli] Cookies saved to {COOKIES_PATH}", file=sys.stderr)

    return client


async def command_login(args):
    """Login — uses agenix secrets or interactive fallback. Saves cookies."""
    from twikit import Client

    client = Client("en-US")

    COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)

    if COOKIES_PATH.exists():
        print(f"Loading existing cookies from {COOKIES_PATH}")
        client.load_cookies(str(COOKIES_PATH))
        try:
            user_id = await client.user_id()
            print(f"Already authenticated as user {user_id}")
            return
        except Exception:
            print("Existing cookies expired, need fresh login")

    username = read_secret_file(USERNAME_FILE)
    email = read_secret_file(EMAIL_FILE)
    password = read_secret_file(PASSWORD_FILE)

    if not all([username, email, password]):
        print("No agenix secrets found, falling back to interactive login")
        username = input("X username: ")
        email = input("X email: ")
        password = input("X password: ")

    totp_secret = None
    if args.totp:
        totp_secret = args.totp

    print(f"Logging in as {username}...")

    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
        totp_secret=totp_secret,
    )

    client.save_cookies(str(COOKIES_PATH))
    os.chmod(str(COOKIES_PATH), 0o600)
    print(f"Cookies saved to {COOKIES_PATH}")


async def command_search(args):
    """Search tweets."""
    client = await get_client()
    product_map = {"latest": "Latest", "top": "Top", "media": "Media"}
    product = product_map.get(args.product, "Latest")
    try:
        tweets = await client.search_tweet(args.query, product, count=args.limit)
        results = [serialize_tweet(tweet) for tweet in tweets]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Search failed for '{args.query}': {error}", "query": args.query})


async def command_user(args):
    """Get user profile by username."""
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        output_json(serialize_user(user))
    except Exception as error:
        output_json({"error": f"Failed to fetch user {args.username}: {error}", "username": args.username})


async def command_user_tweets(args):
    """Get tweets from a user."""
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        tweet_type_map = {"tweets": "Tweets", "replies": "Replies", "media": "Media", "likes": "Likes"}
        tweet_type = tweet_type_map.get(args.type, "Tweets")
        tweets = await client.get_user_tweets(user.id, tweet_type, count=args.limit)
        results = [serialize_tweet(tweet) for tweet in tweets]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch tweets for {args.username}: {error}", "username": args.username})


async def command_tweet(args):
    """Get a single tweet by ID."""
    client = await get_client()
    try:
        tweet = await client.get_tweet_by_id(args.tweet_id)
        output_json(serialize_tweet(tweet))
    except (KeyError, AttributeError) as error:
        output_json({"error": f"Failed to fetch tweet {args.tweet_id}: {error}", "tweet_id": args.tweet_id})


async def command_replies(args):
    """Get replies to a tweet."""
    client = await get_client()
    try:
        tweet = await client.get_tweet_by_id(args.tweet_id)
        replies = await tweet.get_replies()
        results = [serialize_tweet(reply) for reply in replies[:args.limit]]
        output_json(results)
    except (KeyError, AttributeError) as error:
        output_json({"error": f"Failed to fetch replies for {args.tweet_id}: {error}", "tweet_id": args.tweet_id})


async def command_trends(args):
    """Get trending topics."""
    client = await get_client()
    trends = await client.get_trends("trending")
    output_json(trends)


async def command_followers(args):
    """Get user's followers."""
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        followers = await client.get_user_followers(user.id, count=args.limit)
        results = [serialize_user(follower) for follower in followers]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch followers for {args.username}: {error}", "username": args.username})


async def command_following(args):
    """Get who a user follows."""
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        following = await client.get_user_following(user.id, count=args.limit)
        results = [serialize_user(u) for u in following]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch following for {args.username}: {error}", "username": args.username})


async def command_post(args):
    """Create a tweet."""
    client = await get_client()
    try:
        tweet = await client.create_tweet(text=args.text, reply_to=args.reply_to)
        output_json(serialize_tweet(tweet))
    except Exception as error:
        output_json({"error": f"Failed to post tweet: {error}"})


async def command_like(args):
    """Like a tweet."""
    client = await get_client()
    try:
        await client.favorite_tweet(args.tweet_id)
        output_json({"status": "liked", "tweet_id": args.tweet_id})
    except Exception as error:
        output_json({"error": f"Failed to like tweet {args.tweet_id}: {error}", "tweet_id": args.tweet_id})


async def command_retweet(args):
    """Retweet a tweet."""
    client = await get_client()
    try:
        await client.retweet(args.tweet_id)
        output_json({"status": "retweeted", "tweet_id": args.tweet_id})
    except Exception as error:
        output_json({"error": f"Failed to retweet {args.tweet_id}: {error}", "tweet_id": args.tweet_id})


async def command_bookmark(args):
    """Bookmark a tweet."""
    client = await get_client()
    try:
        await client.create_bookmark(args.tweet_id)
        output_json({"status": "bookmarked", "tweet_id": args.tweet_id})
    except Exception as error:
        output_json({"error": f"Failed to bookmark tweet {args.tweet_id}: {error}", "tweet_id": args.tweet_id})


async def command_bookmarks(args):
    """Get bookmarked tweets."""
    client = await get_client()
    try:
        bookmarks = await client.get_bookmarks(count=args.limit)
        results = [serialize_tweet(tweet) for tweet in bookmarks]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch bookmarks: {error}"})


async def command_dm(args):
    """Send a direct message."""
    client = await get_client()
    try:
        await client.send_dm(args.user_id, args.text)
        output_json({"status": "sent", "user_id": args.user_id})
    except Exception as error:
        output_json({"error": f"Failed to send DM to {args.user_id}: {error}", "user_id": args.user_id})


async def command_timeline(args):
    """Get home timeline."""
    client = await get_client()
    try:
        tweets = await client.get_timeline(count=args.limit)
        results = [serialize_tweet(tweet) for tweet in tweets]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch timeline: {error}"})


async def command_whoami(args):
    """Show authenticated user info."""
    client = await get_client()
    user = await client.user()
    output_json(serialize_user(user))


def main():
    parser = argparse.ArgumentParser(
        prog="twikit-cli",
        description="X/Twitter CLI for agents — JSON output, cookie-based auth",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # login
    login_parser = subparsers.add_parser("login", help="Login (auto from secrets or interactive)")
    login_parser.add_argument("--totp", help="TOTP secret for 2FA")

    # whoami
    subparsers.add_parser("whoami", help="Show authenticated user")

    # search
    search_parser = subparsers.add_parser("search", help="Search tweets")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-n", "--limit", type=int, default=20, help="Max results")
    search_parser.add_argument("-p", "--product", choices=["latest", "top", "media"], default="latest")

    # user
    user_parser = subparsers.add_parser("user", help="Get user profile")
    user_parser.add_argument("username", help="X username (without @)")

    # user-tweets
    user_tweets_parser = subparsers.add_parser("user-tweets", help="Get user tweets")
    user_tweets_parser.add_argument("username", help="X username")
    user_tweets_parser.add_argument("-n", "--limit", type=int, default=20)
    user_tweets_parser.add_argument("-t", "--type", choices=["tweets", "replies", "media", "likes"], default="tweets")

    # tweet
    tweet_parser = subparsers.add_parser("tweet", help="Get tweet by ID")
    tweet_parser.add_argument("tweet_id", help="Tweet ID")

    # replies
    replies_parser = subparsers.add_parser("replies", help="Get tweet replies")
    replies_parser.add_argument("tweet_id", help="Tweet ID")
    replies_parser.add_argument("-n", "--limit", type=int, default=20)

    # trends
    subparsers.add_parser("trends", help="Get trending topics")

    # timeline
    timeline_parser = subparsers.add_parser("timeline", help="Home timeline")
    timeline_parser.add_argument("-n", "--limit", type=int, default=20)

    # followers
    followers_parser = subparsers.add_parser("followers", help="Get followers")
    followers_parser.add_argument("username")
    followers_parser.add_argument("-n", "--limit", type=int, default=20)

    # following
    following_parser = subparsers.add_parser("following", help="Get following")
    following_parser.add_argument("username")
    following_parser.add_argument("-n", "--limit", type=int, default=20)

    # post
    post_parser = subparsers.add_parser("post", help="Create a tweet")
    post_parser.add_argument("text", help="Tweet text")
    post_parser.add_argument("--reply-to", help="Tweet ID to reply to")

    # like
    like_parser = subparsers.add_parser("like", help="Like a tweet")
    like_parser.add_argument("tweet_id")

    # retweet
    retweet_parser = subparsers.add_parser("retweet", help="Retweet")
    retweet_parser.add_argument("tweet_id")

    # bookmark
    bookmark_parser = subparsers.add_parser("bookmark", help="Bookmark a tweet")
    bookmark_parser.add_argument("tweet_id")

    # bookmarks
    bookmarks_parser = subparsers.add_parser("bookmarks", help="Get bookmarks")
    bookmarks_parser.add_argument("-n", "--limit", type=int, default=20)

    # dm
    dm_parser = subparsers.add_parser("dm", help="Send DM")
    dm_parser.add_argument("user_id", help="User ID to DM")
    dm_parser.add_argument("text", help="Message text")

    args = parser.parse_args()

    command_map = {
        "login": command_login,
        "whoami": command_whoami,
        "search": command_search,
        "user": command_user,
        "user-tweets": command_user_tweets,
        "tweet": command_tweet,
        "replies": command_replies,
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

    asyncio.run(command_map[args.command](args))


if __name__ == "__main__":
    main()
