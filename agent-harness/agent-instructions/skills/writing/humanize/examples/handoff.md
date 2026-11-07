# Handoff to a person

**Reader:** a competent colleague who lacks your context and must not inherit a mystery.

**Budget:** 150 to 400 words for a shift; up to 800 for leave or a role change; 1 to 3 lines per item; system state in
2 to 3 sentences.

**Shape for a shift or incident:**

1. Who hands to whom, and when.
2. Active items: problem, impact, what you tried, the next step, and when to escalate.
3. Resolved items: cause, fix, follow-up ticket.
4. Noise: alerts that fired without cause, and what should change.
5. Recent deploys and what to watch.
6. How to reach you, and an explicit request to acknowledge.

**Shape for leave or a role change:** dates away and an emergency contact; recurring duties; each active project with
goal, next milestone, people, risks, and status; what the cover may decide and what they must escalate.

**Visuals that earn their place:** a table of active items (Item | State | Next action | Owner | Link) with status words
beside any emoji; timestamped bullets for an incident timeline. Diagrams rarely help.

**Avoid:** "everything was fine", troubleshooting transcripts, assumed context, items with no owner, a handoff sent only
by direct message. Post it where the team sees it and send the person a pointer.

## Example

```text
On-call handoff · 2026-11-07 18:00 UTC · @maria → @dev

🔴 Active: checkout 5xx at 2% (normal <0.1%) since 16:40.
   Tried: rolled back api v4.12, no change. Suspect payment gateway timeouts.
   Next: check the gateway dashboard; if still >1% at 19:00, page payments on-call.
   Thread: #inc-2291
✅ Resolved: disk full on log-3; rotated logs; OPS-551 tracks the retention fix.
🔕 Noisy: "queue-lag-warn" fired 6 times with lag <5 s; threshold too low (OPS-552).
🚀 Deploys: search v2.3 at 14:10; watch query p99 (baseline 180 ms).
Reachable by phone until 20:00. @dev please react 👍 when you have the pager.
```

For leave, a table keeps many projects scannable:

```markdown
| Project | State | Next milestone | You may decide | Escalate to |
|---|---|---|---|---|
| Billing v3 | 🟡 At risk | Load test, Nov 10 | Test scope | @ana |
| Search migration | 🟢 On track | Backfill done, Nov 14 | Batch sizes | @leo |
```

**Sources:** [Google SRE on-call](https://sre.google/workbook/on-call/),
[Google SRE incident response](https://sre.google/sre-book/incident-response/),
[Kaplan-Moss, transition files](https://jacobian.org/2022/nov/9/transition-files/).
