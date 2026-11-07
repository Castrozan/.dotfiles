# Status update to stakeholders

**Reader:** someone deciding whether to act, with five minutes for your update.

**Budget:** a summary of at most three sentences; 150 to 400 words in total.

**Shape:**

1. Overall status as a word (On track, At risk, Off track) and how far off.
2. The decision you need, from whom, by when.
3. Progress as outcomes, not activity.
4. Risks and what you are doing about them.
5. Next milestones with dates.

**Visuals that earn their place:** a workstream table with status words beside emoji; a milestone table; a chart only
for a trend the decision depends on.

**Avoid:** activity lists with no outcome, green on the outside and red on the inside, a decision request buried at the
end.

## Example

```markdown
**Search migration · week of 2026-11-02 · 🟡 At risk (1 week late)**

**Need from you:** decide by Nov 12 whether we drop fuzzy matching from launch
(saves 1 week) or move launch to Dec 8.

| Workstream | Status | Note |
|---|---|---|
| Indexing | 🟢 On track | Backfill 80% done |
| Query API | 🟡 At risk | Fuzzy matching 2× slower than target |
| UI | 🟢 On track | Behind a flag in staging |

**Next:** load test Nov 10. Launch target Dec 1.
```

**Sources:** [Larson, weekly updates](https://lethain.com/weekly-updates/),
[BLUF summary of Sehgal, HBR 2016](https://gist.github.com/skullvalanche/250f3dca2316ee77669fbe01f4c4ac2b).
