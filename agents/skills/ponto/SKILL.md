---
name: ponto
description: Fill time entries on Senior Gestão de Ponto. Use when user asks to fill ponto, clock-in entries, marcações, acertos de ponto, or time tracking on the Senior platform.
---

<schedule>
Mon-Fri escala 4741: 08:00–12:00 / 13:30–17:30. Four daily punches: 08:00, 12:00, 13:30, 17:30. Weekends (horário 9998/9999) skipped.
</schedule>

<prerequisites>
Pinchtab in headed mode (use `pinchtab-switch-mode headed` — see browser skill for details). User must be logged into platform.senior.com.br (session persists across mode switches).
</prerequisites>

<workflow>
1. Switch to headed mode via `pinchtab-switch-mode headed`
2. Navigate to Senior ponto page via pinchtab API (bookmarked in Favoritos)
3. Wait for iframe to load (look for "DIAS APURADOS" table)
4. Run the fill script targeting missing weekdays
5. Verify results via the list script or screenshot
</workflow>

<scripts>
Scripts connect to pinchtab's Chrome via raw CDP WebSocket using cdp-browser.js (zero-dependency Node 22 built-in WebSocket).

ponto-list.js: List all days and their current status (filled vs pending).
ponto-fill.js all: Fill all pending weekdays.
ponto-fill.js DD/MM: Fill a specific date.

Each day: click "Inserir marcações" → "Inserir previstas" → select "1 - Esquecimento de Batida" → "Confirmar" → "Salvar" → dismiss "Acerto retroativo" dialog.
</scripts>

<troubleshooting>
Day fails: retry individually with ponto-fill.js DD/MM. "Inserir previstas" missing: dialog overlay blocking — script handles "Acerto retroativo" confirmation automatically. Session expired: reopen Senior platform URL in headed mode and log in manually. Iframe invisible to pinchtab snapshot: scripts use frame detection by title ("Meus acertos de ponto").
</troubleshooting>
