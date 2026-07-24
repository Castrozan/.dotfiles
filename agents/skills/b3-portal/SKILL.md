---
name: b3-portal
description: Log into and scrape data from Lucas's B3 Área do Investidor (investidor.b3.com.br) via the PinchTab browser-automation CLI plus raw CDP XHR capture. Use when syncing portfolio positions, trades, dividends, or any other read-only data from B3; for example when Golden runs b3-sync, or when verifying brokerage state. Documents the working flow, the SPA quirks that broke prior attempts, the API endpoint catalog, and the institution-CNPJ filter trick.
---

<managed_scope>
GOLDEN MANAGES ONLY THE NUBANK SLEEVE (NuInvest + Nubank Caixinhas). Hard scope boundary set by Lucas on 2026-05-30.

B3 aggregates EVERY institution Lucas has custody at. On 2026-05-12 that included Sicoob (~R$ 36k), Caixa/CEF (~R$ 34k),
and Inter (~R$ 7k) in renda fixa. That money is Lucas's but it is OUT OF SCOPE. Do NOT:
- pull non-Nubank institutions into portfolio.json,
- propose managing / rebalancing / diversifying them,
- treat B3's total patrimônio as the number Golden manages or sizes against,
- offer to "expand scope" to all institutions.

When syncing, filter to Nubank only: `documentoInstituicao=62169875000179` (NU CTVM). Ignore every other institution
chip. Note the Nubank Caixinhas RDB does NOT appear in B3 at all (see gotchas), so even within the Nubank sleeve, B3
only shows the BDR/ETF/FII/externally-custodiada-RF part; combine it with what Lucas reports for the Caixinhas.

Why this rule exists: on 2026-05-30 Golden saw the ~R$ 77k of non-Nubank renda fixa in a B3 capture and over-reacted,
proposing to track all institutions and run a full multi-institution sync. Lucas corrected: "We only manage nubank." Do
not repeat that overreaction.
</managed_scope>

<scope>
Authoritative recipe for pulling data from B3's `investidor.b3.com.br` portal. The portal is an Angular SPA backed by
Microsoft Azure AD B2C for auth. There is no public read API, so we drive a real browser and listen to its XHRs over
CDP. This skill documents:

- the login dance (cookie banner gating, B2C OAuth flow, no-2FA happy path)
- the working browser tooling (the `pinchtab` CLI, NOT `chrome-devtools` MCP; see "Why not chrome-devtools" below)
- the raw-CDP XHR listener that runs alongside PinchTab
- the API endpoint catalog (institutions, trades, dividends, IR informes)
- the per-institution filter trick (clicking an institution chip dispatches `?documentoInstituicao=<CNPJ>` to the same
  endpoint)
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

Do NOT invoke for: brokerage-app screenshots, third-party financial data, public market data (yfinance / Investing.com),
Tesouro Direto direct portal (different system).
</when_to_invoke>

<credentials_policy>
Lucas's CPF + B3 password live in `.env` in the golden workspace (`/home/zanoni/.claude-discord-agents/golden/.env`) as
`B3_CPF` and `B3_PASSWORD`. The `.env` is `chmod 600` and gitignored.

Never echo credentials into Discord, briefings, memory files, or any other persistent doc. If Lucas pastes credentials
in Discord, tell him to delete the message and write them to `.env` instead. The persona explicitly allows handling
these credentials: the older "refuse on principle" rule was deprecated 2026-05-12 when the B3 login flow was unblocked
at the tool layer.

B3 does NOT require 2FA for Lucas's account today (2026-05-12). The B2C login accepts CPF+password and returns OAuth
code+id_token directly to `https://www.investidor.b3.com.br?code=...&id_token=...`.
</credentials_policy>

<pinchtab_bootstrap>
One-time setup on golden before the first B3 run. Navigation is globally unrestricted: the browser skill's
`enforce_pinchtab_config.py` reasserts wildcard `security.allowedDomains` and IDPI-off into `~/.pinchtab/config.json` on
every rebuild, so there is no per-host allowlist step and no `Error 403 ... Domain not in allowlist` to clear. Do not
narrow `allowedDomains` to the B3 hosts, the next rebuild reverts it to `["*"]` and the wildcard already covers them.

1. **Dedicated profile + headed login**: use a B3-only profile so the authenticated session is isolated and reused
   safely rather than sharing the `default` profile: `export PINCHTAB_SESSION=$(pinchtab session create --agent-id
   golden-b3)`, then start the server for the interactive first login (headed is the enforced default; `pinchtab server
   -H` forces it explicitly). On golden the profile lives under `/home/zanoni/.pinchtab/profiles/<profile>`.

