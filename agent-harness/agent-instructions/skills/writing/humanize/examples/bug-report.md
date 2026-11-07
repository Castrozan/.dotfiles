# Bug report

**Reader:** a maintainer who must reproduce the problem without asking you anything.

**Budget:** summary of about 10 words, under 60 characters, describing the symptom rather than your fix; steps short
enough to follow without scrolling.

**Shape:**

1. Summary of the symptom.
2. Numbered steps to reproduce, and how often it happens.
3. Expected result.
4. Actual result, with the exact error text.
5. Versions and environment.
6. Logs in `<details>`.
7. Your guess at the cause, marked as a guess.

**Avoid:** "it crashes", "doesn't work", a screenshot of an error you could paste as text, a fix proposal in place of
the symptom.

## Example

Bad summary: "Software crashes". Good summary: "Cancelling a file copy dialog crashes File Manager".

````markdown
### Export to CSV drops rows after 10,000 when a filter is active

1. Open Reports → Orders and filter `status = shipped` (about 14,000 rows).
2. Click Export → CSV.

**Expected:** all 14,212 filtered rows. **Actual:** exactly 10,000 rows, no error.
Always reproducible; without a filter every row exports.

**Version:** web 5.8.1, Firefox 132, macOS 15.1

<details><summary>Export response headers</summary>

```text
HTTP 200, X-Row-Count: 10000, X-Truncated: true
```

</details>

Guess: the filtered path uses the paged query's default page size.
````

**Sources:** [Tatham, how to report bugs](https://www.chiark.greenend.org.uk/~sgtatham/bugs.html),
[Mozilla bug writing](https://bugzilla.mozilla.org/page.cgi?id=bug-writing.html).
