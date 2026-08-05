"""Write twikit commands: post, like, retweet, bookmark, dm."""

from twikit_cli_authentication import get_client
from twikit_cli_serializers import output_json, serialize_tweet


async def command_post(args):
    client = await get_client()
    try:
        tweet = await client.create_tweet(text=args.text, reply_to=args.reply_to)
        output_json(serialize_tweet(tweet))
    except Exception as error:
        output_json({"error": f"Failed to post tweet: {error}"})


async def command_like(args):
    client = await get_client()
    try:
        await client.favorite_tweet(args.tweet_id)
        output_json({"status": "liked", "tweet_id": args.tweet_id})
    except Exception as error:
        output_json(
            {
                "error": f"Failed to like tweet {args.tweet_id}: {error}",
                "tweet_id": args.tweet_id,
            }
        )


async def command_retweet(args):
    client = await get_client()
    try:
        await client.retweet(args.tweet_id)
        output_json({"status": "retweeted", "tweet_id": args.tweet_id})
    except Exception as error:
        output_json(
            {
                "error": f"Failed to retweet {args.tweet_id}: {error}",
                "tweet_id": args.tweet_id,
            }
        )


async def command_bookmark(args):
    client = await get_client()
    try:
        await client.create_bookmark(args.tweet_id)
        output_json({"status": "bookmarked", "tweet_id": args.tweet_id})
    except Exception as error:
        output_json(
            {
                "error": f"Failed to bookmark tweet {args.tweet_id}: {error}",
                "tweet_id": args.tweet_id,
            }
        )


async def command_dm(args):
    client = await get_client()
    try:
        await client.send_dm(args.user_id, args.text)
        output_json({"status": "sent", "user_id": args.user_id})
    except Exception as error:
        output_json(
            {
                "error": f"Failed to send DM to {args.user_id}: {error}",
                "user_id": args.user_id,
            }
        )
