export const meta = {
  name: "compose-page",
  description:
    "Build a web page section by section with a per-section meaning gate: establish a thesis and section spine, then construct each section in order with real purposeful content while an adversarial critic refutes filler, placeholder, off-thesis, neighborless, and decorative-only elements before the next section starts, then a whole-page coherence pass.",
  whenToUse:
    "Building a real web page or landing UI and you want every section to carry purposeful content that relates to the others, instead of a skeleton of placeholder mock content.",
  phases: [
    {
      title: "Foundation",
      detail: "thesis, audience, single primary action, ordered section spine",
    },
    {
      title: "Build",
      detail:
        "construct each section in order, meaning-gate it, revise until it passes",
    },
    {
      title: "Coherence",
      detail: "whole-page arc, no orphan or redundant section, assemble",
    },
  ],
};

const pageBrief =
  args && typeof args === "object" && !Array.isArray(args)
    ? args
    : { brief: typeof args === "string" ? args : null };

if (!pageBrief.brief) {
  throw new Error(
    "compose-page requires args.brief describing the page: subject, audience, and the single action it should drive. Optionally args.output (target format, e.g. 'self-contained semantic HTML5 with inline <style>') and args.constraints (design tokens, voice, length, things not to invent).",
  );
}

const outputFormat =
  pageBrief.output || "self-contained semantic HTML5 with an inline <style>";
const sharedConstraints = pageBrief.constraints || "";

const FOUNDATION_SCHEMA = {
  type: "object",
  properties: {
    thesis: { type: "string" },
    audience: { type: "string" },
    primaryAction: { type: "string" },
    sections: {
      type: "array",
      items: {
        type: "object",
        properties: {
          id: { type: "string" },
          role: {
            enum: ["header", "hero", "middle", "bottom", "footer"],
          },
          oneIdea: { type: "string" },
          relatesToPrev: { type: "string" },
          setsUpNext: { type: "string" },
          whyItEarnsItsPlace: { type: "string" },
        },
        required: ["id", "role", "oneIdea", "whyItEarnsItsPlace"],
      },
    },
  },
  required: ["thesis", "audience", "primaryAction", "sections"],
};

const SECTION_SCHEMA = {
  type: "object",
  properties: {
    id: { type: "string" },
    contentRationale: { type: "string" },
    markup: { type: "string" },
  },
  required: ["id", "contentRationale", "markup"],
};

const GATE_SCHEMA = {
  type: "object",
  properties: {
    passes: { type: "boolean" },
    reason: { type: "string" },
    defects: {
      type: "array",
      items: {
        type: "object",
        properties: {
          element: { type: "string" },
          kind: {
            enum: [
              "filler",
              "placeholder",
              "off-thesis",
              "no-relation-to-neighbors",
              "decorative-only",
              "unsupported-claim",
            ],
          },
          problem: { type: "string" },
          fix: { type: "string" },
        },
        required: ["element", "kind", "problem", "fix"],
      },
    },
  },
  required: ["passes", "reason", "defects"],
};

phase("Foundation");
const foundation = await agent(
  `You are designing the meaning spine of a web page before any markup exists. This step is the antidote to the "random skeleton" failure where a page is scaffolded all at once with placeholder mock content that means nothing. Define intent first.\n\nPAGE BRIEF: ${pageBrief.brief}\n${sharedConstraints ? `CONSTRAINTS: ${sharedConstraints}\n` : ""}\nProduce: a one-sentence THESIS the entire page argues; the AUDIENCE; the single PRIMARY ACTION the page drives; and an ordered list of SECTIONS spanning header, a title/hero, two to four middle sections, a bottom call-to-action, and a footer. For every section give its id, its role, the ONE idea it carries, how it relates to the previous section, what it sets up for the next, and why removing it would lose meaning. A section that cannot justify why removing it loses meaning does not belong in the spine. Do not write any markup yet.`,
  { label: "foundation", phase: "Foundation", schema: FOUNDATION_SCHEMA },
);

log(
  `Spine: ${foundation.sections.length} sections around thesis "${foundation.thesis}". Building each in order; sections build sequentially because every section grounds its content in the actual markup of the ones before it.`,
);

const maximumRevisionsPerSection = 3;
const builtSections = [];

