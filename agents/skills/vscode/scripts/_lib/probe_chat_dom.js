// Probe the live VS Code DOM for Claude Code chat selectors.
//
// Read at startup by cdp_cli.py and templated through string.Template — the
// four INPUT_SELECTOR, SEND_SELECTOR, STOP_SELECTOR, ASSISTANT_SELECTOR
// placeholders below are substituted with JSON-quoted strings (already
// wrapped in their own quotes). Python's string.Template substitution does
// not conflict with JavaScript braces, so this file remains valid standalone
// JavaScript and can be lint-checked.  (Note: literal dollar signs in this
// comment would have to be doubled per string.Template escaping rules, so
// the placeholders are referenced without the leading sigil here.)
JSON.stringify({
  pinned_selectors: {
    chat_input_editor: (() => {
      const el = document.querySelector($INPUT_SELECTOR);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        found: true,
        rect: {
          x: Math.round(r.x),
          y: Math.round(r.y),
          w: Math.round(r.width),
          h: Math.round(r.height),
        },
        cls: (el.className || "").toString().slice(0, 120),
      };
    })(),
    send_button: (() => {
      const el = document.querySelector($SEND_SELECTOR);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        found: true,
        disabled: el.classList.contains("disabled"),
        aria: el.getAttribute("aria-label") || "",
        rect: {
          x: Math.round(r.x),
          y: Math.round(r.y),
          w: Math.round(r.width),
          h: Math.round(r.height),
        },
      };
    })(),
    stop_button: (() => {
      const el = document.querySelector($STOP_SELECTOR);
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        found: true,
        aria: el.getAttribute("aria-label") || "",
        rect: {
          x: Math.round(r.x),
          y: Math.round(r.y),
          w: Math.round(r.width),
          h: Math.round(r.height),
        },
      };
    })(),
    assistant_messages: {
      count: document.querySelectorAll($ASSISTANT_SELECTOR).length,
    },
  },
  candidate_message_selectors: [
    {
      sel: ".interactive-list .interactive-item-container",
      count: document.querySelectorAll(
        ".interactive-list .interactive-item-container",
      ).length,
    },
    {
      sel: ".interactive-list .interactive-response",
      count: document.querySelectorAll(
        ".interactive-list .interactive-response",
      ).length,
    },
    {
      sel: ".interactive-list .interactive-request",
      count: document.querySelectorAll(".interactive-list .interactive-request")
        .length,
    },
    {
      sel: ".interactive-response",
      count: document.querySelectorAll(".interactive-response").length,
    },
    {
      sel: ".chat-response",
      count: document.querySelectorAll(".chat-response").length,
    },
    {
      sel: "[data-username]",
      count: document.querySelectorAll("[data-username]").length,
    },
    {
      sel: ".interactive-list > div",
      count: document.querySelectorAll(".interactive-list > div").length,
    },
  ],
  chat_toolbar_buttons: Array.from(
    document.querySelectorAll(
      ".chat-execute-toolbar .action-label, .chat-input-toolbars .action-label",
    ),
  ).map((el) => {
    const r = el.getBoundingClientRect();
    return {
      aria: (
        el.getAttribute("aria-label") ||
        el.title ||
        el.textContent ||
        ""
      ).slice(0, 80),
      cls: (el.className || "").toString().slice(0, 100),
      disabled: el.classList.contains("disabled"),
      rect: {
        x: Math.round(r.x),
        y: Math.round(r.y),
        w: Math.round(r.width),
        h: Math.round(r.height),
      },
    };
  }),
  editable_elements: Array.from(
    document.querySelectorAll('textarea, input, [contenteditable="true"]'),
  ).map((el) => {
    const r = el.getBoundingClientRect();
    return {
      tag: el.tagName,
      placeholder:
        el.getAttribute("placeholder") || el.getAttribute("aria-label") || "",
      cls: (el.className || "").toString().slice(0, 100),
      rect: {
        x: Math.round(r.x),
        y: Math.round(r.y),
        w: Math.round(r.width),
        h: Math.round(r.height),
      },
      visible: el.offsetParent !== null,
    };
  }),
  send_button_ancestor_chain: (() => {
    const send = document.querySelector($SEND_SELECTOR);
    if (!send) return null;
    const chain = [];
    let el = send;
    for (let i = 0; i < 12 && el; i++) {
      chain.push({
        tag: el.tagName,
        cls: (el.className || "").toString().slice(0, 120),
      });
      el = el.parentElement;
    }
    return chain;
  })(),
  chat_input_ancestor_chain: (() => {
    const ed = document.querySelector($INPUT_SELECTOR);
    if (!ed) return null;
    const chain = [];
    let el = ed;
    for (let i = 0; i < 10 && el; i++) {
      chain.push({
        tag: el.tagName,
        cls: (el.className || "").toString().slice(0, 120),
      });
      el = el.parentElement;
    }
    return chain;
  })(),
});
