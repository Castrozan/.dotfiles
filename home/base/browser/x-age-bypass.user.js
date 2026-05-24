// ==UserScript==
// @name         X Age Bypass (BR)
// @version      1.2.0
// @description  Bypass X/Twitter age verification gate (Brazil content policy)
// @author       zanoni
// @match        https://x.com/*
// @match        https://twitter.com/*
// @grant        none
// @run-at       document-start
// @inject-into  page
// ==/UserScript==

// How it works:
// X's GraphQL API returns tweets with age-gated media as type "TweetWithVisibilityResults".
// The media URLs are fully present in the response — the gate is purely client-side.
// The key field is: mediaVisibilityResults.blurred_image_interstitial.interstitial_action = "AgeVerificationPrompt"
// We hook JSON.parse to strip this field before X's React code sees it.

// With @grant none + @inject-into page, this runs directly in page context.
// No script element injection needed (which Brave's CSP blocks).

const seen = new WeakSet();
function patchDeep(obj, depth) {
  if (!obj || typeof obj !== "object" || depth > 20) return;
  if (seen.has(obj)) return;
  try {
    seen.add(obj);
  } catch {
    return;
  }
  if (obj === window || obj === document || obj instanceof Node) return;

  for (const key in obj) {
    try {
      const val = obj[key];

      // The main gate: strip the blurred_image_interstitial from API responses
      if (
        key === "blurred_image_interstitial" &&
        val &&
        val.interstitial_action
      ) {
        obj[key] = null;
        continue;
      }

      // Also null the parent container if present
      if (
        key === "mediaVisibilityResults" &&
        val &&
        val.blurred_image_interstitial
      ) {
        obj[key] = null;
        continue;
      }

      // Feature flags that enable the gate
      if (key === "rweb_age_assurance_flow_enabled" && val === true) {
        obj[key] = false;
      }
      if (key === "age_verification_gate_enabled" && val === true) {
        obj[key] = false;
      }

      if (val && typeof val === "object") {
        patchDeep(val, depth + 1);
      }
    } catch {}
  }
}

// Hook JSON.parse — catches all GraphQL API responses
const origParse = JSON.parse;
JSON.parse = function () {
  const result = origParse.apply(this, arguments);
  try {
    if (result && typeof result === "object") patchDeep(result, 0);
  } catch {}
  return result;
};

// Hook webpack — patches the tombstone overlay component
function hookWebpack() {
  const wp = window.webpackChunk_twitter_responsive_web;
  if (!wp) {
    setTimeout(hookWebpack, 50);
    return;
  }

  const origWpPush = wp.push;
  wp.push = function (chunk) {
    const modules = chunk[1];
    for (const id in modules) {
      if (!modules.hasOwnProperty(id)) continue;
      const code = modules[id].toString();
      if (code.includes("sensitiveMediaVisibilityResultsTombstoneConfig=")) {
        const orig = modules[id];
        modules[id] = function (module, exports, require) {
          orig(module, exports, require);
          try {
            const t =
              module.exports?.Z || module.exports?.default || module.exports;
            if (t?.sensitiveMediaVisibilityResultsTombstoneConfig) {
              t.sensitiveMediaVisibilityResultsTombstoneConfig.withBlurredMedia = false;
            }
          } catch {}
        };
      }
    }
    return origWpPush.call(this, chunk);
  };
}

// Block SPA navigation to age_verification
const origPushState = history.pushState;
history.pushState = function () {
  if (arguments[2]?.includes?.("age_verification")) return;
  return origPushState.apply(this, arguments);
};

hookWebpack();
