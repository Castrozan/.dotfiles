---
name: ponto
description: Fill time entries on Senior Gestão de Ponto. Use when user asks to fill ponto, clock-in entries, marcações, acertos de ponto, or time tracking on the Senior platform.
---

# Ponto — Senior Gestão de Ponto Automation

Automates filling daily time entries (marcações) on the Senior HCM platform. Navigates the cross-origin iframe, clicks "Inserir previstas" for each weekday, selects justificativa, and saves.

<schedule>
Lucas works Mon-Fri on escala 4741: 08:00–12:00 / 13:30–17:30. The four daily punches are 08:00, 12:00, 13:30, 17:30. Weekends (horário 9998/9999) are skipped.
</schedule>

<prerequisites>
- `pw` CLI available (Playwright browser automation from dotfiles)
- Browser launched in headed mode with Senior platform session active
- User must be logged into platform.senior.com.br (session persists in pw browser profile)
</prerequisites>

<workflow>
1. Open the Senior ponto page in headed mode via `pw open <url> --headed`
2. Wait for the iframe to load (look for "DIAS APURADOS" table)
3. Run the fill script targeting missing weekdays
4. Verify results via screenshot or the list script

The ponto page URL (bookmarked as Favoritos):
```
https://platform.senior.com.br/senior-x/#/Favoritos/0/res:%2F%2Fsenior.com.br%2Fmenu%2Frh%2Fponto%2Fgestaoponto%2Fcolaborador?category=frame&link=https:%2F%2Fweb02s1p.seniorcloud.com.br:30151%2Fgestaoponto-frontend%2Fuser%2Fredirect%3Factiveview%3Demployee%26portal%3Dg7&withCredentials=true
```
</workflow>

<scripts>
All scripts require the pw browser running on CDP port 9222. They connect via `playwright-core` using the Nix store path for the pw node_modules.

**ponto-list.js** — List all days and their current status (filled vs pending).
```bash
node scripts/ponto-list.js
```

**ponto-fill.js** — Fill time entries for specified dates or all pending weekdays.
```bash
node scripts/ponto-fill.js all        # Fill all pending weekdays
node scripts/ponto-fill.js 09/02      # Fill a specific date
```

Each day goes through: click "Inserir marcações" → click "Inserir previstas" → select "1 - Esquecimento de Batida" justificativa → click "Confirmar" → click "Salvar" → dismiss "Acerto retroativo" dialog → done.
</scripts>

<troubleshooting>
- If a day fails, retry individually with `ponto-fill.js DD/MM`
- If the "Inserir previstas" button is missing, a dialog overlay may be blocking — the script handles the "Acerto retroativo" confirmation automatically
- If the browser session expired, reopen the Senior platform URL in headed mode and log in manually
- The iframe is cross-origin so `pw elements`/`pw snap` won't see inside it — the scripts use Playwright frame detection by title ("Meus acertos de ponto")
</troubleshooting>

<playwright-core-path>
Scripts resolve playwright-core from the pw CLI's Nix store path. Read the `PW_NODE_MODULES` env var from the pw wrapper script to find it dynamically:
```bash
PW_MODULES=$(grep PW_NODE_MODULES "$(which pw)" | head -1 | cut -d'"' -f2)
```
</playwright-core-path>
