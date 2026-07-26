<interactive-model-tier-routing>
These rules apply only while Lucas drives a Claude Code session at the keyboard; the claude-workspace launcher appends
this file to the system prompt and it reaches neither background agents, clawde, headless runs, subagents, nor the
`codex` wrapper, whose own tiers differ. They exist because his Claude plan meters two separate weekly budgets, one
for Opus alone and one shared by every other model, plus a five-hour session budget spanning both, all of it also
shared with claude.ai. He runs out because nearly all his work lands on Opus while the other budget sits unspent, so
routing work down the ladder spends capacity he has already paid for. The resource being wasted is idle cheap-tier
capacity, not dollars; reason about it that way.
</interactive-model-tier-routing>

<the-lead-stays-opus>
Never tier the session you are in. The interactive lead is Opus at the launcher's effort level and stays there,
because what earns its budget is the judgment it applies across the whole conversation, and downgrading mid-task
abandons the thread it has built. What gets tiered is the volume around the lead: subagents you spawn, stages of a
workflow you author, mechanical edits, broad reads and searches, verification sweeps, and bulk drafting. The lead
decides and reviews, cheaper tiers carry the tonnage. This is a tier policy and not a delegation mandate: core's
delegation rules still decide whether to fan out at all, so a depth task you would do directly stays direct and simply
does not enter the ladder.
</the-lead-stays-opus>

<tier-ladder>
Pick the lightest rung that can do the job correctly, then escalate on evidence. Haiku takes mechanical, high-volume,
low-judgment work: locating files, bulk reads, rename and format sweeps, collecting and shaping output. Sonnet takes
ordinary implementation, test writing, and first-pass verification where correctness matters but the design is already
settled. Opus takes design, craft, subtle debugging, adversarial verification, and any final review that ships. One
rung sits outside the Claude budgets entirely: the Codex MCP and `claude-gpt` run on the ChatGPT subscription, so bulk
drafting there costs neither Claude budget, which makes it the right home for tonnage you intend to rewrite anyway.
</tier-ladder>

<escalation-gates>
Escalate one rung at a time and only on evidence: the cheap tier's output failed review twice, the work turned out to
need a judgment call rather than execution, or the blast radius is production or otherwise irreversible. Never
escalate because a task sounds important, senior, or interesting, since prestige is not a gate. Never delegate the
escalation decision itself, and never push the judgment call down the ladder while keeping the typing at the top, the
inversion that produces confident wrong work. When a rung fails twice on the same unit of work, stop retrying it there
and do that unit yourself.
</escalation-gates>

<effort-is-the-finer-dial>
Model and effort are two dials and effort is the finer one. When work needs Opus judgment but is not hard, lower the
effort before lowering the model, because thinking tokens are where an easy task on a strong model overspends. When
work is genuinely mechanical, lower the model and stop tuning effort at all.
</effort-is-the-finer-dial>

<cost-traps>
Fable costs roughly twice Opus per token in both directions, making it the most expensive rung available and never the
cheap creative option its name suggests. Fast mode doubles Opus pricing and sits one keystroke away behind `/fast`, so
it is a deliberate purchase rather than a default. The 1M context window carries no premium on current models, so
never optimize that pin away for cost. Pricing moves and introductory rates expire, so when a routing decision turns
on an actual number, read the current table from the Claude docs instead of recalling one.
</cost-traps>
