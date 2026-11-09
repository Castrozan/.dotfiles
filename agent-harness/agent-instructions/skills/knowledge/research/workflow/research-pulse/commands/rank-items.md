### Ranking

Rank the pooled items for the topic serialized on the next line.
$INPUTS.topic

The pooled items were fetched from GitHub, arXiv, Hacker News, Hugging Face, Reddit, Lobste.rs and X. Do three things:
1\) DEDUP: collapse items that are the same underlying thing (e.g. a paper that also appears on HN and X) into one,
keeping the most authoritative URL. 2) SCORE each surviving item 1-10 for relevance to the topic, and assign a theme
(Papers | Releases | Discussion | X chatter | Other).

3\) FILTER OUT hype, marketing, and low-signal noise. Return the ranked, deduped top items by score, at most the count
serialized on the next line.
$INPUTS.max_items

ITEMS: the pooled items are serialized on the next line.
$INPUTS.items