After this, subsequent runs reuse the authenticated persistent profile with no re-login until B2C token expiry. To apply
a later config edit to an already-running server, `pinchtab server restart`.
</pinchtab_bootstrap>

<login_flow>
1. **Reach the login page**: `pinchtab nav https://www.investidor.b3.com.br/login --snap`. Navigation is unrestricted
   (wildcard allowlist, IDPI off), so no allowlist prep is needed.
2. **Cookie banner blocks everything**: a OneTrust banner (`REJEITAR TODOS OS COOKIES` / `ACEITAR TODOS OS COOKIES`)
   keeps the Angular `Entrar` button `disabled="true"` until dismissed. Accept it by clicking
   `#onetrust-accept-btn-handler` (from `pinchtab snap`, click the ref, or `pinchtab click
   '#onetrust-accept-btn-handler'`). Rejecting also works but persists across reloads, so re-accept after a profile
   reset.
3. **CPF input**: `pinchtab type` the CPF (digits only, no formatting) into the input with placeholder `Digite seu CPF
   ou CNPJ`. Use `type` (real keystrokes), NEVER `fill` (value injection leaves the Angular form control unaware and
   Entrar stays disabled, see `<gotchas>`).
4. **Click Entrar**: `pinchtab click` the `Entrar` button in default mode (trusted `Input.dispatchMouseEvent`); never
   `--mode dom` or `--mode dispatch`. Redirects to
   `https://b3investidor.b2clogin.com/b3Investidor.onmicrosoft.com/oauth2/v2.0/authorize?p=B2C_1A_SIGN_IN&...&doc_hint=<CPF>`
   (Azure AD B2C).
5. **Password input**: `pinchtab type` the password into the empty input on the B2C page, then `pinchtab click` the
   `ENTRAR` button.
6. **OAuth callback**: redirects back to `https://www.investidor.b3.com.br/?state=...&code=...&id_token=...`; the SPA
   processes the code and lands authenticated on `https://www.investidor.b3.com.br/`.

Confirm authentication with `pinchtab url` (back at investidor.b3.com.br) and `pinchtab snap` showing the side-nav
(`Início`, `Extratos`, `Proventos`, `Relatórios`, `Portabilidade`) and at least one institution chip (e.g. `NU`).

**Session persistence**: PinchTab drives a persistent on-disk profile, so a one-time headed login persists the B3
session across runs until normal B2C cookie/token expiry, unlike browser-use's old throwaway profile that forced a
re-login every run.
</login_flow>

<chrome_topology>
Two Chrome instances may exist on golden's machine:

1. **chrome-global** at `~/.config/chrome-global` profile, port 9222. The dotfiles-managed personal Chrome
   (`hypr-summon-chrome-global` launcher), shared with the `chrome-devtools` MCP. NOT what we use for B3.

2. **PinchTab's own Chrome** at `~/.pinchtab/profiles/<profile>`, exposing a real CDP remote-debugging port (default
   `9869`; the PinchTab server is `9867` and its first instance's HTTP API is `9868`, neither of which is CDP). This is
   the Chrome carrying the B3 session after login, and the only Chrome exposing a debug port (chrome-global runs bare
   without one).

