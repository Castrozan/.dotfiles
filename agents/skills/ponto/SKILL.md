---
name: ponto
description: Fill time entries on Senior Gestão de Ponto. Use when user asks to fill ponto, clock-in entries, marcações, acertos de ponto, or time tracking on the Senior platform.
---

<schedule>
Mon-Fri escala 4741: 08:00–12:00 / 13:30–17:30. Four daily punches: 08:00, 12:00, 13:30, 17:30. Weekends (horário 9998/9999) skipped.
</schedule>

<prerequisites>
Pinchtab running (browser automation on Chrome port 9222). Browser launched in headed mode with Senior platform session active. User must be logged into platform.senior.com.br (session persists in ~/.pinchtab/chrome-profile/).
</prerequisites>

<workflow>
1. Start pinchtab in headed mode: BRIDGE_HEADLESS=false pinchtab
2. Navigate to Senior ponto page via pinchtab API (bookmarked in Favoritos)
3. Wait for iframe to load (look for "DIAS APURADOS" table)
4. Run the fill script targeting missing weekdays
5. Verify results via the list script or screenshot
</workflow>

<scripts>
All scripts require pinchtab's Chrome on CDP port 9222. They connect via raw CDP WebSocket using cdp-browser.js (zero-dependency Node 22 built-in WebSocket).

ponto-list.js: List all days and their current status (filled vs pending).
ponto-fill.js all: Fill all pending weekdays.
ponto-fill.js DD/MM: Fill a specific date.

Each day: click "Inserir marcações" → "Inserir previstas" → select "1 - Esquecimento de Batida" → "Confirmar" → "Salvar" → dismiss "Acerto retroativo" dialog.
</scripts>

<troubleshooting>
Day fails: retry individually with ponto-fill.js DD/MM. "Inserir previstas" missing: dialog overlay blocking — script handles "Acerto retroativo" confirmation automatically. Session expired: reopen Senior platform URL in headed mode and log in manually. Iframe invisible to pinchtab snapshot: scripts use frame detection by title ("Meus acertos de ponto").
</troubleshooting>
