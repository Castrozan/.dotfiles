# wa-poll-state.json

Location: `/home/zanoni/clawd/scripts/wa-poll-state.json`

## Structure
```json
{
  "groups": {
    "aplicacoes-bethais": {
      "name": "aplicações bethais",
      "lastActivity": "2026-01-30T12:21:00-03:00",
      "consecutiveEmpty": 8,
      "currentIntervalMin": 60,
      "lastPollTime": "2026-01-30T18:49:45.958500-03:00",
      "mode": "passive"
    },
    "rinha-de-ia": {
      "name": "Rinha de IA",
      "lastActivity": "2026-01-30T12:23:00-03:00",
      "consecutiveEmpty": 8,
      "currentIntervalMin": 60,
      "lastPollTime": "2026-01-30T18:49:45.958500-03:00",
      "mode": "ai-battle"
    }
  },
  "backoffSchedule": [2, 2, 5, 5, 10, 10, 15, 30, 60],
  "note": "Interval increases per consecutiveEmpty index. Resets on activity."
}
```

## Update Rules
- **Activity found**: reset `consecutiveEmpty = 0`, set `currentIntervalMin = 2`.
- **No activity**: increment `consecutiveEmpty`, set `currentIntervalMin = backoffSchedule[min(consecutiveEmpty, len-1)]`.
- **Always** update `lastPollTime`.
