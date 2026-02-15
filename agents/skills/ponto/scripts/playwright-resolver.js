import { execSync } from 'child_process';
import { readFileSync } from 'fs';

function resolvePlaywrightCorePath() {
  const pwPath = execSync('which pw', { encoding: 'utf-8' }).trim();
  const pwScript = readFileSync(pwPath, 'utf-8');
  const nodeModulesMatch = pwScript.match(/PW_NODE_MODULES="([^"]+)"/);

  if (!nodeModulesMatch) {
    throw new Error('could not resolve PW_NODE_MODULES from pw wrapper script');
  }

  return `${nodeModulesMatch[1]}/playwright-core/index.js`;
}

async function connectToBrowser() {
  const playwrightCorePath = resolvePlaywrightCorePath();
  const playwrightModule = await import(playwrightCorePath);
  const chromium = playwrightModule.chromium || playwrightModule.default?.chromium;

  if (!chromium) {
    throw new Error(`could not find chromium export in ${playwrightCorePath}`);
  }

  const browser = await chromium.connectOverCDP('http://localhost:9222');
  const page = browser.contexts()[0].pages()[0];
  return { browser, page };
}

async function findPontoFrame(page) {
  for (const frame of page.frames()) {
    try {
      const title = await frame.title();
      if (title.includes('acertos de ponto') || title.includes('Gestão do Ponto')) {
        return frame;
      }
    } catch {}
  }
  return null;
}

export { connectToBrowser, findPontoFrame };