Point the CDP XHR listener at PinchTab's port. Discovery on Linux: `pgrep -af 'pinchtab/profiles' | grep -oP
'remote-debugging-port=\K\d+' | head -1`. The bundled `scripts/b3_capture_listener.py` does this auto-discovery (falls
back to 9869).
</chrome_topology>

<why_not_chrome_devtools>
The `chrome-devtools` MCP auto-connects to the chrome-global profile. Driving an authenticated B3 session through it
fails: either "Cannot connect to Chrome" (chrome-global not running), or it attaches to the unauthenticated
chrome-global tab and returns nonsense.

PinchTab is the right tool because it drives its own persistent-profile Chrome and its default `click`/`type` dispatch
trusted CDP `Input.*` events (`isTrusted=true`), which fire the real mouse and `input` events Angular's guards require.
The historical "raw CDP fails, only browser-use works" note was a misdiagnosis: the trap was value-injection (`fill` /
setting `.value`), which never fires the `input` event that enables the Entrar button, NOT the trust level of the click.
So use `pinchtab type` (keystrokes) for the CPF and password fields and default `pinchtab click` (never `--mode
dom`/`--mode dispatch`) for the buttons.
</why_not_chrome_devtools>

<xhr_capture_pattern>
B3's SPA fires XHR/Fetch requests on every page navigation and most interactions. We capture them via raw CDP
`Network.enable` on a parallel WebSocket while PinchTab drives the browser.

The bundled `scripts/b3_capture_listener.py` does this. Run it in the background BEFORE driving the browser:

```bash
cd /home/zanoni/.claude-discord-agents/golden
nohup uv run python <skill_dir>/scripts/b3_capture_listener.py > /tmp/b3-listener.log 2>&1 &
disown
```

It writes one JSON file per captured XHR into `data/raw/b3/<today>/explore/<HHMMSS>_<seq>_<url-segment>.json` and
appends a `summary.txt`. SIGINT stops it cleanly. After each PinchTab click/navigation, give the listener 3-4 seconds to
drain.

Alternative to evaluate as a follow-up: PinchTab ships a built-in capture, `pinchtab network --type xhr --filter
investidor.b3 --body --buffer-size 500 --json`, which can replace the listener. The raw-CDP listener stays primary for
now because it guarantees a body fetch on every `loadingFinished` and is the proven high-volume path.
</xhr_capture_pattern>

<endpoint_catalog>
Two API host prefixes under `investidor.b3.com.br`:
- `/negocio-<area>/api/<area>/<version>/<route>`: main pattern
- `/api/<area>/<version>/<route>`: auxiliary (transferencia-ativos)

**Position / patrimônio**:
- `GET /negocio-home/api/home/v1/minha-carteira/instituicao`: patrimônio total + institutions list + category breakdown
  (RF/RV)
- `GET /negocio-home/api/home/v1/minha-carteira/instituicao?documentoInstituicao=<CNPJ>`: **per-institution detail**
  (the institution-filter trick)
- `GET /negocio-home/api/home/v2/total-acumulado?dc=YYYY-MM-DDT00:00:00`: patrimônio scalar
- `GET /negocio-home/api/home/v1/minha-carteira/resumo`: 30d delta + insight
- `GET /negocio-home/api/home/v2/evolucao-patrimonial?ap=N&dc=...`: historical patrimônio
- `GET /negocio-home/api/home/v1/minha-carteira/instituicao` (no param): across all institutions

**Cash flow / trades**:
- `GET
  /negocio-movimentacao/api/extrato-movimentacao/v2/movimentacao?dataInicio=YYYY-MM-DD&dataFim=YYYY-MM-DD&pagina=N`:
  paginated cash events
- `GET /negocio-movimentacao/api/extrato-movimentacao/v2/movimentacao/ultimas`: recent
- `GET /negocio-negociacaoativos/api/extrato-negociacao-ativos/v1/negociacao-ativos/1?dataInicio=...&dataFim=...`:
  executed trades
- `GET /negocio-home/api/home/v2/negociacao/ultimas-negociacoes?dataFim=YYYY-MM-DD`: last few trades

**Dividends / proventos**:
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/recebidos?dti=YYYY-MM-DD&dtf=YYYY-MM-DD`:
  received provents
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v2/receber?data=YYYY-MM-DD`: upcoming provents
  (with `previsaoPagamento`)
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/resumo-mensal/recebidos?dc=...`: monthly
  aggregate
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/recebidos/resumo-proventos`: `totalAno` and
  `totalUltimosDozeMeses`
- `GET /negocio-eventosprovisionados/api/extrato-eventos-provisionados/v1/proventos/investidor/anos`: years with
  provents

**IR / reports**:
- `GET /negocio-informerendimentos/api/informes/v1/informe-rendimentos`: IR yearly statement (returns `[]` if none
  generated)
- `/relatorios/mensal-consolidado` page has PDF/Excel download buttons (file URL likely `/api/relatorios/...`; not
  captured yet)

**Misc**:
- `GET /negocio-investidor/api/investidor/v1.3/cadastro`: investor data
- `GET /negocio-investidor/api/investidor/v1/perfil`: profile
- `GET /api/transferencia-ativos/v2/solicitacoes/pendentes`: portability
- `GET /negocio-ofertaspublicas/api/extrato-ofertas-publicas/v1/ofertas-publicas/1`: IPOs

All endpoints take a `cache-guid=<uuid>` query parameter that the SPA generates per session.

**The Nubank CTVM CNPJ for the institution filter is `62169875000179`.** Other institutions Lucas had visible on
2026-05-12: Cclaa Sicoob (`81367880000130`), CEF (`00360305000104`), Inter (`18945670000146`), Inter alt CNPJ
(`00416968000101`).

Persistent endpoint patterns are committed to `/home/zanoni/.claude-discord-agents/golden/golden_cli/b3_endpoints.py`.
</endpoint_catalog>

<gotchas>
**Angular enables Entrar only on a real `input` event.** Use `pinchtab type` (never `fill`) for CPF and password and
default `pinchtab click` (never `--mode dom|dispatch`) for buttons; see `<why_not_chrome_devtools>` for why
value-injection leaves the button disabled.

**PinchTab domain allowlist 403.** Should not occur: the browser skill enforces wildcard `allowedDomains` plus IDPI-off
on every rebuild. If a `navigation blocked by IDPI: Domain not in allowlist` 403 ever appears, the enforced config
drifted or the running server predates it, so `rebuild` the host and `pinchtab server restart`.

**Cookie banner gating.** `Entrar` is permanently disabled until cookies are dismissed. Reject *or* accept works, but
rejection persists across page reloads.

**Anti-automation residual risk.** PinchTab's stealth is light (vs browser-use's heavier stealth), so B3's B2C
anti-automation heuristics are the open variable, confirmed only by a live headed login. The persistent headed profile
(a real prior login, real cookies) helps more than browser-use's throwaway profile did. If login is refused, retry from
a fresh headed session before assuming a code bug.

**404 on `/extrato/posicoes` and `/extrato/eventos`.** Those routes are stale. The current "Posições" view is the SPA
root (`/`), and "Eventos" is a tab within the Extratos page accessed via the side-tab click (not a direct URL).

**`golden b3-sync --capture` is broken** as of 2026-05-12. Attaches WebSocket correctly but captures 0 XHRs. Root cause
not investigated. Workaround: use the bundled `b3_capture_listener.py` instead. TODO: debug
`b3_cdp_client.py:_pump_incoming_messages` and the response-body race condition.

**RDB de emissor Nubank-interno não aparece na B3.** The R$ 25k of Nubank Caixinhas (RDB Nubank-issued) is invisible to
B3 custódia. Only equity, FII, BDR, ETF, externally-custodiada renda fixa show up. Don't treat B3 patrimônio as total
Nubank patrimônio.

**Settlement lag.** Trades executed on day D appear in "ultimas-negociacoes" immediately but don't enter
"total-acumulado" patrimônio until D+2 settlement. The settlement cash sits in `RV` category as "cash on B3" during the
lag.
</gotchas>

<standard_workflow>
For "sync Nubank-only positions from B3":

1. Verify `.env` has `B3_CPF` and `B3_PASSWORD`. If missing, ask Lucas (and tell him to paste in DM not channel).
   Confirm PinchTab bootstrap is done (`<pinchtab_bootstrap>`).
2. Start the listener: `nohup uv run python
   ~/.local/share/claude-skill-sets/personal/.claude/skills/b3-portal/scripts/b3_capture_listener.py >
   /tmp/b3-listener.log 2>&1 & disown`.
3. Drive login via PinchTab (`<login_flow>`):
   - `pinchtab nav https://www.investidor.b3.com.br/login --snap`
   - click the cookie accept button `#onetrust-accept-btn-handler`
   - `pinchtab type` the CPF into the `Digite seu CPF ou CNPJ` input
   - `pinchtab click` the `Entrar` button (default mode)
   - on the B2C page: `pinchtab type` the password, then `pinchtab click` `ENTRAR`
   - confirm `pinchtab url` is back at investidor.b3.com.br with the dashboard.
