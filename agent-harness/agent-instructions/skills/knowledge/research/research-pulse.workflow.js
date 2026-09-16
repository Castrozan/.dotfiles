export const meta = {
  name: "research-pulse",
  description:
    "On-demand AI/dev community research digest: fan out across GitHub, arXiv, Hacker News, Hugging Face, Reddit, Lobste.rs and X for a dynamic topic, dedup and relevance-rank, return a themed digest. Invoke-and-exit, no resident infra.",
  phases: [
    {
      title: "Fetch",
      detail: "parallel source agents query each source for the topic",
    },
    {
      title: "Rank",
      detail: "merge, dedup, relevance-score vs the topic, drop low-signal",
    },
    {
      title: "Synthesize",
      detail: "themed markdown digest with why-it-matters lines",
    },
  ],
};

const instructionData = (value) =>
  "`" + JSON.stringify(value).replaceAll("`", "\\u0060") + "`";

let input = args || {};
if (typeof input === "string") {
  const trimmed = input.trim();
  if (trimmed.startsWith("{")) {
    try {
      input = JSON.parse(trimmed);
    } catch {
      input = { topic: trimmed };
    }
  } else {
    input = { topic: trimmed };
  }
}
const topic =
  input.topic ||
  "the latest in AI agents, LLM inference, local models, and developer tooling";
const seedAccounts =
  input.accounts && input.accounts.length
    ? input.accounts
    : ["steipete", "karpathy", "simonw"];
const maxItems = input.maxItems || 12;

const SOURCES = researchSourcePrompts(topic, seedAccounts);

const boundedAgentOptions = (label, phaseName, model, effort, schema) => ({
  label,
  phase: phaseName,
  schema,
  model,
  effort,
});

phase("Fetch");
const fetched = (
  await parallel(
    SOURCES.map(
      (s) => () =>
        agent(
          s.prompt,
          boundedAgentOptions(
            `fetch:${s.key}`,
            "Fetch",
            "haiku",
            "low",
            ITEMS_SCHEMA,
          ),
        ),
    ),
  )
).filter(Boolean);

const allItems = fetched.flatMap((f) =>
  (f.items || []).map((it) => ({ ...it, source: f.source })),
);
log(
  `Fetched ${allItems.length} items across ${fetched.length}/${SOURCES.length} sources`,
);

if (!allItems.length) {
  return {
    topic,
    digest: `No items found for "${topic}". All sources returned empty - check network or twikit-cli auth.`,
    itemCount: 0,
    sourcesHit: fetched.length,
  };
}

phase("Rank");
const ranked = await agent(
  `### Ranking

Topic:
${instructionData(topic)}.


Below is a pooled list of items fetched from GitHub, arXiv, Hacker News, Hugging Face, Reddit, Lobste.rs and X. Do three
things: 1) DEDUP: collapse items that are the same underlying thing (e.g. a paper that also appears on HN and X) into
one, keeping the most authoritative URL. 2) SCORE each surviving item 1-10 for relevance to the topic, and assign a
theme (Papers | Releases | Discussion | X chatter | Other).

3\\) FILTER OUT hype, marketing, and low-signal noise; keep
only the top
${instructionData(maxItems)}
by score.

Return the ranked, deduped top
${instructionData(maxItems)}.


ITEMS:

${instructionData(allItems)}`,
  boundedAgentOptions("rank", "Rank", "sonnet", "medium", RANKED_SCHEMA),
);

const top = (ranked.items || [])
  .sort((a, b) => b.score - a.score)
  .slice(0, maxItems);
log(`Ranked to ${top.length} high-signal items`);

phase("Synthesize");
const digest = await agent(
  `### Synthesis

Write a tight, skimmable markdown research digest for the topic
${instructionData(topic)}.
Audience: a senior AI/dev engineer who wants signal, not fluff.

Group the items below by their theme (order: Papers, Releases, Discussion, X chatter, Other - skip empty groups). For
each item: a bold linked title \`[title](url)\`, then a single \`- why:\` line on why it matters. No preamble, no
padding, no invented facts. Keep it under ~400 words. End with a one-line "Top pick:" calling out the single
highest-signal item.

RANKED ITEMS:

${instructionData(top)}`,
  boundedAgentOptions("digest", "Synthesize", "sonnet", "medium"),
);

return { topic, digest, itemCount: top.length, sourcesHit: fetched.length };
