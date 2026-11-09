import argparse
import json

DEFAULT_TOPIC = (
    "the latest in AI agents, LLM inference, local models, and developer tooling"
)
DEFAULT_ACCOUNTS = "steipete,karpathy,simonw"

DATE_HINT = (
    'First run "date +%Y-%m-%d" via Bash to learn today\'s date, '
    "then prioritise items from roughly the last 7 days."
)
FREE_API_RULE = (
    "Use Bash curl against the free public API (no key). Prefer curl over WebFetch "
    "for exact JSON. Fall back to WebSearch\n"
    "only if the API fails. Return real URLs you actually saw, never invented ones."
)


def instruction_data(value):
    return (
        "`"
        + json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace(
            "`", "\\u0060"
        )
        + "`"
    )


def parse_accounts(accounts):
    parsed = [account.strip() for account in accounts.split(",") if account.strip()]
    return parsed or DEFAULT_ACCOUNTS.split(",")


def source_definitions(topic, seed_accounts):
    topic_data = instruction_data(topic)
    return [
        (
            "github",
            f"""### Search

Find GitHub repositories, releases, and notable commits relevant to
{topic_data}.

{DATE_HINT}
{FREE_API_RULE}
Query the GitHub search API, e.g. `curl -s
"https://api.github.com/search/repositories?q=<keywords>+pushed:>=<date>&sort=stars&order=desc&per_page=15"` and the
releases of any clearly-relevant tracked repos. Return up to 12 items.""",
        ),
        (
            "arxiv",
            f"""### Search

Find recent arXiv papers relevant to
{topic_data}
in cs.AI, cs.CL, cs.LG.

{DATE_HINT}
{FREE_API_RULE}
Query the arXiv API, e.g. `curl -s
"http://export.arxiv.org/api/query?search_query=all:<keywords>&sortBy=submittedDate&sortOrder=descending&max_results=15"`
and parse the Atom feed. Summaries should be plain-language. Return up to 12 items.""",
        ),
        (
            "hackernews",
            f"""### Search

Find Hacker News stories and Show HN posts relevant to
{topic_data}.

{DATE_HINT}
{FREE_API_RULE}
Query the Algolia HN API, e.g. `curl -s
"https://hn.algolia.com/api/v1/search_by_date?query=<keywords>&tags=story&numericFilters=points>30"`. Include the HN
discussion URL. Return up to 12 items.""",
        ),
        (
            "huggingface",
            f"""### Search

Find trending or newly-released Hugging Face models and datasets relevant to
{topic_data}.

{FREE_API_RULE}
Query the HF Hub API, e.g. `curl -s "https://huggingface.co/api/models?search=<keywords>&sort=trending&limit=15"` and
`curl -s "https://huggingface.co/api/datasets?search=<keywords>&sort=trending&limit=10"`. Return up to 10 items.""",
        ),
        (
            "reddit",
            f"""### Search

Find high-signal discussion relevant to
{topic_data}
from r/LocalLLaMA and r/MachineLearning (and any other clearly-relevant subreddit).

{FREE_API_RULE}
Query the public Reddit JSON with a custom User-Agent, e.g. `curl -s -H "User-Agent: research-pulse/1.0"
"https://www.reddit.com/r/LocalLLaMA/top.json?t=week&limit=15"`. Return up to 10 items.""",
        ),
        (
            "lobsters",
            f"""### Search

Find recent Lobste.rs stories relevant to
{topic_data}
, especially ai/ml/programming tags.

{FREE_API_RULE}
Query e.g. `curl -s "https://lobste.rs/t/ai.json"` and `curl -s "https://lobste.rs/newest.json"`, filter to the
topic. Return up to 8 items.""",
        ),
        (
            "x",
            f"""### Search

Find notable X/Twitter posts relevant to
{topic_data}.

Use the twikit-cli tool via Bash: run `twikit-cli search \\"<keywords>\\" -n 25` (it outputs JSON). Additionally
peek at these high-signal SEED accounts as a soft signal boost - `twikit-cli user-tweets <handle> -n 10` for each of:
{instruction_data(", ".join(seed_accounts))}.
CRITICAL: the seed accounts are only a hint - rank by relevance to the topic and include the best posts regardless of
author; never restrict results to the seed accounts. If twikit-cli errors, note it and return what you got. Return up to
12 items with the post URL.""",
        ),
    ]


def source_prompts(topic, seed_accounts):
    return [
        f'{prompt}\n\nSet the "source" field of your answer to exactly "{key}".'
        for key, prompt in source_definitions(topic, seed_accounts)
    ]


def parse_command_line():
    parser = argparse.ArgumentParser(
        prog="research-pulse-sources",
        description="Emit one fetch prompt per research source for the research-pulse workflow.",
    )
    parser.add_argument("--topic", default="")
    parser.add_argument("--accounts", default="")
    return parser.parse_args()


def main():
    arguments = parse_command_line()
    topic = arguments.topic.strip() or DEFAULT_TOPIC
    prompts = source_prompts(topic, parse_accounts(arguments.accounts))
    print(json.dumps({"topic": topic, "sources": prompts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
