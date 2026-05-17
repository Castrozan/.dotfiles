---
name: b3-portal
description: Log into and scrape data from Lucas's B3 Área do Investidor (investidor.b3.com.br) via browser-use MCP plus raw CDP XHR capture. Use when syncing portfolio positions, trades, dividends, or any other read-only data from B3 — for example when Golden runs b3-sync, or when verifying brokerage state. Documents the working flow, the SPA quirks that broke prior attempts, the API endpoint catalog, and the institution-CNPJ filter trick.
---

<scope>
Authoritative recipe for pulling data from B3's `investidor.b3.com.br` portal. The portal is an Angular SPA backed by Microsoft Azure AD B2C for auth. There is no public read API, so we drive a real browser and listen to its XHRs over CDP. This skill documents:

- the login dance (cookie banner gating, B2C OAuth flow, no-2FA happy path)
- the working browser tooling (`browser-use` MCP, NOT `chrome-devtools` MCP — see "Why not chrome-devtools" below)
- the raw-CDP XHR listener that runs alongside browser-use
- the API endpoint catalog (institutions, trades, dividends, IR informes)
- the per-institution filter trick (clicking an institution chip dispatches `?documentoInstituicao=<CNPJ>` to the same endpoint)
- the gotchas that wasted hours the first time around
</scope>

<when_to_invoke>
Invoke this skill when any of these come up:

- "Sync Lucas's positions from B3"
- "Pull dividends history from B3"
- "Find Lucas's trades over the last N days at NU"
- "What does B3 show for Lucas's patrimônio?"
- "The `golden b3-sync` CLI is broken, get the data anyway"
- Lucas pastes B3 credentials and asks Golden to log in

Do NOT invoke for: brokerage-app screenshots, third-party financial data, public market data (yfinance / Investing.com), Tesouro Direto direct portal (different system).
</when_to_invoke>

<credentials_policy>
Lucas's CPF + B3 password live in `.env` in the golden workspace (`/home/zanoni/.claude-discord-agents/golden/.env`) as `B3_CPF` and `B3_PASSWORD`. The `.env` is `chmod 600` and gitignored.

Never echo credentials into Discord, briefings, memory files, or any other persistent doc. If Lucas pastes credentials in Discord, tell him to delete the message and write them to `.env` instead. The persona explicitly allows handling these credentials — the older "refuse on principle" rule was deprecated 2026-05-12 when browser-use was unblocked at the tool layer.

B3 does NOT require 2FA for Lucas's account today (2026-05-12). The B2C login accepts CPF+password and returns OAuth code+id_token directly to `https://www.investidor.b3.com.br?code=...&id_token=...`.
</credentials_policy>

<login_flow>
1. **Reach the login page**: navigate browser-use to `https://www.investidor.b3.com.br/login`.
2. **Cookie banner blocks everything**: there is a OneTrust banner with buttons `REJEITAR TODOS OS COOKIES` and `ACEITAR TODOS OS COOKIES`. The Angular `Entrar` button is `disabled="true"` until cookies are dismissed. Click `ACEITAR TODOS OS COOKIES` (id `onetrust-accept-btn-handler`). Rejecting also works but persists across reloads, so re-accept after a session restart.
3. **CPF input**: find the input with placeholder `Digite seu CPF ou CNPJ`. Use `browser_type` with the CPF (digits only, no formatting).
4. **Click Entrar**: redirects to `https://b3investidor.b2clogin.com/b3Investidor.onmicrosoft.com/oauth2/v2.0/authorize?p=B2C_1A_SIGN_IN&...&doc_hint=<CPF>` (Azure AD B2C).
5. **Password input**: type the password into the empty input on the B2C page, click the `ENTRAR` button.
6. **OAuth callback**: redirects back to `https://www.investidor.b3.com.br/?state=...&code=...&id_token=...`, then the SPA processes the code and you land on `https://www.investidor.b3.com.br/` authenticated.

You can confirm authentication by checking that `browser_get_state` shows the side-nav buttons (`Início`, `Extratos`, `Proventos`, `Relatórios`, `Portabilidade`) and at least one institution filter chip (e.g. `NU`).

**Session persistence**: browser-use launches Chrome with a tmp `--user-data-dir=/tmp/browser-use-user-data-dir-*`, so cookies do NOT survive across browser-use sessions. Each new run requires re-login.
</login_flow>

<chrome_topology>
Two Chrome instances may exist on Lucas's machine:

1. **chrome-global** at `~/.config/chrome-global` profile, port 9222. This is the dotfiles-managed personal Chrome (`hypr-summon-chrome-global` launcher). Shared with `chrome-devtools` MCP server (auto-connects). NOT what browser-use uses.

