export const meta = {
  name: "compose-page",
  description:
    "Two-pass page composition: build an intent-led section spine with final content, then independently meaning-gate every section and assemble the corrected page.",
  whenToUse:
    "Building a real web page or landing UI whose sections must carry purposeful content and connect into one argument. Uses at most two model calls.",
  phases: [
    {
      title: "Draft",
      detail: "define the page intent and build every section around it",
    },
    {
      title: "Gate",
      detail: "independently refute weak sections, revise them, and assemble",
    },
  ],
};

const pageBrief =
  args && typeof args === "object" && !Array.isArray(args)
    ? args
    : { brief: typeof args === "string" ? args : null };

if (!pageBrief.brief) {
  throw new Error(
    "compose-page requires args.brief describing the page subject, audience, and single action. args.output and args.constraints are optional.",
  );
}

const outputFormat =
  pageBrief.output || "self-contained semantic HTML5 with an inline <style>";
const sharedConstraints = pageBrief.constraints || "";

const DRAFT_SCHEMA = {
  type: "object",
  properties: {
    thesis: { type: "string" },
    audience: { type: "string" },
    primaryAction: { type: "string" },
    sections: {
      type: "array",
      minItems: 6,
      maxItems: 8,
      items: {
        type: "object",
        properties: {
          id: { type: "string" },
          role: { enum: ["header", "hero", "middle", "bottom", "footer"] },
          oneIdea: { type: "string" },
          relatesToPrevious: { type: "string" },
          setsUpNext: { type: "string" },
          whyItEarnsItsPlace: { type: "string" },
          contentRationale: { type: "string" },
          markup: { type: "string" },
        },
        required: [
          "id",
          "role",
          "oneIdea",
          "whyItEarnsItsPlace",
          "contentRationale",
          "markup",
        ],
      },
    },
  },
  required: ["thesis", "audience", "primaryAction", "sections"],
};

const FINAL_SCHEMA = {
  type: "object",
  properties: {
    sectionGateOutcomes: {
      type: "array",
      minItems: 6,
      maxItems: 8,
      items: {
        type: "object",
        properties: {
          id: { type: "string" },
          acceptedWithoutRevision: { type: "boolean" },
          gateReason: { type: "string" },
          defectsFixed: { type: "array", items: { type: "string" } },
        },
        required: [
          "id",
          "acceptedWithoutRevision",
          "gateReason",
          "defectsFixed",
        ],
      },
    },
    page: { type: "string" },
  },
  required: ["sectionGateOutcomes", "page"],
};

phase("Draft");
const draft = await agent(
  `Design and build a complete web page from intent rather than a placeholder skeleton. PAGE BRIEF: ${pageBrief.brief}. AUDIENCE, THESIS, AND ACTION: infer one precise audience, one sentence the page argues, and one primary action. SECTION SPINE: create 6 to 8 ordered sections spanning header, hero, two to four middle sections, bottom call to action, and footer. Each section must carry one idea, earn its place, connect to its neighbors, and contain purposeful final content. Build the sections in order so later content continues rather than repeats earlier content. Never use lorem ipsum, placeholder labels, unsupported facts, decorative-only elements, or claims the brief does not support. OUTPUT FORMAT: ${outputFormat}. Return markup per section without a document wrapper. ${sharedConstraints ? `CONSTRAINTS: ${sharedConstraints}` : ""}`,
  {
    label: "draft",
    phase: "Draft",
    schema: DRAFT_SCHEMA,
    model: "sonnet",
    maxTurns: 8,
  },
);

phase("Gate");
const finalPage = await agent(
  `Independently meaning-gate and assemble this page draft. Try to refute every section. A section fails when any element is filler, placeholder, off-thesis, unrelated to its neighbors, decorative without informational purpose, or an unsupported claim. Revise every failed section in place, preserve sound sections, and then assemble one complete ${outputFormat} document with a coherent arc from the hero's promise to the primary action. Return one gate outcome per section and the corrected ready-to-ship page. Keep the supplied constraints authoritative. PAGE BRIEF: ${pageBrief.brief}. ${sharedConstraints ? `CONSTRAINTS: ${sharedConstraints}.` : ""} DRAFT: ${JSON.stringify(draft)}.`,
  {
    label: "gate",
    phase: "Gate",
    schema: FINAL_SCHEMA,
    model: "sonnet",
    maxTurns: 8,
  },
);

return {
  thesis: draft.thesis,
  audience: draft.audience,
  primaryAction: draft.primaryAction,
  spine: draft.sections.map(
    ({ contentRationale, markup, ...sectionSpecification }) =>
      sectionSpecification,
  ),
  sectionGateOutcomes: finalPage.sectionGateOutcomes,
  page: finalPage.page,
};
