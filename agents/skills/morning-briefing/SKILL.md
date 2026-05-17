---
name: morning-briefing
description: Golden's 08:00 routine — resume HEARTBEAT.md or run the market briefing (US/BR markets, FX, portfolio quotes, headlines, geopolitics), save to briefings/<date>.md, and ship the FULL report to Lucas via Discord MCP reply. Heartbeat-only.
---

<priority_order>
On every tick walk these in order. Stop at the first that fires; always run steps 4-5.

1. **Resume in-flight work.** Read HEARTBEAT.md in the golden workspace. If it has a real objective (anything beyond "No active work"), continue it and skip 2-3.
2. **Self-maintenance sweep** (only if HEARTBEAT is empty). See `<self_maintenance_authority>`.
3. **Run the briefing.** See `<briefing_pipeline>` and `<briefing_markdown_layout>`.
4. **Save** to `briefings/YYYY-MM-DD.md`. Single canonical version per day — overwrite if re-running, no `-rerun` / `-morning` suffixes, no editorial preamble explaining that it's a re-run.
5. **Deliver** the FULL briefing to Lucas via `mcp__plugin_discord_discord__reply` using chat_id from `lucas-dm-chat-id.txt`. Discord splits long messages automatically — do NOT pre-strip to a summary. Skip the send only if `quiet-mornings.flag` exists or the chat-id file is missing.
</priority_order>

<self_maintenance_authority>
Fix without asking when the diff is mechanical and bounded:
- portfolio.json desync from confirmed B3 data (settled trade not reflected, closed position still listed active).
- A previous-day briefing that ends mid-section. Mark `## INCOMPLETE — recovered next tick` at top.
- HEARTBEAT.md saying "in-flight" when artifacts on disk show the work landed. Reset to "No active work."
- b3_endpoints.py regex no longer matches the freshest capture (B3 changed the path).
- Zombie processes (dashboards, listeners) left from yesterday.

Do not touch: persona/CLAUDE.md/dotfiles, semantic portfolio.json changes (positions not confirmed by Lucas), other skills, anything outside the golden workspace.

Boundary: if a fix would take >~10 min, write it as a "## Pendências técnicas" item instead. The briefing is the deliverable, not refactors.

Log every fix in a "## Self-maintenance" section so Lucas can audit.
</self_maintenance_authority>

<briefing_pipeline>
Collect fields in this order, parallel where possible. Fast local snapshot first.

