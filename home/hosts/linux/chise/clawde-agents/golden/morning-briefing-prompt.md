Heartbeat tick (cron 0 8 * * *, daily morning briefing window).

Invoke Skill(morning-briefing) and follow its instructions end-to-end. That skill defines the full routine: HEARTBEAT.md resume, self-maintenance sweep, market data collection, briefing layout, save-to-disk path, and the Discord DM contract.

Do not improvise around the skill — if the skill is missing from the inventory, that is a process failure, fall back to the briefing fields below and log "skill missing" in the briefing.

Fallback field list (only if Skill(morning-briefing) is unavailable):
  - US overnight close: S&P 500, NASDAQ Composite, Dow Jones Industrial Average. Current US futures.
  - FX: USD/BRL spot and overnight move.
  - Brazil: Bovespa (Ibovespa) close and futures.
  - portfolio.json: every active ticker's live quote + P&L + any scheduled earnings / dividend / settlement event.
  - Top 3 macro headlines.
  - Save to briefings/$(date +%Y-%m-%d).md.
  - DM 5-8 line summary via mcp__plugin_discord_discord__reply using chat_id from lucas-dm-chat-id.txt. Skip if quiet-mornings.flag exists or the chat-id file is missing.

Never poll Gmail/Calendar/Drive (denied). Never browse non-public sites.
