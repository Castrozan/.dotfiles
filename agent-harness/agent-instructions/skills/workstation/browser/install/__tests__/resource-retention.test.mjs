import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { existsSync } from "node:fs";
import { resolve } from "node:path";
import { test } from "node:test";
import { pathToFileURL } from "node:url";

const packageDirectory = resolve(process.env.CHROME_DEVTOOLS_MCP_PACKAGE);
const sourceDirectory = `${packageDirectory}/build/src`;
const collectorPath = existsSync(
  `${sourceDirectory}/collectors/PageCollector.js`,
)
  ? `${sourceDirectory}/collectors/PageCollector.js`
  : `${sourceDirectory}/PageCollector.js`;
const { NetworkCollector, ConsoleCollector } = await import(
  pathToFileURL(collectorPath)
);
const { createTargetUniverse, overrideDevToolsGlobals } = await import(
  pathToFileURL(`${sourceDirectory}/devtools/DevtoolsUtils.js`)
);
const { DevTools } = await import(
  pathToFileURL(`${sourceDirectory}/third_party/index.js`)
);

function createPage() {
  const page = new EventEmitter();
  const frame = new EventEmitter();
  const session = new EventEmitter();
  session.target = () => ({ _targetId: "test-target" });
  page.mainFrame = () => frame;
  page._client = () => session;
  return page;
}

test("network traffic retains at most 1000 requests per navigation", () => {
  const page = createPage();
  const collector = new NetworkCollector(page);
  for (let navigation = 0; navigation < 5; navigation++) {
    for (let index = 0; index < 20_000; index++) {
      page.emit("request", {
        index,
        frame: () => page.mainFrame(),
        isNavigationRequest: () => false,
      });
    }
    assert.equal(collector.getData(false).length, 1000);
    assert.equal(collector.getData(false)[0].index, 19_000);
    assert.ok(collector.getData(true).length <= 3000);
    page.emit("framenavigated", page.mainFrame());
  }
  collector.dispose();
  assert.equal(page.listenerCount("request"), 0);
  assert.equal(page.listenerCount("framenavigated"), 0);
  assert.equal(page.mainFrame().eventNames().length, 0);
});

test("console traffic retains at most 10000 messages per navigation", () => {
  const page = createPage();
  const collector = new ConsoleCollector(page, (collect) => ({
    console: collect,
  }));
  for (let index = 0; index < 20_000; index++) {
    page.emit("console", { index });
  }
  assert.equal(collector.getData(false).length, 10_000);
  assert.equal(collector.getData(false)[0].index, 10_000);
  collector.dispose();
  assert.equal(page.eventNames().length, 0);
  assert.equal(page._client().eventNames().length, 0);
  assert.equal(page.mainFrame().eventNames().length, 0);
});

test("DevTools loads source maps only on demand", async () => {
  const session = new EventEmitter();
  session.id = () => "test-session";
  session.connection = () => ({ session: () => session });
  session.send = async (method) =>
    method === "Debugger.enable" ? { debuggerId: "test-debugger" } : {};
  overrideDevToolsGlobals({
    loadResource: async () => {
      throw new Error("An unused source map must not be fetched");
    },
  });
  const { universe } = await createTargetUniverse(session);
  try {
    const descriptor = DevTools.SourceMapManager?.lazyLoadingSettingDescriptor;
    assert.ok(descriptor, "The bundle must support lazy source maps");
    assert.equal(universe.settings.resolve(descriptor).get(), true);
  } finally {
    universe.dispose?.();
    session.removeAllListeners();
  }
});
