// pw.js — Fast persistent browser automation via Playwright + CDP
// Chrome lifecycle managed by pw.sh wrapper.

const { chromium } = require("playwright");
const PW_PORT = process.env.PW_PORT || "9222";

async function main() {
  const [cmd, ...args] = process.argv.slice(2);

  if (!cmd) {
    console.error("No command. Run: pw help");
    process.exit(1);
  }

  let browser;
  try {
    browser = await chromium.connectOverCDP(`http://127.0.0.1:${PW_PORT}`);
  } catch {
    console.error("No browser running. Run: pw open <url>");
    process.exit(1);
  }

  let page = getActivePage(browser);

  try {
    switch (cmd) {
      case "open":
      case "navigate": {
        const isNew = args.includes("--new");
        const url = args.filter((a) => a !== "--new")[0];
        if (!url) {
          console.error("Usage: pw open <url>");
          process.exit(1);
        }
        if (!page || isNew) {
          const ctx = browser.contexts()[0] || (await browser.newContext());
          page = await ctx.newPage();
        }
        await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
        console.log(`Page: ${page.url()}`);
        console.log(`Title: ${await page.title()}`);
        break;
      }

      case "snap":
      case "snapshot": {
        need(page);
        const tree = await page.locator("body").ariaSnapshot();
        console.log(tree);
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
              if (el.type && el.type !== "submit")
                parts.push(`type=${el.type}`);
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
        els.forEach((e) => console.log(e));
        break;
      }

      case "click": {
        need(page);
        const urlBefore = page.url();
        if (/^\d+$/.test(args[0])) {
          const idx = parseInt(args[0]);
          // Get the element's info and build a Playwright selector
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
            // Mark the element with a temporary attribute for Playwright to find
            els[i].setAttribute("data-pw-click", "target");
          }, idx);
          // Use Playwright's native click (triggers navigation detection)
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
        // Wait for potential navigation
        if (page.url() !== urlBefore) {
          await page.waitForLoadState("domcontentloaded").catch(() => {});
        } else {
          // Give a moment for navigation to start
          await page.waitForTimeout(200);
          if (page.url() !== urlBefore) {
            await page.waitForLoadState("domcontentloaded").catch(() => {});
          }
        }
        console.log(`Page: ${page.url()}`);
        break;
      }

      case "click-text": {
        need(page);
        await page.getByText(args.join(" "), { exact: false }).first().click();
        await page.waitForLoadState("domcontentloaded").catch(() => {});
        console.log(`Page: ${page.url()}`);
        break;
      }

      case "fill": {
        need(page);
        const [selector, ...rest] = args;
        await page.fill(selector, rest.join(" "));
        console.log("OK");
        break;
      }

      case "type": {
        need(page);
        const [selector, ...rest] = args;
        await page.type(selector, rest.join(" "));
        console.log("OK");
        break;
      }

      case "select": {
        need(page);
        await page.selectOption(args[0], args[1]);
        console.log("OK");
        break;
      }

      case "press": {
        need(page);
        await page.keyboard.press(args[0]);
        console.log("OK");
        break;
      }

      case "screenshot": {
        need(page);
        const p =
          args.filter((a) => a !== "--full")[0] || "/tmp/pw-screenshot.png";
        await page.screenshot({ path: p, fullPage: args.includes("--full") });
        console.log(p);
        break;
      }

      case "eval": {
        need(page);
        const result = await page.evaluate(args.join(" "));
        console.log(
          typeof result === "string" ? result : JSON.stringify(result, null, 2),
        );
        break;
      }

      case "text": {
        need(page);
        console.log(await page.evaluate(() => document.body.innerText));
        break;
      }

      case "html": {
        need(page);
        console.log(await page.content());
        break;
      }

      case "url": {
        need(page);
        console.log(page.url());
        break;
      }

      case "title": {
        need(page);
        console.log(await page.title());
        break;
      }

      case "back": {
        need(page);
        await page
          .goBack({ waitUntil: "domcontentloaded", timeout: 5000 })
          .catch(() => {});
        console.log(`Page: ${page.url()}`);
        break;
      }

      case "forward": {
        need(page);
        await page
          .goForward({ waitUntil: "domcontentloaded", timeout: 5000 })
          .catch(() => {});
        console.log(`Page: ${page.url()}`);
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
        console.log(`Scrolled ${dir} ${amount}px`);
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
        console.log("OK");
        break;
      }

      case "tabs": {
        const pages = browser.contexts().flatMap((c) => c.pages());
        if (pages.length === 0) {
          console.log("No tabs open.");
          break;
        }
        pages.forEach((p, i) => {
          const marker = p === page ? " *" : "";
          console.log(`[${i}] ${p.url()}${marker}`);
        });
        break;
      }

      case "tab": {
        const pages = browser.contexts().flatMap((c) => c.pages());
        const idx = parseInt(args[0]);
        if (!pages[idx]) {
          console.error(`Tab ${idx} not found (${pages.length} tabs)`);
          process.exit(1);
        }
        await pages[idx].bringToFront();
        console.log(`Page: ${pages[idx].url()}`);
        break;
      }

      default:
        console.error(`Unknown command: ${cmd}. Run: pw help`);
        process.exit(1);
    }
  } catch (e) {
    console.error(`Error: ${e.message}`);
    process.exit(1);
  }

  process.exit(0);
}

function getActivePage(browser) {
  const allPages = browser.contexts().flatMap((c) => c.pages());
  if (allPages.length === 0) return null;
  const urlMatch = process.env.PW_TAB_URL;
  if (urlMatch) {
    const match = allPages.find((p) => p.url().includes(urlMatch));
    if (match) return match;
  }
  return allPages[allPages.length - 1];
}

function need(page) {
  if (!page) {
    console.error("No page open. Run: pw open <url>");
    process.exit(1);
  }
}

main();
