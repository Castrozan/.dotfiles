import http from 'node:http';
import { execSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';

let resolvedCdpPort = null;

function discoverChromeDebugPort() {
  if (resolvedCdpPort) return resolvedCdpPort;

  const ssOutput = execSync('ss -tlnp 2>/dev/null', { encoding: 'utf-8' });
  const chromiumListeningMatch = ssOutput.match(
    /127\.0\.0\.1:(\d+).*(?:chromium|chrome|brave)/,
  );

  if (!chromiumListeningMatch) {
    throw new Error(
      'could not find Chrome CDP port — is pinchtab running? (no chromium listening on localhost)',
    );
  }

  resolvedCdpPort = parseInt(chromiumListeningMatch[1]);
  return resolvedCdpPort;
}

const QUERY_ELEMENTS_SOURCE = `function queryElements(root, selector, firstOnly) {
  function matchPart(r, part) {
    const m = part.match(/^(.+?):has-text\\("([^"]+)"\\)$/);
    if (m) return [...r.querySelectorAll(m[1])].filter(el => el.textContent.includes(m[2]));
    return [...r.querySelectorAll(part)];
  }
  const results = selector.split(/,\\s*/).flatMap(p => matchPart(root, p));
  return firstOnly ? (results[0] || null) : results;
}`;

function cdpHttpGet(path) {
  const port = discoverChromeDebugPort();
  return new Promise((resolve, reject) => {
    http
      .get(`http://127.0.0.1:${port}${path}`, (res) => {
        let data = '';
        res.on('data', (chunk) => (data += chunk));
        res.on('end', () => {
          try {
            resolve(JSON.parse(data));
          } catch {
            reject(new Error(`invalid CDP response at ${path}`));
          }
        });
      })
      .on('error', reject);
  });
}

class CdpSession {
  constructor(ws) {
    this.ws = ws;
    this.nextId = 0;
    this.pending = new Map();
    this.listeners = new Map();

    ws.addEventListener('message', (event) => {
      const text =
        typeof event.data === 'string'
          ? event.data
          : new TextDecoder().decode(event.data);
      const msg = JSON.parse(text);

      if (msg.id !== undefined) {
        const callback = this.pending.get(msg.id);
        if (callback) {
          this.pending.delete(msg.id);
          callback(msg);
        }
      }

      if (msg.method) {
        for (const handler of this.listeners.get(msg.method) || []) {
          handler(msg.params);
        }
      }
    });
  }

  static connect(wsUrl) {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(wsUrl);
      ws.addEventListener('open', () => resolve(new CdpSession(ws)));
      ws.addEventListener('error', () =>
        reject(new Error('CDP WebSocket connection failed')),
      );
    });
  }

  call(method, params = {}) {
    return new Promise((resolve, reject) => {
      const id = ++this.nextId;
      this.pending.set(id, (msg) => {
        if (msg.error) reject(new Error(`${method}: ${msg.error.message}`));
        else resolve(msg.result);
      });
      this.ws.send(JSON.stringify({ id, method, params }));
    });
  }

  on(eventName, handler) {
    if (!this.listeners.has(eventName)) this.listeners.set(eventName, []);
    this.listeners.get(eventName).push(handler);
  }

  close() {
    this.ws.close();
  }
}

async function extractRemoteArrayElements(session, remoteObject, contextId) {
  if (!remoteObject.objectId) return [];
  const { result: properties } = await session.call('Runtime.getProperties', {
    objectId: remoteObject.objectId,
    ownProperties: true,
  });
  return properties
    .filter((p) => /^\d+$/.test(p.name) && p.value?.objectId)
    .sort((a, b) => Number(a.name) - Number(b.name))
    .map((p) => new CdpElement(session, p.value.objectId, contextId));
}

class CdpElement {
  constructor(session, objectId, contextId) {
    this.session = session;
    this.objectId = objectId;
    this.contextId = contextId;
  }

  async textContent() {
    const { result } = await this.session.call('Runtime.callFunctionOn', {
      objectId: this.objectId,
      functionDeclaration: 'function() { return this.textContent; }',
      returnByValue: true,
    });
    return result.value;
  }

  async click() {
    await this.session.call('Runtime.callFunctionOn', {
      objectId: this.objectId,
      functionDeclaration:
        'function() { this.scrollIntoView({block:"center"}); this.click(); }',
    });
  }

