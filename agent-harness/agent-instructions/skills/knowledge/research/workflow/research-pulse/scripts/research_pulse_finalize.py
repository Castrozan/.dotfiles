import argparse
import json
import sys


def parse_json_or_empty(raw_text, empty_value):
    text = raw_text.strip()
    return json.loads(text) if text else empty_value


def top_ranked(ranked, maximum_items):
    items = (ranked or {}).get("items") or []
    return sorted(items, key=lambda item: item["score"], reverse=True)[:maximum_items]


def no_items_result(topic, sources_hit):
    return {
        "topic": topic,
        "digest": (
            f'No items found for "{topic}". All sources returned empty - '
            "check network or twikit-cli auth."
        ),
        "itemCount": 0,
        "sourcesHit": sources_hit,
    }


def digest_result(topic, digest, item_count, sources_hit):
    return {
        "topic": topic,
        "digest": digest,
        "itemCount": item_count,
        "sourcesHit": sources_hit,
    }


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="research-pulse-finalize",
        description="Select top ranked items or build the final research-pulse result from stdin JSON.",
    )
    parser.add_argument("mode", choices=["select", "result"])
    parser.add_argument("--topic", default="")
    parser.add_argument("--max-items", type=int, default=12)
    return parser.parse_args()


def main():
    arguments = parse_command_line()
    payload = parse_json_or_empty(sys.stdin.read(), {})
    if arguments.mode == "select":
        top = top_ranked(payload, arguments.max_items)
        print(json.dumps({"items": top, "itemCount": len(top)}))
        return
    sources_hit = payload["pool"]["sourcesHit"]
    if payload["pool"]["itemCount"] == 0:
        result = no_items_result(arguments.topic, sources_hit)
    else:
        result = digest_result(
            arguments.topic,
            payload["digest"]["digest"],
            payload["select"]["itemCount"],
            sources_hit,
        )
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
