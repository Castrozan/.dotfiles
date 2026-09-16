const researchSourcePrompts = (topic, seedAccounts) => {
  const dateHint =
    'First run "date +%Y-%m-%d" via Bash to learn today\'s date, then prioritise items from roughly the last 7 days.';
  const freeApiRule =
    "Use Bash curl against the free public API (no key). Prefer curl over WebFetch for exact JSON. Fall back to WebSearch\nonly if the API fails. Return real URLs you actually saw, never invented ones.";

  return [
    {
      key: "github",
      prompt: `### Search

Find GitHub repositories, releases, and notable commits relevant to
${instructionData(topic)}.

${dateHint}
${freeApiRule}
Query the GitHub search API, e.g. \`curl -s
"https://api.github.com/search/repositories?q=<keywords>+pushed:>=<date>&sort=stars&order=desc&per_page=15"\` and the
releases of any clearly-relevant tracked repos. Return up to 12 items.`,
    },
    {
      key: "arxiv",
      prompt: `### Search

Find recent arXiv papers relevant to
${instructionData(topic)}
in cs.AI, cs.CL, cs.LG.

${dateHint}
${freeApiRule}
Query the arXiv API, e.g. \`curl -s
"http://export.arxiv.org/api/query?search_query=all:<keywords>&sortBy=submittedDate&sortOrder=descending&max_results=15"\`
and parse the Atom feed. Summaries should be plain-language. Return up to 12 items.`,
    },
    {
      key: "hackernews",
      prompt: `### Search

Find Hacker News stories and Show HN posts relevant to
${instructionData(topic)}.

${dateHint}
${freeApiRule}
Query the Algolia HN API, e.g. \`curl -s
"https://hn.algolia.com/api/v1/search_by_date?query=<keywords>&tags=story&numericFilters=points>30"\`. Include the HN
discussion URL. Return up to 12 items.`,
    },
    {
      key: "huggingface",
      prompt: `### Search

Find trending or newly-released Hugging Face models and datasets relevant to
${instructionData(topic)}.

${freeApiRule}
Query the HF Hub API, e.g. \`curl -s "https://huggingface.co/api/models?search=<keywords>&sort=trending&limit=15"\` and
\`curl -s "https://huggingface.co/api/datasets?search=<keywords>&sort=trending&limit=10"\`. Return up to 10 items.`,
    },
    {
      key: "reddit",
      prompt: `### Search

Find high-signal discussion relevant to
${instructionData(topic)}
from r/LocalLLaMA and r/MachineLearning (and any other clearly-relevant subreddit).

${freeApiRule}
Query the public Reddit JSON with a custom User-Agent, e.g. \`curl -s -H "User-Agent: research-pulse/1.0"
"https://www.reddit.com/r/LocalLLaMA/top.json?t=week&limit=15"\`. Return up to 10 items.`,
    },
    {
      key: "lobsters",
      prompt: `### Search

Find recent Lobste.rs stories relevant to
${instructionData(topic)}
, especially ai/ml/programming tags.

${freeApiRule}
Query e.g. \`curl -s "https://lobste.rs/t/ai.json"\` and \`curl -s "https://lobste.rs/newest.json"\`, filter to the
topic. Return up to 8 items.`,
    },
    {
      key: "x",
      prompt: `### Search

Find notable X/Twitter posts relevant to
${instructionData(topic)}.

Use the twikit-cli tool via Bash: run \`twikit-cli search \\"<keywords>\\" -n 25\` (it outputs JSON). Additionally
peek at these high-signal SEED accounts as a soft signal boost - \`twikit-cli user-tweets <handle> -n 10\` for each of:
${instructionData(seedAccounts.join(", "))}.
CRITICAL: the seed accounts are only a hint - rank by relevance to the topic and include the best posts regardless of
author; never restrict results to the seed accounts. If twikit-cli errors, note it and return what you got. Return up to
12 items with the post URL.`,
    },
  ];
};
