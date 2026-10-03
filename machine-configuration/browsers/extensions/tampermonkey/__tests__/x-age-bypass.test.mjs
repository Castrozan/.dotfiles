import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import vm from "node:vm";

const source = readFileSync(
  new URL("../x-age-bypass.user.js", import.meta.url),
  "utf8",
);

function loadScript() {
  const context = vm.createContext({
    window: { webpackChunk_twitter_responsive_web: [] },
    document: {},
    Node: class Node {},
    history: { pushState() {} },
  });
  vm.runInContext(source, context);
  return context;
}

test("JSON responses clear nested gates and retain unrelated values", () => {
  const context = loadScript();
  const result = vm.runInContext(
    `JSON.parse(JSON.stringify({
      entries: [{
        blurred_image_interstitial: { interstitial_action: "show" },
        mediaVisibilityResults: { blurred_image_interstitial: {} },
        rweb_age_assurance_flow_enabled: true,
        age_verification_gate_enabled: true,
        unrelated: true
      }],
      blurred_image_interstitial: null,
      age_verification_gate_enabled: "true"
    }))`,
    context,
  );
  assert.deepEqual(JSON.parse(JSON.stringify(result)), {
    entries: [
      {
        blurred_image_interstitial: null,
        mediaVisibilityResults: null,
        rweb_age_assurance_flow_enabled: false,
        age_verification_gate_enabled: false,
        unrelated: true,
      },
    ],
    blurred_image_interstitial: null,
    age_verification_gate_enabled: "true",
  });
  assert.equal(vm.runInContext('JSON.parse("12")', context), 12);
  assert.throws(() => vm.runInContext('JSON.parse("{")', context), {
    name: "SyntaxError",
  });
});

test("traversal retains cycle, depth, host-object and getter boundaries", () => {
  const context = loadScript();
  const result = vm.runInContext(
    `(() => {
      const root = { age_verification_gate_enabled: true };
      root.self = root;
      Object.defineProperty(root, "broken", {
        enumerable: true,
        get() { throw new Error("inaccessible"); }
      });
      root.after = { age_verification_gate_enabled: true };
      root.host = new Node();
      root.host.age_verification_gate_enabled = true;
      let deepest = root;
      for (let depth = 0; depth < 21; depth += 1) {
        deepest.child = { age_verification_gate_enabled: true };
        deepest = deepest.child;
      }
      patchDeep(root, 0);
      return [root.age_verification_gate_enabled,
        root.after.age_verification_gate_enabled,
        root.host.age_verification_gate_enabled,
        deepest.age_verification_gate_enabled];
    })()`,
    context,
  );
  assert.deepEqual(Array.from(result), [false, false, true, true]);
});
