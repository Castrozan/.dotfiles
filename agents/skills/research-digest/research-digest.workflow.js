export const meta = {
  name: "research-digest",
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

const ITEMS_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["source", "items"],
  properties: {
    source: { type: "string" },
    items: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["title", "url", "summary"],
        properties: {
          title: { type: "string" },
          url: { type: "string" },
          summary: {
            type: "string",
            description: "one-to-two sentence factual summary",
          },
          published: {
            type: "string",
            description: 'ISO date or relative; "unknown" if absent',
          },
          signal: {
            type: "string",
            description: "why this is notable for the topic",
          },
        },
      },
    },
  },
};

const RANKED_SCHEMA = {
  type: "object",
  additionalProperties: false,
  required: ["items"],
  properties: {
    items: {
      type: "array",
      items: {
        type: "object",
        additionalProperties: false,
        required: ["title", "url", "source", "score", "theme", "why"],
        properties: {
          title: { type: "string" },
          url: { type: "string" },
          source: { type: "string" },
          score: { type: "number", description: "relevance to topic, 1-10" },
          theme: {
            type: "string",
            description: "Papers | Releases | Discussion | X chatter | Other",
          },
          why: {
            type: "string",
            description: "one line on why it matters for the topic",
          },
        },
      },
    },
  },
};

const dateHint = `First run "date -u +%Y-%m-%d" via Bash to learn today's date, then prioritise items from roughly the last 7 days.`;
const freeApiRule = `Use Bash curl against the free public API (no key). Prefer curl over WebFetch for exact JSON. Fall back to WebSearch only if the API fails. Return real URLs you actually saw, never invented ones.`;

const SOURCES = [
  {
    key: "github",
    prompt: `Find GitHub repositories, releases, and notable commits relevant to "${topic}". ${dateHint} ${freeApiRule} Query the GitHub search API, e.g. curl -s "https://api.github.com/search/repositories?q=<keywords>+pushed:>=<date>&sort=stars&order=desc&per_page=15" and the releases of any clearly-relevant tracked repos. Return up to 12 items.`,
  },
  {
    key: "arxiv",
    prompt: `Find recent arXiv papers relevant to "${topic}" in cs.AI, cs.CL, cs.LG. ${dateHint} ${freeApiRule} Query the arXiv API, e.g. curl -s "http://export.arxiv.org/api/query?search_query=all:<keywords>&sortBy=submittedDate&sortOrder=descending&max_results=15" and parse the Atom feed. Summaries should be plain-language. Return up to 12 items.`,
  },
  {
    key: "hackernews",
    prompt: `Find Hacker News stories and Show HN posts relevant to "${topic}". ${dateHint} ${freeApiRule} Query the Algolia HN API, e.g. curl -s "https://hn.algolia.com/api/v1/search_by_date?query=<keywords>&tags=story&numericFilters=points>30". Include the HN discussion URL. Return up to 12 items.`,
  },
  {
    key: "huggingface",
    prompt: `Find trending or newly-released Hugging Face models and datasets relevant to "${topic}". ${freeApiRule} Query the HF Hub API, e.g. curl -s "https://huggingface.co/api/models?search=<keywords>&sort=trending&limit=15" and curl -s "https://huggingface.co/api/datasets?search=<keywords>&sort=trending&limit=10". Return up to 10 items.`,
  },
  {
    key: "reddit",
    prompt: `Find high-signal discussion relevant to "${topic}" from r/LocalLLaMA and r/MachineLearning (and any other clearly-relevant subreddit). ${freeApiRule} Query the public Reddit JSON with a custom User-Agent, e.g. curl -s -H "User-Agent: research-digest/1.0" "https://www.reddit.com/r/LocalLLaMA/top.json?t=week&limit=15". Return up to 10 items.`,
  },
  {
    key: "lobsters",
    prompt: `Find recent Lobste.rs stories relevant to "${topic}", especially ai/ml/programming tags. ${freeApiRule} Query e.g. curl -s "https://lobste.rs/t/ai.json" and curl -s "https://lobste.rs/newest.json", filter to the topic. Return up to 8 items.`,
  },
  {
    key: "x",
    prompt: `Find notable X/Twitter posts relevant to "${topic}". Use the twikit-cli tool via Bash: run "twikit-cli search \\"<keywords>\\" -n 25" (it outputs JSON). Additionally peek at these high-signal SEED accounts as a soft signal boost - "twikit-cli user-tweets <handle> -n 10" for each of: ${seedAccounts.join(", ")}. CRITICAL: the seed accounts are only a hint - rank by relevance to the topic and include the best posts regardless of author; never restrict results to the seed accounts. If twikit-cli errors, note it and return what you got. Return up to 12 items with the post URL.`,
  },
];

phase("Fetch");
const fetched = (
  await parallel(
    SOURCES.map(
      (s) => () =>
        agent(s.prompt, {
          label: `fetch:${s.key}`,
          phase: "Fetch",
          schema: ITEMS_SCHEMA,
        }),
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
  `Topic: "${topic}".\n\nBelow is a pooled list of items fetched from GitHub, arXiv, Hacker News, Hugging Face, Reddit, Lobste.rs and X. Do three things:\n1. DEDUP: collapse items that are the same underlying thing (e.g. a paper that also appears on HN and X) into one, keeping the most authoritative URL.\n2. SCORE each surviving item 1-10 for relevance to the topic, and assign a theme (Papers | Releases | Discussion | X chatter | Other).\n3. FILTER OUT hype, marketing, and low-signal noise; keep only the top ${maxItems} by score.\n\nReturn the ranked, deduped top ${maxItems}.\n\nITEMS:\n${JSON.stringify(allItems)}`,
  { label: "rank", phase: "Rank", schema: RANKED_SCHEMA },
);

const top = (ranked.items || [])
  .sort((a, b) => b.score - a.score)
  .slice(0, maxItems);
log(`Ranked to ${top.length} high-signal items`);

phase("Synthesize");
const digest = await agent(
  `Write a tight, skimmable markdown research digest for the topic "${topic}". Audience: a senior AI/dev engineer who wants signal, not fluff.\n\nGroup the items below by their theme (order: Papers, Releases, Discussion, X chatter, Other - skip empty groups). For each item: a bold linked title "[title](url)", then a single "- why:" line on why it matters. No preamble, no padding, no invented facts. Keep it under ~400 words. End with a one-line "Top pick:" calling out the single highest-signal item.\n\nRANKED ITEMS:\n${JSON.stringify(top)}`,
  { label: "digest", phase: "Synthesize" },
);

return { topic, digest, itemCount: top.length, sourcesHit: fetched.length };