2. **browser-use's own Chrome** at `/tmp/browser-use-user-data-dir-<random>` profile, random CDP port (different each spawn — e.g. 48811, 52785). browser-use launches and tears it down per session. **This is the Chrome with B3 cookies after login.**

When you write a CDP listener to capture XHRs, point it at browser-use's port, NOT 9222. Discovery: `pgrep -af browser-use-user-data-dir | grep -oP 'remote-debugging-port=\d+' | head -1`.

The bundled `scripts/b3_capture_listener.py` does this auto-discovery.
</chrome_topology>

<why_not_chrome_devtools>
The `chrome-devtools` MCP server is configured to auto-connect to the chrome-global profile. If you try to drive an authenticated B3 session through it:

- It will either fail with "Cannot connect to Chrome" (when chrome-global isn't running), OR
- It will attach to the unauthenticated chrome-global tab and produce nonsense results.

`browser-use` is the right tool because it launches its own isolated Chrome with a fresh profile, and its full-stack input simulation handles Angular's strict click-event guards (which CDP `Input.dispatchMouseEvent` does NOT — see "Gotchas").
</why_not_chrome_devtools>

<xhr_capture_pattern>
B3's SPA fires XHR/Fetch requests on every page navigation and most interactions. We capture them via raw CDP `Network.enable` on a parallel WebSocket while browser-use drives the browser.

The bundled `scripts/b3_capture_listener.py` does this. Run it in the background BEFORE driving the browser:

```bash
cd /home/zanoni/.claude-discord-agents/golden
nohup uv run python <skill_dir>/scripts/b3_capture_listener.py > /tmp/b3-listener.log 2>&1 &
disown
```

It writes one JSON file per captured XHR into `data/raw/b3/<today>/explore/<HHMMSS>_<seq>_<url-segment>.json` and appends a `summary.txt`. SIGINT stops it cleanly.

Then drive the browser via browser-use MCP. After each click/navigation, give the listener 3-4 seconds to drain.
</xhr_capture_pattern>

<endpoint_catalog>
Two API host prefixes under `investidor.b3.com.br`:
- `/negocio-<area>/api/<area>/<version>/<route>` — main pattern
- `/api/<area>/<version>/<route>` — auxiliary (transferencia-ativos)

**Position / patrimônio**:
- `GET /negocio-home/api/home/v1/minha-carteira/instituicao` — patrimônio total + institutions list + category breakdown (RF/RV)
- `GET /negocio-home/api/home/v1/minha-carteira/instituicao?documentoInstituicao=<CNPJ>` — **per-institution detail** (the institution-filter trick)
- `GET /negocio-home/api/home/v2/total-acumulado?dc=YYYY-MM-DDT00:00:00` — patrimônio scalar
- `GET /negocio-home/api/home/v1/minha-carteira/resumo` — 30d delta + insight
- `GET /negocio-home/api/home/v2/evolucao-patrimonial?ap=N&dc=...` — historical patrimônio
- `GET /negocio-home/api/home/v1/minha-carteira/instituicao` (no param) — across all institutions

**Cash flow / trades**:
- `GET /negocio-movimentacao/api/extrato-movimentacao/v2/movimentacao?dataInicio=YYYY-MM-DD&dataFim=YYYY-MM-DD&pagina=N` — paginated cash events
- `GET /negocio-movimentacao/api/extrato-movimentacao/v2/movimentacao/ultimas` — recent
- `GET /negocio-negociacaoativos/api/extrato-negociacao-ativos/v1/negociacao-ativos/1?dataInicio=...&dataFim=...` — executed trades
- `GET /negocio-home/api/home/v2/negociacao/ultimas-negociacoes?dataFim=YYYY-MM-DD` — last few trades

**Dividends / proventos**:
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/recebidos?dti=YYYY-MM-DD&dtf=YYYY-MM-DD` — received provents
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v2/receber?data=YYYY-MM-DD` — upcoming provents (with `previsaoPagamento`)
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/resumo-mensal/recebidos?dc=...` — monthly aggregate
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/recebidos/resumo-proventos` — `totalAno` and `totalUltimosDozeMeses`
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/proventos/investidor/anos` — years with provents

**IR / reports**:
- `GET /negocio-informerendimentos/api/informes/v1/informe-rendimentos` — IR yearly statement (returns `[]` if none generated)
- `/relatorios/mensal-consolidado` page has PDF/Excel download buttons (file URL likely `/api/relatorios/...` — not captured yet)

**Misc**:
- `GET /negocio-investidor/api/investidor/v1.3/cadastro` — investor data
- `GET /negocio-investidor/api/investidor/v1/perfil` — profile
- `GET /api/transferencia-ativos/v2/solicitacoes/pendentes` — portability
- `GET /negocio-ofertaspublicas/api/extrato-ofertas-publicas/v1/ofertas-publicas/1` — IPOs

All endpoints take a `cache-guid=<uuid>` query parameter that the SPA generates per session.

**The Nubank CTVM CNPJ for the institution filter is `62169875000179`.** Other institutions Lucas had visible on 2026-05-12: Cclaa Sicoob (`81367880000130`), CEF (`00360305000104`), Inter (`18945670000146`), Inter alt CNPJ (`00416968000101`).

Persistent endpoint patterns are committed to `/home/zanoni/.claude-discord-agents/golden/golden_cli/b3_endpoints.py`.
</endpoint_catalog>

<gotchas>
**Angular click guards ignore synthetic clicks.** The page's `Entrar` button reads `disabled=""` from the Angular component's `Input`, not the DOM attribute. Calling `el.click()` or even CDP `Input.dispatchMouseEvent` does NOT enable it. `browser-use`'s input pipeline replays through the real browser event loop, which works. Don't waste time trying to fake clicks via raw CDP — drive via browser-use.

**Cookie banner gating.** `Entrar` is permanently disabled until cookies are dismissed. Reject *or* accept works, but rejection persists across page reloads.

**Pure raw-CDP login probably fails.** Even with the right approach, the SPA's anti-automation heuristics may refuse to dispatch the login flow. browser-use's stealth Chrome is what gets past.

**404 on `/extrato/posicoes` and `/extrato/eventos`.** Those routes are stale. The current "Posições" view is the SPA root (`/`), and "Eventos" is `/extrato/eventos` is a tab within Extratos page but accessed via the side-tab click (not direct URL).

**`golden b3-sync --capture` is broken** as of 2026-05-12. Attaches WebSocket correctly but captures 0 XHRs. Root cause not investigated. Workaround: use the bundled `b3_capture_listener.py` instead. TODO: debug `b3_cdp_client.py:_pump_incoming_messages` and the response-body race condition.

**RDB de emissor Nubank-interno não aparece na B3.** The R$ 25k of Nubank Caixinhas (RDB Nubank-issued) is invisible to B3 custódia. Only equity, FII, BDR, ETF, externally-custodiada renda fixa show up. Don't treat B3 patrimônio as total Nubank patrimônio.

**Settlement lag.** Trades executed on day D appear in "ultimas-negociacoes" immediately but don't enter "total-acumulado" patrimônio until D+2 settlement. The settlement cash sits in `RV` category as "cash on B3" during the lag.
</gotchas>

<standard_workflow>
For "sync Nubank-only positions from B3":

1. Verify `.env` has `B3_CPF` and `B3_PASSWORD`. If missing, ask Lucas (and tell him to paste in DM not channel).
2. Start the listener: `nohup uv run python ~/.local/share/claude-skill-sets/personal/.claude/skills/b3-portal/scripts/b3_capture_listener.py > /tmp/b3-listener.log 2>&1 & disown`.
3. Drive login via `browser-use`:
   - `browser_navigate https://www.investidor.b3.com.br/login`
   - `browser_get_state` → find cookie accept button index → `browser_click`
   - find CPF input index → `browser_type <CPF>`
   - find Entrar button index → `browser_click`
   - wait, then `browser_get_state` → on B2C page, find password input index → `browser_type <password>`
   - find ENTRAR button → `browser_click`
   - wait 5s, confirm URL is back at investidor.b3.com.br with the dashboard.
4. Click the `NU` institution filter chip → captures `minha-carteira/instituicao?documentoInstituicao=62169875000179` → has NU's RF/RV breakdown.
5. Navigate to `/extrato/movimentacao` and `/extrato/negociacao` for cash flow and trades.
6. Navigate to `/proventos/visao-geral` and click through the 5 tabs (Visão geral, Recebidos, A Receber, Radar, Calendário) for full dividend history.
7. Stop the listener with `kill <pid>`.
8. Inspect the captured JSON files in `data/raw/b3/<today>/explore/` and filter to NU-only by `nomeInstituicao == "NU INVESTIMENTOS S.A. - CTVM"` or `documentoInstituicao == "62169875000179"`.

For just verifying Lucas's NU patrimônio total: the single call `GET /negocio-home/api/home/v1/minha-carteira/instituicao?documentoInstituicao=62169875000179` with the session cookies suffices. If a future b3-sync writes that endpoint directly, it can skip the navigation entirely after login.
</standard_workflow>

<remember>
- Always work in the golden workspace (`/home/zanoni/.claude-discord-agents/golden/`).
- Always use uv (`uv run python ...`), never `pip` or `python3` directly.
- The listener writes to `data/raw/b3/<today>/explore/` (gitignored).
- Raw JSON dumps are the source of truth; parse them with `uv run python -c '...'` rather than re-fetching.
- After scraping, decide whether anything materially changed before updating `portfolio.json` — most days B3 just confirms what Lucas already told Golden.
</remember>