  async $(selector) {
    const { result } = await this.session.call('Runtime.callFunctionOn', {
      objectId: this.objectId,
      functionDeclaration: `function(sel) { ${QUERY_ELEMENTS_SOURCE} return queryElements(this, sel, true); }`,
      arguments: [{ value: selector }],
      returnByValue: false,
    });
    if (!result.objectId || result.subtype === 'null') return null;
    return new CdpElement(this.session, result.objectId, this.contextId);
  }

  async $$(selector) {
    const { result } = await this.session.call('Runtime.callFunctionOn', {
      objectId: this.objectId,
      functionDeclaration: `function(sel) { ${QUERY_ELEMENTS_SOURCE} return queryElements(this, sel, false); }`,
      arguments: [{ value: selector }],
      returnByValue: false,
    });
    return extractRemoteArrayElements(this.session, result, this.contextId);
  }
}

class CdpFrame {
  constructor(session, contextId) {
    this.session = session;
    this.contextId = contextId;
  }

  async evaluate(functionOrExpression) {
    const expression =
      typeof functionOrExpression === 'function'
        ? `(${functionOrExpression.toString()})()`
        : functionOrExpression;

    const { result, exceptionDetails } = await this.session.call(
      'Runtime.evaluate',
      {
        expression,
        contextId: this.contextId,
        returnByValue: true,
        awaitPromise: true,
      },
    );

    if (exceptionDetails) {
      throw new Error(exceptionDetails.text || 'evaluate failed');
    }
    return result.value;
  }

  async $(selector) {
    const { result } = await this.session.call('Runtime.evaluate', {
      expression: `(function() { ${QUERY_ELEMENTS_SOURCE} return queryElements(document, ${JSON.stringify(selector)}, true); })()`,
      contextId: this.contextId,
      returnByValue: false,
    });
    if (!result.objectId || result.subtype === 'null') return null;
    return new CdpElement(this.session, result.objectId, this.contextId);
  }

  async $$(selector) {
    const { result } = await this.session.call('Runtime.evaluate', {
      expression: `(function() { ${QUERY_ELEMENTS_SOURCE} return queryElements(document, ${JSON.stringify(selector)}, false); })()`,
      contextId: this.contextId,
      returnByValue: false,
    });
    return extractRemoteArrayElements(this.session, result, this.contextId);
  }
}

class CdpPage {
  constructor(session, executionContexts) {
    this.session = session;
    this.executionContexts = executionContexts;
  }

  waitForTimeout(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async screenshot({ path }) {
    const { data } = await this.session.call('Page.captureScreenshot', {
      format: 'png',
    });
    writeFileSync(path, Buffer.from(data, 'base64'));
  }
}

class CdpBrowser {
  constructor(session) {
    this.session = session;
  }

  close() {
    this.session.close();
  }
}

async function connectToBrowser() {
  const targets = await cdpHttpGet('/json');
  const pageTarget = targets.find((t) => t.type === 'page');

  if (!pageTarget) {
    throw new Error('no page target found — is pinchtab running?');
  }

  const session = await CdpSession.connect(pageTarget.webSocketDebuggerUrl);

  const executionContexts = new Map();
  session.on('Runtime.executionContextCreated', ({ context }) => {
    const frameId = context.auxData?.frameId;
    if (frameId) executionContexts.set(frameId, context);
  });
  session.on('Runtime.executionContextDestroyed', ({ executionContextId }) => {
    for (const [frameId, ctx] of executionContexts) {
      if (ctx.id === executionContextId) {
        executionContexts.delete(frameId);
        break;
      }
    }
  });
  session.on('Runtime.executionContextsCleared', () => {
    executionContexts.clear();
  });

  await session.call('Page.enable');
  await session.call('Runtime.enable');
  await new Promise((r) => setTimeout(r, 200));

  return {
    browser: new CdpBrowser(session),
    page: new CdpPage(session, executionContexts),
  };
}

async function findPontoFrame(page) {
  const pontoTitlePatterns = ['acertos de ponto', 'gestão do ponto'];

  for (const [, context] of page.executionContexts) {
    try {
      const { result } = await page.session.call('Runtime.evaluate', {
        expression: 'document.title',
        contextId: context.id,
        returnByValue: true,
      });

      const title = (result.value || '').toLowerCase();
      if (pontoTitlePatterns.some((pattern) => title.includes(pattern))) {
        return new CdpFrame(page.session, context.id);
      }
    } catch {}
  }

  return null;
}

export { connectToBrowser, findPontoFrame, CdpFrame, CdpElement, CdpPage };
