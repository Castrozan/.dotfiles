# Tweet from Pirate Face — abliterated-model discovery

Capture: `ReadItLater Inbox/Tweet from Pirate Face (2026-09-30 19-47-22).md`
Origin: https://x.com/thepirateface/status/2105230533899018315
Verdict: **drop**

## The origin as resolved

Read the captured status through the twitter route, not a topic search. `twikit-cli tweet
2105230533899018315` currently fails with its known `'value'` parser error. The unattended browser did load the
canonical X page with the matching author, status id and title, although X timed out when asked for its accessibility
tree. The capture contains the complete post text, and resolving its `t.co` link confirms that the attachment is the
status's own video rather than an external article.

The post announces one catalog change: models described as “Abliterated,” “Heretic,” and “Obliteratus” are now
discoverable on Pirate Face. Those names refer to model variants made with refusal-removal techniques; the announcement
does not introduce a model, a runtime, an API, or an evaluation of any particular variant.

Pirate Face itself is a preservation and discovery layer over Hugging Face. Its current site says that it indexes
eligible Hugging Face models, records source checksums and lists community torrents. A listed magnet can keep working
while peers retain the files if the Hugging Face source disappears. The important current boundary is equally explicit:
the `HF_ENDPOINT=https://pirateface.co` compatibility API is “coming soon,” datasets are also “soon,” and direct model
publishing without a Hugging Face source is not live.

Sources checked on 2026-09-30:

- captured status: https://x.com/thepirateface/status/2105230533899018315
- current product and FAQ: https://pirateface.co/
- saved-model catalog: https://pirateface.co/catalog
- existing Hugging Face `abliteration` catalog: https://huggingface.co/models?other=abliteration

## What it touches here

Nothing should change.

The closest live consumer is the research pulse's Hugging Face source at
`agent-harness/agent-instructions/skills/knowledge/research/pulse/source-prompts.js:49-57`. It deliberately asks the
Hugging Face JSON APIs for both models and datasets. Pirate Face's current terminal surface returns a text list of
torrented models, while its compatible endpoint and dataset support are not live, so substituting it would remove
metadata and dataset coverage rather than add resilience.

The other apparent fit is
`machine-configuration/development/local-language-models/ollama-home-manager.nix:45-63`, which installs and serves
Ollama. That module has no model declaration, no Hugging Face download path and, outside its isolated evaluation test,
no import anywhere in the repository. Repository-wide search also finds no `HF_ENDPOINT` setting. Pirate Face therefore
cannot replace or unblock that service as configured.

This decision adds no dependency or configuration, replaces and deletes nothing, and carries no activation cost.

## Reasoning

Adopting an alternate Hugging Face endpoint would be the strongest possible fit, but the endpoint is still a stated
future feature. Adding Pirate Face's `/s/<query>` text search to the research pulse is the weaker alternative: Hugging
Face already exposes these variants through its model filters, and the existing source needs structured metadata plus
datasets. A trial also has no decision to answer because no particular model, workload, or runtime was captured.

This is a drop rather than a reference. The saved fact is a transient catalog-indexing announcement, not a durable
technique or a named model worth retaining, and the catalog remains directly searchable if a future local-model task
creates a real need. Filing it would preserve a second discovery surface without changing what can be run here.

## Vault entry

None. A drop files no Second Brain entry.