4. Click the `NU` institution filter chip → captures `minha-carteira/instituicao?documentoInstituicao=62169875000179` →
   has NU's RF/RV breakdown.
5. `pinchtab nav` to `/extrato/movimentacao` and `/extrato/negociacao` for cash flow and trades.
6. `pinchtab nav` to `/proventos/visao-geral` and click through the 5 tabs (Visão geral, Recebidos, A Receber, Radar,
   Calendário) for full dividend history.
7. Stop the listener with `kill <pid>`.
8. Inspect the captured JSON files in `data/raw/b3/<today>/explore/` and filter to NU-only by `nomeInstituicao == "NU
   INVESTIMENTOS S.A. - CTVM"` or `documentoInstituicao == "62169875000179"`.

For just verifying Lucas's NU patrimônio total: the single call `GET
/negocio-home/api/home/v1/minha-carteira/instituicao?documentoInstituicao=62169875000179` with the session cookies
suffices. If a future b3-sync writes that endpoint directly, it can skip the navigation entirely after login.
</standard_workflow>

<remember>
- Always work in the golden workspace (`/home/zanoni/.claude-discord-agents/golden/`).
- Always use uv (`uv run python ...`), never `pip` or `python3` directly.
- The listener writes to `data/raw/b3/<today>/explore/` (gitignored).
- Raw JSON dumps are the source of truth; parse them with `uv run python -c '...'` rather than re-fetching.
- After scraping, decide whether anything materially changed before updating `portfolio.json`: most days B3 just
  confirms what Lucas already told Golden.
</remember>
