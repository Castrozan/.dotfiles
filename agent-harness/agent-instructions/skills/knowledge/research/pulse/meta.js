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
