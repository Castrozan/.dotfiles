import json
import sys


def parse_fetch_results(raw_text):
    text = raw_text.strip()
    return json.loads(text) if text else []


def is_fetched(result):
    return isinstance(result, dict) and not result.get("archon_failed")


def pool_items(results):
    fetched = [result for result in results if is_fetched(result)]
    items = [
        {**item, "source": result.get("source", "")}
        for result in fetched
        for item in result.get("items") or []
    ]
    return {"items": items, "itemCount": len(items), "sourcesHit": len(fetched)}


def main():
    print(json.dumps(pool_items(parse_fetch_results(sys.stdin.read()))))


if __name__ == "__main__":
    main()