for (
  let sectionIndex = 0;
  sectionIndex < foundation.sections.length;
  sectionIndex++
) {
  const sectionSpecification = foundation.sections[sectionIndex];
  const priorMarkup =
    builtSections
      .map((section) => `SECTION ${section.id}:\n${section.markup}`)
      .join("\n\n") || "(none yet, this is the first section)";

  let acceptedSection = null;
  let outstandingDefects = null;

  for (let attempt = 1; attempt <= maximumRevisionsPerSection; attempt++) {
    const candidate = await agent(
      `You are building one section of a web page, in order, as part of a section-by-section construction. Build ONLY the "${sectionSpecification.id}" section (role: ${sectionSpecification.role}). Inject real, purposeful, final content. Never use lorem ipsum, never use placeholder labels like "Feature one" or "Lorem", never invent facts the brief does not support.\n\nPAGE THESIS: ${foundation.thesis}\nAUDIENCE: ${foundation.audience}\nPRIMARY ACTION: ${foundation.primaryAction}\nTHIS SECTION'S ONE IDEA: ${sectionSpecification.oneIdea}\nHOW IT RELATES TO THE PREVIOUS SECTION: ${sectionSpecification.relatesToPrev || "n/a"}\nWHAT IT SETS UP NEXT: ${sectionSpecification.setsUpNext || "n/a"}\nWHY IT EARNS ITS PLACE: ${sectionSpecification.whyItEarnsItsPlace}\n\nOUTPUT FORMAT: ${outputFormat}. Emit only the markup for this one section (no document wrapper, no <head>); it will be assembled with the others later. ${sharedConstraints ? `CONSTRAINTS: ${sharedConstraints}\n` : ""}\nALREADY-BUILT SECTIONS (ground your content in these so it continues the page rather than repeating or contradicting them):\n${priorMarkup}\n${outstandingDefects ? `\nYour previous attempt was rejected by the meaning gate. Fix exactly these defects: ${JSON.stringify(outstandingDefects)}` : ""}`,
      {
        label: `build:${sectionSpecification.id}:attempt-${attempt}`,
        phase: "Build",
        schema: SECTION_SCHEMA,
      },
    );

    const verdict = await agent(
      `You are the meaning gate for one section of a web page. Adversarially judge whether every element of this section carries real meaning, and try hard to REFUTE it. The page exists to fight placeholder skeletons, so reject anything that is filler, a placeholder, off-thesis, unrelated to its neighbors, decorative with no informational purpose, or an unsupported claim the brief does not back. It passes ONLY if every element advances the section's one idea, the section advances the page thesis, and it connects to the sections around it. Default to passes=false when in doubt and name each defect with a concrete fix.\n\nPAGE THESIS: ${foundation.thesis}\nTHIS SECTION'S ONE IDEA: ${sectionSpecification.oneIdea}\nIT MUST RELATE TO PREVIOUS: ${sectionSpecification.relatesToPrev || "n/a"}\nIT MUST SET UP NEXT: ${sectionSpecification.setsUpNext || "n/a"}\n${sharedConstraints ? `CONSTRAINTS THE CONTENT MUST RESPECT: ${sharedConstraints}\n` : ""}\nSECTION CONTENT RATIONALE: ${candidate.contentRationale}\nSECTION MARKUP:\n${candidate.markup}`,
      {
        label: `gate:${sectionSpecification.id}:attempt-${attempt}`,
        phase: "Build",
        schema: GATE_SCHEMA,
      },
    );

    acceptedSection = { ...candidate, gate: verdict, attempts: attempt };
    if (verdict.passes) {
      break;
    }
    outstandingDefects = verdict.defects;
  }

  builtSections.push(acceptedSection);
  log(
    `Section "${sectionSpecification.id}" ${acceptedSection.gate.passes ? "passed" : "best-effort after " + maximumRevisionsPerSection + " tries"} the meaning gate.`,
  );
}

phase("Coherence");
const assembledSections = builtSections
  .map((section) => `SECTION ${section.id}:\n${section.markup}`)
  .join("\n\n");

const finalPage = await agent(
  `You are assembling section-built markup into one coherent web page and doing the final coherence pass. Read the whole thing as a single document and fix only what cross-section coherence requires: the page must carry an arc from the hero's promise to the primary action that resolves it, hold one consistent voice, contain no orphan or redundant section, and flow from each section to the next. Do not reopen meaning decisions already gated per section; integrate them.\n\nPAGE THESIS: ${foundation.thesis}\nPRIMARY ACTION: ${foundation.primaryAction}\nOUTPUT FORMAT: ${outputFormat}. Return the complete, ready-to-ship page as one document.\n${sharedConstraints ? `CONSTRAINTS: ${sharedConstraints}\n` : ""}\nSECTION SPINE (for reference): ${JSON.stringify(foundation.sections)}\n\nSECTIONS TO ASSEMBLE, IN ORDER:\n${assembledSections}\n\nReturn only the final page document, nothing else.`,
  { label: "coherence", phase: "Coherence" },
);

return {
  thesis: foundation.thesis,
  audience: foundation.audience,
  primaryAction: foundation.primaryAction,
  spine: foundation.sections,
  sectionGateOutcomes: builtSections.map((section) => ({
    id: section.id,
    passed: section.gate.passes,
    attempts: section.attempts,
    gateReason: section.gate.reason,
  })),
  page: finalPage,
};
