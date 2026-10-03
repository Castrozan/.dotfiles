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
  if (!isWithinTraversalBounds(obj, depth)) return;
  if (!markAsUnseen(obj)) return;
  if (isPageHostObject(obj)) return;

  for (const key in obj) {
    try {
      const val = obj[key];
      if (patchVisibilityGate(obj, key, val)) continue;
      patchAgeFeatureFlag(obj, key, val);
      recurseIntoObject(val, depth);
    } catch {}
  }
}

function isWithinTraversalBounds(obj, depth) {
  if (!obj || typeof obj !== "object") return false;
  if (depth > 20) return false;
  return true;
}

function isPageHostObject(obj) {
  return obj === window || obj === document || obj instanceof Node;
}

function markAsUnseen(obj) {
  if (seen.has(obj)) return false;
  try {
    seen.add(obj);
    return true;
  } catch {
    return false;
  }
}

function patchVisibilityGate(obj, key, val) {
  if (patchBlurredInterstitial(obj, key, val)) return true;
  return patchMediaVisibilityResults(obj, key, val);
}

function patchBlurredInterstitial(obj, key, val) {
  if (key !== "blurred_image_interstitial") return false;
  if (!val) return false;
  if (!val.interstitial_action) return false;
  obj[key] = null;
  return true;
}

function patchMediaVisibilityResults(obj, key, val) {
  if (key !== "mediaVisibilityResults") return false;
  if (!val) return false;
  if (!val.blurred_image_interstitial) return false;
  obj[key] = null;
  return true;
}

function patchAgeFeatureFlag(obj, key, val) {
  if (val !== true) return;
  if (key === "rweb_age_assurance_flow_enabled") obj[key] = false;
  if (key === "age_verification_gate_enabled") obj[key] = false;
}

function recurseIntoObject(val, depth) {
  if (val && typeof val === "object") patchDeep(val, depth + 1);
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
