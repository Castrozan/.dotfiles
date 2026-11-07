# Chat message to a person

**Reader:** a busy person who sees a notification preview, maybe hours later and in another time zone.

**Budget:** the ask or conclusion fits the first line, which is all a notification preview shows; at most 60 words for
a question and 150 for an update. Anything longer goes in a document, with a one-line summary and the link in chat.

**Shape:**

1. The ask or conclusion, addressed to a person, with a deadline when there is one.
2. One or two lines of context the reader needs to answer.
3. What happens if they say no, or by when you need the answer.

**Rules:** no bare "hi" or "quick question?"; one message, not five; follow-ups in the thread; a public channel over a
direct message when others benefit; an @mention only for a specific request; react with an emoji instead of sending
"ok".

**Visuals that earn their place:** a code block for a command or error; one cropped screenshot for a UI problem;
emoji paired with words. Chat apps do not render Mermaid or reliable tables, so attach a diagram as an image with a
one-line caption.

## Example

Bad, as three separate messages:

> hey
> you around?
> quick q about the deploy

Good, as one:

```text
@lena can you approve the prod deploy for billing v3.2 by 15:00 UTC today?
Staging passed (run #4411). Only change: the invoice rounding fix from PR #902.
If you'd rather wait until Monday, say so and I'll reschedule.
```

An update leads with the outcome:

```text
Search backfill finished at 11:20: 4.2 M documents, 0 errors. Query p99 is 170 ms (target 200).
Next: switch reads on Monday 10:00 unless someone objects in this thread.
```

**Sources:** [nohello](https://nohello.net/en/), [dontasktoask](https://dontasktoask.com/).
