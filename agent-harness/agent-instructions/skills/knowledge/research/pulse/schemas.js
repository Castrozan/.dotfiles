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
