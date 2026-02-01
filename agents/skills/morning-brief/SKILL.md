# Morning Brief — Clawdbot Skill

> Deliver a personalized morning briefing every day. Weather, calendar, news, tasks, and anything the agent noticed overnight.

## When to Use
When the user wants a daily morning summary delivered to their messaging channel (WhatsApp, Telegram, Signal, etc.) at a set time.

## Setup

### 1. Configure the Cron Job
Add a cron job that fires at the user's preferred wake time:

```
/cron add "morning-brief" "0 7 * * *" "Run the Morning Brief skill"
```

Or via the cron tool:
```json
{
  "action": "add",
  "job": {
    "label": "morning-brief",
    "schedule": "0 7 * * *",
    "text": "Run the Morning Brief skill. Read skills/morning-brief/SKILL.md and follow it.",
    "enabled": true
  }
}
```

### 2. User Preferences (Optional)
Create `skills/morning-brief/preferences.md` to customize sections:

```markdown
# Morning Brief Preferences

## Sections (in order)
1. weather - Location: Criciúma, SC, Brazil
2. calendar - Source: Google Calendar (if available)
3. news - Topics: AI, NixOS, developer tools, crypto
4. tasks - Source: MEMORY.md todos, HEARTBEAT.md pending items
5. overnight - What the agent did while user slept
6. markets - Crypto prices, Polymarket highlights (if enabled)

## Delivery
- Channel: whatsapp
- Format: concise, emoji headers, no fluff
- Max length: ~500 words
- Language: English (unless user prefers otherwise)

## News Sources
- Hacker News front page
- X/Twitter trending in tech
- Web search for user's topics
```

## Execution Flow

When triggered (by cron or manually):

### Step 1: Gather Data
Run these in parallel where possible:

1. **Weather**: Web search `"weather [location] today"` or fetch from weather API
2. **Calendar**: Check Google Calendar MCP or browser automation (if configured)
3. **News**: 
   - Fetch Hacker News front page (`https://news.ycombinator.com`)
   - Web search for user's interest topics
   - Check X/Twitter trending (browser, if available)
4. **Tasks**: Read `MEMORY.md` for pending todos, `HEARTBEAT.md` for active tasks
5. **Overnight Work**: Read `memory/YYYY-MM-DD.md` for what happened while user slept
6. **Markets** (optional): Fetch crypto prices, Polymarket highlights

### Step 2: Compose Brief
Format as a clean, scannable message:

```
☀️ Good morning! Here's your brief for [Day, Month DD]:

🌤️ WEATHER
[City]: [temp]°C, [conditions]. High [X]° / Low [Y]°

📅 CALENDAR
• [Event 1] at [time]
• [Event 2] at [time]
(or: No events today)

📰 HEADLINES
• [Top HN story] — [1-line summary]
• [Relevant news item] — [1-line summary]  
• [AI/tech news] — [1-line summary]

✅ TASKS & TODOS
• [Pending item from memory]
• [Pending item from heartbeat]

🌙 OVERNIGHT
[2-3 line summary of what the agent accomplished]

💰 MARKETS (optional)
BTC: $[price] ([change]%) | ETH: $[price] ([change]%)
```

### Step 3: Deliver
Send via the message tool to the configured channel:

```json
{
  "action": "send",
  "channel": "whatsapp",
  "target": "[user's number]",
  "message": "[composed brief]"
}
```

## Customization

### Adding Sections
Users can add custom sections by editing `preferences.md`. Each section needs:
- **Name**: identifier
- **Source**: where to get data (web search, file, API, browser)
- **Format**: how to display it (bullet list, single line, paragraph)

### Removing Sections
Comment out or delete from `preferences.md`. The skill only runs sections that are listed.

### Frequency
Default is daily, but can be set to:
- Weekdays only: `"0 7 * * 1-5"`
- Twice daily: morning + evening recap
- On-demand: user says "give me a brief"

## Dependencies
- `web_search` or `web_fetch` — for weather and news
- `message` — for delivery
- `memory_get` / file read — for tasks and overnight summary
- Browser (optional) — for calendar, X/Twitter, richer data

## Error Handling
- If a section fails (e.g., web search unavailable), skip it with a note: "📰 News unavailable today"
- Always deliver something — even a minimal brief is better than nothing
- If the channel is unreachable, log the brief to `memory/YYYY-MM-DD.md` as "undelivered brief"

## Example Output

> ☀️ Good morning! Here's your brief for Thursday, Jan 30:
> 
> 🌤️ WEATHER
> Criciúma: 24°C, partly cloudy. High 29° / Low 19°
> 
> 📰 HEADLINES
> • Microsoft forced me to switch to Linux — massive HN thread (1700pts)
> • Rust at scale: WhatsApp using Rust for security — Meta eng blog
> • Kimi K2.5 beats Opus 4.5 on coding benchmarks — free this week
> 
> ✅ PENDING
> • Run `nixos-rebuild switch` — deploys agenix secrets + workspace 11
> • Review 2 X thread drafts in projects/money/
> • Set up BRAVE_API_KEY for web search
> 
> 🌙 OVERNIGHT
> Processed all 325 ReadItLater items. Built 2 Clawdbot skills (night-shift, readitlater-processor). Drafted 2 X threads. Researched Polymarket API + money strategies. Set up qmd for local markdown search.
> 
> Have a great day! 🚀
