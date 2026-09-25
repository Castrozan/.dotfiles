import assert from "node:assert/strict";
import { EventEmitter } from "node:events";
import { resolve } from "node:path";
import { test } from "node:test";
import { pathToFileURL } from "node:url";

const sourceDirectory = `${resolve(process.env.CHROME_DEVTOOLS_MCP_PACKAGE)}/build/src`;
await import(pathToFileURL(`${sourceDirectory}/utils/polyfill.js`));
const { McpPage } = await import(
  pathToFileURL(`${sourceDirectory}/McpPage.js`)
);
const { BrowserManager } = await import(
  pathToFileURL(`${sourceDirectory}/BrowserManager.js`)
);
const { DevTools, puppeteer } = await import(
  pathToFileURL(`${sourceDirectory}/third_party/index.js`)
);
const { overrideDevToolsGlobals } = await import(
  pathToFileURL(`${sourceDirectory}/devtools/DevtoolsUtils.js`)
);

overrideDevToolsGlobals({
  loadResource: async () => ({ success: false, content: "" }),
});

function createPage() {
  const page = new EventEmitter();
  const frame = new EventEmitter();
  const session = new EventEmitter();
  const calls = { created: 0, detached: 0 };
  session.id = () => "test-session";
  session.target = () => ({ _targetId: "test-target" });
  session.connection = () => ({ session: () => session });
  session.send = async (method) =>
    method === "Debugger.enable" ? { debuggerId: "test-debugger" } : {};
  session.detach = async () => {
    calls.detached++;
    session.removeAllListeners();
  };
  page.mainFrame = () => frame;
  page._client = () => session;
  page.emulateFocusedPage = async () => {};
  page.createCDPSession = async () => {
    calls.created++;
    return session;
  };
  return { page, session, calls };
}

test("enumerating fifteen pages creates no DevTools sessions", async () => {
  for (let index = 0; index < 15; index++) {
    const { page, calls } = createPage();
    const managedPage = new McpPage(page, index, {});
    await managedPage.init();
    assert.equal(calls.created, 0);
    managedPage.dispose();
  }
});

test("concurrent requests share one session and disposal prevents recreation", async () => {
  const { page, calls } = createPage();
  const managedPage = new McpPage(page, 1, {});
  const universes = await Promise.all(
    Array.from({ length: 10 }, () => managedPage.ensureDevtoolsUniverse()),
  );
  assert.ok(universes[0]);
  assert.ok(universes.every((universe) => universe === universes[0]));
  assert.equal(calls.created, 1);
  managedPage.dispose();
  assert.equal(calls.detached, 1);
  assert.equal(await managedPage.ensureDevtoolsUniverse(), undefined);
  assert.equal(calls.created, 1);
});

test("closing a page during initialization detaches the late session", async () => {
  const { page, session, calls } = createPage();
  let completeInitialization;
  page.createCDPSession = () =>
    new Promise((resolveSession) => {
      completeInitialization = resolveSession;
    });
  const managedPage = new McpPage(page, 1, {});
  const initialization = managedPage.ensureDevtoolsUniverse();
  managedPage.dispose();
  completeInitialization(session);
  assert.equal(await initialization, undefined);
  assert.equal(calls.detached, 1);
  assert.equal(managedPage.devtoolsUniverse, undefined);
});

test("failed initialization can be retried without retaining a rejected promise", async () => {
  const { page, session } = createPage();
  let attempts = 0;
  page.createCDPSession = async () => {
    if (++attempts === 1) throw new Error("Connection interrupted");
    return session;
  };
  const managedPage = new McpPage(page, 1, {});
  assert.equal(await managedPage.ensureDevtoolsUniverse(), undefined);
  assert.ok(await managedPage.ensureDevtoolsUniverse());
  assert.equal(attempts, 2);
  managedPage.dispose();
});

test("a lost CDP session returns a protocol error without an uncaught exception", async () => {
  const { session } = createPage();
  session.connection = () => ({ session: () => undefined });
  const connection = new DevTools.PuppeteerDevToolsConnection(session);
  let response;
  assert.doesNotThrow(() => {
    response = connection.send("Runtime.enable", {}, "expired-session");
  });
  assert.match((await response).error.message, /Unknown session/);
  connection.dispose("test complete");
  assert.equal(session.eventNames().length, 0);
});

test("a disconnected attached browser reconnects without closing user Chrome", async (context) => {
  let connections = 0;
  let disconnections = 0;
  context.mock.method(puppeteer, "connect", async () => {
    connections++;
    return {
      connected: true,
      disconnect: async () => disconnections++,
      close: async () => assert.fail("Attached Chrome must remain running"),
    };
  });
  const manager = new BrowserManager({ autoConnect: true, channel: "stable" });
  const original = await manager.ensureBrowser();
  assert.equal(await manager.ensureBrowser(), original);
  original.connected = false;
  assert.notEqual(await manager.ensureBrowser(), original);
  assert.equal(connections, 2);
  await manager.close();
  assert.equal(disconnections, 1);
});
