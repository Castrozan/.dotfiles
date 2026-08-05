"""Read-only twikit commands: search, user profile, tweets, replies, threads, trends."""

from twikit_cli_authentication import get_client
from twikit_cli_serializers import output_json, serialize_tweet, serialize_user


async def command_search(args):
    client = await get_client()
    product_map = {"latest": "Latest", "top": "Top", "media": "Media"}
    product = product_map.get(args.product, "Latest")
    try:
        tweets = await client.search_tweet(args.query, product, count=args.limit)
        results = [serialize_tweet(tweet) for tweet in tweets]
        output_json(results)
    except Exception as error:
        output_json(
            {"error": f"Search failed for '{args.query}': {error}", "query": args.query}
        )


async def command_user(args):
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        output_json(serialize_user(user))
    except Exception as error:
        output_json(
            {
                "error": f"Failed to fetch user {args.username}: {error}",
                "username": args.username,
            }
        )


async def command_user_tweets(args):
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        tweet_type_map = {
            "tweets": "Tweets",
            "replies": "Replies",
            "media": "Media",
            "likes": "Likes",
        }
        tweet_type = tweet_type_map.get(args.type, "Tweets")
        tweets = await client.get_user_tweets(user.id, tweet_type, count=args.limit)
        results = [serialize_tweet(tweet) for tweet in tweets]
        output_json(results)
    except Exception as error:
        output_json(
            {
                "error": f"Failed to fetch tweets for {args.username}: {error}",
                "username": args.username,
            }
        )


async def command_tweet(args):
    client = await get_client()
    try:
        tweet = await client.get_tweet_by_id(args.tweet_id)
        output_json(serialize_tweet(tweet))
    except (KeyError, AttributeError) as error:
        output_json(
            {
                "error": f"Failed to fetch tweet {args.tweet_id}: {error}",
                "tweet_id": args.tweet_id,
            }
        )


async def command_replies(args):
    client = await get_client()
    try:
        tweet = await client.get_tweet_by_id(args.tweet_id)
        reply_tweets = []
        for reply_group in tweet.replies:
            reply_tweets.append(serialize_tweet(reply_group))
            if hasattr(reply_group, "replies") and reply_group.replies:
                for nested_reply in reply_group.replies:
                    reply_tweets.append(serialize_tweet(nested_reply))
        output_json(reply_tweets[: args.limit])
    except (KeyError, AttributeError) as error:
        output_json(
            {
                "error": f"Failed to fetch replies for {args.tweet_id}: {error}",
                "tweet_id": args.tweet_id,
            }
        )


async def command_thread(args):
    client = await get_client()
    try:
        tweet = await client.get_tweet_by_id(args.tweet_id)
        thread_tweets = [serialize_tweet(tweet)]
        if hasattr(tweet, "thread") and tweet.thread:
            for thread_tweet in tweet.thread:
                serialized = serialize_tweet(thread_tweet)
                if serialized["id"] != tweet.id:
                    thread_tweets.append(serialized)
        output_json(thread_tweets)
    except (KeyError, AttributeError) as error:
        output_json(
            {
                "error": f"Failed to fetch thread for {args.tweet_id}: {error}",
                "tweet_id": args.tweet_id,
            }
        )


async def command_trends(args):
    client = await get_client()
    trends = await client.get_trends("trending")
    output_json(trends)


async def command_followers(args):
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        followers = await client.get_user_followers(user.id, count=args.limit)
        results = [serialize_user(follower) for follower in followers]
        output_json(results)
    except Exception as error:
        output_json(
            {
                "error": f"Failed to fetch followers for {args.username}: {error}",
                "username": args.username,
            }
        )


async def command_following(args):
    client = await get_client()
    try:
        user = await client.get_user_by_screen_name(args.username)
        following = await client.get_user_following(user.id, count=args.limit)
        results = [serialize_user(u) for u in following]
        output_json(results)
    except Exception as error:
        output_json(
            {
                "error": f"Failed to fetch following for {args.username}: {error}",
                "username": args.username,
            }
        )


async def command_bookmarks(args):
    client = await get_client()
    try:
        bookmarks = await client.get_bookmarks(count=args.limit)
        results = [serialize_tweet(tweet) for tweet in bookmarks]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch bookmarks: {error}"})


async def command_timeline(args):
    client = await get_client()
    try:
        tweets = await client.get_timeline(count=args.limit)
        results = [serialize_tweet(tweet) for tweet in tweets]
        output_json(results)
    except Exception as error:
        output_json({"error": f"Failed to fetch timeline: {error}"})


async def command_whoami(args):
    client = await get_client()
    user = await client.user()
    output_json(serialize_user(user))