1. **`./bin/golden snapshot`** — Ibov, BOVA11, IVVB11, USD/BRL in one call. Cross-check USD/BRL against investing.com only if move >1%.
2. **US close** (yesterday NY): S&P 500 `^GSPC`, NASDAQ `^IXIC`, Dow `^DJI` via Yahoo Finance quote pages.
3. **US futures**: ES=F, NQ=F via Yahoo.
4. **Portfolio**: read portfolio.json; for every active ticker run `./bin/golden quote <ticker>`; compute P&L vs avg_cost. Flag earnings within 14 days, ex-dividend this week, T+2 settlement events for trades inside last 3 days, and any material underlying news.
5. **Top 3 macro headlines**: one WebSearch per area — (a) largest BDR underlying, (b) Brazilian macro (Selic, IPCA Focus, Copom), (c) third area driven by current portfolio exposure. Every headline must end in "this affects X position because Y" — abstract macro doesn't ship.
6. **Geopolítica e mercados globais**: 2-4 live themes. WebSearch each for "last 24-48h". Standard rotation pool: China-EUA (visits, tariffs, chip controls, Taiwan, yuan), Oriente Médio (Iran, Hormuz, oil, Israel-Gaza), Russia-Ucrânia (sanctions, EU energy), US politics (Fed, fiscal, elections), LatAm (Argentina, Venezuela, México). Format per theme: status (no fabrication — if quiet since DD/MM, declare it), 1st order (commodities/indices/FX with numbers), 2nd order (Lucas's specific positions: BDRs via FX/sector, Caixinhas via Selic, Ibov via VALE/PETR), opportunity/risk with concrete action. Every theme must terminate in a position-level claim or be cut.

Every number gets a source URL. Sources unreachable get "source unreachable" — never fabricate.
</briefing_pipeline>

<dashboard_data_freshness>
The dashboard reads portfolio.json and data/raw/b3/<latest>/. On the morning tick, flag "B3 capture stale — N dias" under "## Pendências" if the freshest B3 capture is older than 7 days AND `.env` has B3 credentials. Do NOT auto-trigger Skill(b3-portal) from the heartbeat — that's an interactive, Lucas-driven flow. Do not start the dashboard from the heartbeat; if it's down, that's a pendência.
</dashboard_data_freshness>

<briefing_markdown_layout>
Hard cap: **30 filled lines total** (blank separators don't count toward the budget but use them sparingly — Discord wraps tightly). Density over completeness — if a fact does not change Lucas's decision today, cut it. No markdown tables (each row eats a line). No paragraph narratives — one-liners only. Sources collapse into a single footer line.

Fixed structure (target line counts in parentheses, sum ≈ 24-27):

```markdown
# Morning briefing — YYYY-MM-DD (dia-da-semana)                                            (1)

**US ontem**: S&P <pct> (<price>), NASDAQ <pct> (<price>), Dow <pct>. Futures: ES <pct>, NQ <pct>.  (1)
**FX**: USD/BRL <price> (<pct> [+ contexto se move grande]).                               (1)
**BR**: Ibov <price> (<pct>) — <driver 1-frase>. BOVA11 <pct>, IVVB11 <pct>.               (1)

**Posições** (avg → última, P&L):                                                          (1)
- <TICKER> <qty>: <avg> → <last>, <±R$ X> (<±Y%>). <event if any: earnings/settlement/div> (1 per ticker)

**Hoje / T+N**: <linha única com settlement, dividendo, ou earnings em ≤ 7 dias>            (1-2)

**Top headlines**:                                                                         (1)
1. <topic> ([src](url)) — <1-frase: what + ação/watch>                                     (1)
2. <topic> ([src](url)) — <1-frase>                                                        (1)
3. <topic> ([src](url)) — <1-frase>                                                        (1)

**Geopolítica**:                                                                           (1)
- <Tema> ([src](url)): <status>. *Lucas*: <impacto carteira + ação concreta ou "monitor"> (1 per tema, 2-4 temas)

**Self-maintenance**: <linha única, omite se nada foi feito>                               (0-1)
**Pendências**: <linha única, omite se nada aberto>                                        (0-1)

**Resumo**:                                                                                (1)
- <market color 1 linha>                                                                   (1)
- <FX 1 linha>                                                                             (1)
- <BR 1 linha>                                                                             (1)
- <posições P&L 1 linha>                                                                   (1)
- <catalisador mais próximo com data>                                                      (1)
- <geopolítica se moveu mercado, senão omite>                                              (0-1)

Sources: <[1](url)> <[2](url)> <[3](url)> ... (inline, espaçados)                          (1)
```

Headlines and Geopolítica items are atomic: title + source + one terse sentence ending in "action/watch". No status/1ª/2ª/oportunidade sub-bullets — collapse into one sentence.

If counting hits 30 filled lines and there's still content, cut from the bottom up: drop Geopolítica themes that produce "neutro pra carteira", then drop the weakest headline, then collapse the Resumo to 4 bullets. Never cut Posições or core market numbers.
</briefing_markdown_layout>

<delivery_format>
The on-disk briefing and the Discord delivery are byte-identical — send the briefing's full markdown body via `mcp__plugin_discord_discord__reply`. The 30-line cap lives in the layout itself, not in a separate "summary for Discord" step. Lucas explicitly rejected (2026-05-14) both (a) the 5-8 line stripped summary AND (b) the long unconstrained dump — the answer is a tight briefing that's the same on disk and in Discord. Skip the send only if `quiet-mornings.flag` exists or `lucas-dm-chat-id.txt` is missing.
</delivery_format>

<delegated_skills>
- `Skill(b3-portal)`: only on explicit Lucas request to sync mid-morning. Never auto-trigger.
- `Skill(research)`: invoke for macro headlines that need triangulation across sources.
- `Skill(deep-analysis-before-recommendation)`: required before naming a specific buy/sell with sizing. Morning briefing surfaces ideas as pendências; the actual recommendation flow is deferred and Lucas-initiated.
- `Skill(investment-vehicle-analysis)`: same — deferred.
- Never invoke `Skill(discord:configure)` or `Skill(discord:access)` — denied for golden by design.
</delegated_skills>

<gotchas>
- USD/BRL `golden snapshot` reports intraday change only. If FX jumped between sessions (e.g., Real fell 2% Tuesday→Wednesday), yfinance's daily-change won't show that. Always compare absolute price vs the previous briefing and call out big moves.
- yfinance can show stale prior-session close as "current" on holidays. Check the timestamp on the Yahoo quote page.
- WebFetch sometimes returns 403/502/empty. Note "source unreachable" and try one cross-source. Never invent.
- Skill availability check: at tick start, confirm `morning-briefing` appears in the skill inventory. If not, the dotfiles symlink is broken — run the fallback field list from the cron prompt and add "skill missing" to pendências.
- Lucas reads in BRT (UTC-3). Phrase times BRT-friendly ("ontem 17h"), not US-tz, unless quoting a specific timestamp from a source.
</gotchas>

<output_contract>
At end of every tick, exactly two artifacts must exist:
1. `briefings/YYYY-MM-DD.md` — single canonical version of today's briefing.
2. A Discord reply via `mcp__plugin_discord_discord__reply` carrying the FULL briefing body, unless `quiet-mornings.flag` is set or the chat-id file is missing.

If either is missing, log a near-miss in `briefings/lessons-learned/YYYY-MM-DD-missed-tick.md` and update memory.
</output_contract>
