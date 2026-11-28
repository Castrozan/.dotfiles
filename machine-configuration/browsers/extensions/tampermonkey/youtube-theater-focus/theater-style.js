(() => {
  const STYLE_ID = "ytweak-style";

  const cssRules = [
    "ytd-watch-flexy { --ytweak-col: min(1600px, 92vw); }",
    "ytd-app { --ytd-masthead-height: 45px !important; }",
    "#masthead-container.ytd-app, ytd-masthead#masthead, ytd-masthead #background.ytd-masthead, ytd-masthead #container.ytd-masthead { height: 45px !important; min-height: 45px !important; }",
    "ytd-page-manager.ytd-app { margin-top: 45px !important; }",
    "html.ytweak-header-below-video ytd-app { --ytd-masthead-height: 0px !important; }",
    "html.ytweak-header-below-video ytd-page-manager.ytd-app { margin-top: 0 !important; }",
    "html.ytweak-header-below-video #masthead-container.ytd-app { visibility: hidden !important; position: relative !important; inset: auto !important; width: 100% !important; margin: 8px auto 16px !important; transform: none !important; }",
    "html.ytweak-header-below-video #masthead-container.ytd-app:has(+ ytd-watch-metadata) { visibility: visible !important; }",
    "html.ytweak-header-below-video #skip-navigation:not(:focus-within) { clip-path: inset(50%) !important; }",
    "ytd-watch-flexy[theater] #full-bleed-container { height: calc(100vh - 53px) !important; max-height: calc(100vh - 53px) !important; }",
    "html.ytweak-header-below-video ytd-watch-flexy[theater] #full-bleed-container { height: 100vh !important; max-height: 100vh !important; }",
    "ytd-watch-flexy[theater] #columns { display: flex !important; flex-direction: column !important; align-items: center !important; }",
    "ytd-watch-flexy[theater] #primary, ytd-watch-flexy[theater] #primary-inner { width: 100% !important; max-width: var(--ytweak-col) !important; margin: 0 auto !important; }",
    "ytd-watch-flexy[theater] #primary #below { margin-bottom: 0 !important; }",
    "ytd-watch-flexy[theater] #secondary { width: 100% !important; max-width: var(--ytweak-col) !important; margin: 12px auto 0 !important; padding: 0 !important; }",
    "ytd-watch-flexy[theater] #secondary #related ytd-item-section-renderer > #contents { display: grid !important; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)) !important; gap: 16px 20px !important; }",
    "ytd-watch-flexy[theater] #secondary yt-lockup-view-model { width: 100% !important; max-width: none !important; }",
    "ytd-watch-flexy #comments { display: none !important; }",
    "ytd-watch-flexy.ytweak-comments #comments { display: block !important; width: 100% !important; max-width: var(--ytweak-col) !important; margin: 0 auto !important; }",
    "ytd-watch-flexy.ytweak-comments #secondary { display: none !important; }",
    "#ytweak-tabs { display: flex; gap: 8px; margin: 16px auto 8px; }",
    "#ytweak-tabs button { font: 500 14px/1 Roboto, system-ui, sans-serif; padding: 10px 20px; border-radius: 18px; border: none; cursor: pointer; background: var(--yt-spec-badge-chip-background, #272727); color: var(--yt-spec-text-primary, #f1f1f1); transition: background .15s; }",
    "#ytweak-tabs button.active { background: var(--yt-spec-call-to-action, #3ea6ff); color: #0f0f0f; }",
  ];

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) return;

    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = cssRules.join("\n");
    (document.head || document.documentElement).appendChild(style);
  }

  window.addEventListener("yt-navigate-finish", ensureStyle);
  window.addEventListener("yt-page-data-updated", ensureStyle);
  ensureStyle();
})();
