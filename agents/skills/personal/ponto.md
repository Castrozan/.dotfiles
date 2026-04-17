Senior Gestao de Ponto - time entry automation via Chrome DevTools MCP.

<schedule>
Mon-Fri escala 4741: 08:00-12:00 / 13:30-17:30. Four daily punches: 08:00, 12:00, 13:30, 17:30. Weekends (horario 9999/9996) are skipped.
</schedule>

<prerequisites>
The Senior ponto page must be open in Chrome Global. The page URL contains `platform.senior.com.br` and the iframe title is "Meus acertos de ponto - Gestao do Ponto". Use `mcp__chrome-devtools__list_pages` to find it and `mcp__chrome-devtools__select_page` to select it. User must be logged in (session persists across browser restarts).
</prerequisites>

<listing-days>
After selecting the ponto page, take a snapshot. The table under "DIAS APURADOS" lists all days. Each row has: date, escala, horario code, marcacoes status, and situacoes.

Weekdays needing filling have horario `4707` and a link with text "Inserir marcacoes".
Weekends have horario `9999` (domingo) or `9996` (sabado) - skip these.
Days already filled show punch times (e.g. "08:00 12:00 13:30 17:30") instead of "Inserir marcacoes".
</listing-days>

<filling-a-single-day>
For each pending weekday, execute this sequence. Wait 2-3 seconds between each step for the UI to settle. Take a fresh snapshot after each click to get updated UIDs.

1. Click the "Inserir marcacoes" link for the target day
2. Wait for the entry dialog to load. Look for the "Inserir previstas" button in the new snapshot
3. Click "Inserir previstas" - this auto-fills the four punch times from the escala
4. A justificativa dropdown appears. Click the dropdown (look for a p-dropdown or combobox element)
5. Select "1 - Esquecimento de Batida" from the dropdown options
6. Click "Confirmar" to apply the justificativa
7. Click "Salvar" to save the entry
8. An "Acerto retroativo" confirmation dialog may appear. If it does, click "Sim" to dismiss it
9. Wait for the page to return to the table view before proceeding to the next day
</filling-a-single-day>

<batch-fill>
To fill all pending weekdays:
1. Take a snapshot and identify all rows with horario 4707 + "Inserir marcacoes"
2. Process days one at a time, oldest first (bottom of table to top)
3. After each day, take a fresh snapshot to confirm success and get updated UIDs
4. Track successes and failures. Retry failed days once individually
5. Report results: which days filled, which failed
</batch-fill>

<troubleshooting>
- "Inserir previstas" not visible: a dialog overlay may be blocking. Look for any modal or ngdialog and dismiss it first
- Dropdown not responding: try clicking the dropdown trigger element, then wait 2s before looking for options
- Session expired: tell user to log in at platform.senior.com.br manually, then retry
- Page shows loading spinner: wait_for the table header text "DIAS APURADOS" before proceeding
</troubleshooting>
