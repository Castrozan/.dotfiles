"""Cookie/secret paths, secret reading, and JSON serialization helpers."""

import json
import os
from pathlib import Path

COOKIES_PATH = Path(
    os.environ.get(
        "TWIKIT_COOKIES_PATH", str(Path.home() / ".config" / "twikit" / "cookies.json")
    )
)
USERNAME_FILE = os.environ.get("TWIKIT_USERNAME_FILE", "")
EMAIL_FILE = os.environ.get("TWIKIT_EMAIL_FILE", "")
PASSWORD_FILE = os.environ.get("TWIKIT_PASSWORD_FILE", "")


def read_secret_file(filepath):
    if not filepath or not Path(filepath).exists():
        return None
    return Path(filepath).read_text().strip()


def serialize_tweet(tweet):
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
        "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}"
        if tweet.user
        else None,
    }


def serialize_user(user):
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
    print(json.dumps(data, ensure_ascii=False, default=str))
