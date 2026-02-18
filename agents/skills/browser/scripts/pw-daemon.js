const http = require("http");
const { chromium } = require("playwright-core");

const PW_PORT = process.env.PW_PORT || "9222";
const DAEMON_PORT = parseInt(PW_PORT) + 1;
const IDLE_TIMEOUT_MS = 10 * 60 * 1000;

let browser = null;
let idleTimer = null;

function resetIdleTimer() {
  if (idleTimer) clearTimeout(idleTimer);
  idleTimer = setTimeout(() => {
    process.exit(0);
  }, IDLE_TIMEOUT_MS);
}

async function getBrowser() {
  if (browser && browser.isConnected()) return browser;
  browser = await chromium.connectOverCDP(`http://127.0.0.1:${PW_PORT}`);
  browser.on("disconnected", () => {
    browser = null;
  });
  return browser;
}

function getActivePage(b) {
  const allPages = b.contexts().flatMap((c) => c.pages());
  if (allPages.length === 0) return null;
  return allPages[allPages.length - 1];
}

function need(page) {
  if (!page) throw new Error("No page open. Run: pw open <url>");
}

async function handleCommand(cmd, args) {
  const b = await getBrowser();
  let page = getActivePage(b);
  const output = [];
  const log = (s) => output.push(s);

  switch (cmd) {
    case "open":
    case "navigate": {
      const isNew = args.includes("--new");
      const url = args.filter((a) => a !== "--new")[0];
      if (!url) throw new Error("Usage: pw open <url>");
      if (!page || isNew) {
        const ctx = b.contexts()[0] || (await b.newContext());
        page = await ctx.newPage();
      }
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
      log(`Page: ${page.url()}`);
      log(`Title: ${await page.title()}`);
      break;
    }

    case "snap":
    case "snapshot": {
      need(page);
      log(await page.locator("body").ariaSnapshot());
      break;
    }

    case "elements":
    case "els": {
      need(page);
      const els = await page.evaluate(() => {
        const sel =
          'a,button,input,select,textarea,[role="button"],[role="link"],[role="tab"],[role="menuitem"],[tabindex]:not([tabindex="-1"])';
        return Array.from(document.querySelectorAll(sel))
          .filter((el) => {
            const s = getComputedStyle(el);
            return (
              s.display !== "none" &&
              s.visibility !== "hidden" &&
              el.offsetParent !== null
            );
          })
          .map((el, i) => {
            const tag = el.tagName.toLowerCase();
            const text = (el.textContent || "")
              .trim()
              .replace(/\s+/g, " ")
              .slice(0, 60);
            const parts = [];
            if (el.id) parts.push(`#${el.id}`);
            if (el.type && el.type !== "submit") parts.push(`type=${el.type}`);
            if (el.name) parts.push(`name="${el.name}"`);
            if (el.placeholder) parts.push(`ph="${el.placeholder}"`);
            if (el.value && el.value.length < 30)
              parts.push(`val="${el.value}"`);
            if (el.href) {
              try {
                parts.push(`-> ${new URL(el.href, location.href).pathname}`);
              } catch {}
            }
            const attr = parts.length ? " " + parts.join(" ") : "";
            return `[${i}] <${tag}${attr}> ${text}`;
          });
      });
      els.forEach((e) => log(e));
      break;
    }

    case "click": {
      need(page);
      const urlBefore = page.url();
      if (/^\d+$/.test(args[0])) {
        const idx = parseInt(args[0]);
        await page.evaluate((i) => {
          const sel =
            'a,button,input,select,textarea,[role="button"],[role="link"],[role="tab"],[role="menuitem"],[tabindex]:not([tabindex="-1"])';
          const els = Array.from(document.querySelectorAll(sel)).filter(
            (el) => {
              const s = getComputedStyle(el);
              return (
                s.display !== "none" &&
                s.visibility !== "hidden" &&
                el.offsetParent !== null
              );
            },
          );
          if (!els[i])
            throw new Error(
              `Element [${i}] not found (${els.length} elements visible)`,
            );
          els[i].setAttribute("data-pw-click", "target");
        }, idx);
        await page.click('[data-pw-click="target"]');
        await page
          .evaluate(() => {
            const el = document.querySelector('[data-pw-click="target"]');
            if (el) el.removeAttribute("data-pw-click");
          })
          .catch(() => {});
      } else {
        await page.click(args[0]);
      }
      if (page.url() !== urlBefore) {
        await page.waitForLoadState("domcontentloaded").catch(() => {});
      } else {
        await page.waitForTimeout(200);
        if (page.url() !== urlBefore) {
          await page.waitForLoadState("domcontentloaded").catch(() => {});
        }
      }
      log(`Page: ${page.url()}`);
      break;
    }

    case "click-text": {
      need(page);
      await page.getByText(args.join(" "), { exact: false }).first().click();
      await page.waitForLoadState("domcontentloaded").catch(() => {});
      log(`Page: ${page.url()}`);
      break;
    }

    case "fill": {
      need(page);
      const [selector, ...rest] = args;
      await page.fill(selector, rest.join(" "));
      log("OK");
      break;
    }

    case "type": {
      need(page);
      const [selector, ...rest] = args;
      await page.type(selector, rest.join(" "));
      log("OK");
      break;
    }

    case "select": {
      need(page);
      await page.selectOption(args[0], args[1]);
      log("OK");
      break;
    }

    case "press": {
      need(page);
      await page.keyboard.press(args[0]);
      log("OK");
      break;
    }

    case "screenshot": {
      need(page);
      const p =
        args.filter((a) => a !== "--full")[0] || "/tmp/pw-screenshot.png";
      await page.screenshot({ path: p, fullPage: args.includes("--full") });
      const fs = require("fs");
      const screenshotBuffer = fs.readFileSync(p);
      const isPng =
        screenshotBuffer[0] === 0x89 && screenshotBuffer[1] === 0x50;
      const isJpeg =
        screenshotBuffer[0] === 0xff && screenshotBuffer[1] === 0xd8;
      if (!isPng && !isJpeg) {
        fs.unlinkSync(p);
        throw new Error(
          "Screenshot produced invalid image file (not PNG/JPEG)",
        );
      }
      log(p);
      break;
    }

    case "eval": {
      need(page);
      const result = await page.evaluate(args.join(" "));
      log(
        typeof result === "string" ? result : JSON.stringify(result, null, 2),
      );
      break;
    }

    case "text": {
      need(page);
      log(await page.evaluate(() => document.body.innerText));
      break;
    }

    case "html": {
      need(page);
      log(await page.content());
      break;
    }

    case "url": {
      need(page);
      log(page.url());
      break;
    }

    case "title": {
      need(page);
      log(await page.title());
      break;
    }

    case "back": {
      need(page);
      await page
        .goBack({ waitUntil: "domcontentloaded", timeout: 5000 })
        .catch(() => {});
      log(`Page: ${page.url()}`);
      break;
    }

    case "forward": {
      need(page);
      await page
        .goForward({ waitUntil: "domcontentloaded", timeout: 5000 })
        .catch(() => {});
      log(`Page: ${page.url()}`);
      break;
    }

    case "scroll": {
      need(page);
      const dir = args[0] || "down";
      const amount = parseInt(args[1]) || 500;
      await page.evaluate(
        ([d, a]) => {
          window.scrollBy(0, d === "up" ? -a : a);
        },
        [dir, amount],
      );
      log(`Scrolled ${dir} ${amount}px`);
      break;
    }

    case "wait": {
      need(page);
      if (args[0] === "--text") {
        await page
          .getByText(args.slice(1).join(" "))
          .waitFor({ timeout: 10000 });
      } else {
        await page.waitForSelector(args[0], { timeout: 10000 });
      }
      log("OK");
      break;
    }

    case "tabs": {
      const pages = b.contexts().flatMap((c) => c.pages());
      if (pages.length === 0) {
        log("No tabs open.");
        break;
      }
      pages.forEach((p, i) => {
        const marker = p === page ? " *" : "";
        log(`[${i}] ${p.url()}${marker}`);
      });
      break;
    }

    case "tab": {
      const pages = b.contexts().flatMap((c) => c.pages());
      const idx = parseInt(args[0]);
      if (!pages[idx])
        throw new Error(`Tab ${idx} not found (${pages.length} tabs)`);
      await pages[idx].bringToFront();
      log(`Page: ${pages[idx].url()}`);
      break;
    }

    case "ping": {
      log("pong");
      break;
    }

    default:
      throw new Error(`Unknown command: ${cmd}. Run: pw help`);
  }

  return output.join("\n");
}

const server = http.createServer((req, res) => {
  let body = "";
  req.on("data", (chunk) => (body += chunk));
  req.on("end", async () => {
    resetIdleTimer();
    try {
      const { cmd, args } = JSON.parse(body);
      const result = await handleCommand(cmd, args || []);
      res.writeHead(200, { "Content-Type": "text/plain" });
      res.end(result);
    } catch (e) {
      res.writeHead(500, { "Content-Type": "text/plain" });
      res.end(e.message);
    }
  });
});

server.listen(DAEMON_PORT, "127.0.0.1", () => {
  resetIdleTimer();
});
