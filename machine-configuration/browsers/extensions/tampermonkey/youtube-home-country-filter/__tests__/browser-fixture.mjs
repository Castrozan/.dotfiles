import { Element } from "./element-fixture.mjs";
import { readFileSync } from "node:fs";
import { createContext, runInContext } from "node:vm";
import { setImmediate } from "node:timers/promises";

const directory = new URL("../", import.meta.url);
const resolverSource = readFileSync(
  new URL("channel-country.js", directory),
  "utf8",
);
const userscriptSource = readFileSync(
  new URL("youtube-home-country-filter.user.js", directory),
  "utf8",
);
export const brazil = "UCKHhA5hN2UohhFDfNXB_cvQ";
export const unitedStates = "UCsBjURrPoezykLs9EqgamOA";
export const unknown = "UCkFSV8HSfJaHYqd4M9K8l7Q";
export const marker = "data-youtube-country-hidden";

export function browser(options = {}) {
  const home = new Element();
  const documentElement = new Element();
  const events = new Map();
  const observers = [];
  const requests = [];
  const storage = new Map(Object.entries(options.storage || {}));
  let now = 1000000;
  const context = createContext({
    Element,
    Intl,
    AbortSignal,
    console,
    Date: class extends Date {
      static now() {
        return now;
      }
    },
    location: { pathname: options.pathname || "/" },
    window: { ytcfg: { get: () => "2.20260911.08.00" } },
    localStorage: {
      getItem: (key) => storage.get(key),
      setItem: (key, value) => {
        if (options.storageDenied) throw new Error("Storage denied");
        storage.set(key, value);
      },
    },
    document: {
      head: new Element(),
      documentElement,
      createElement: () => new Element(),
      querySelector: () => home,
      addEventListener: (name, callback) => events.set(name, callback),
    },
    IntersectionObserver: class {
      constructor(callback) {
        this.callback = callback;
        this.observed = new Set();
        observers.push(this);
      }
      observe(target) {
        this.observed.add(target);
      }
      unobserve(target) {
        this.observed.delete(target);
      }
      disconnect() {
        this.observed.clear();
      }
    },
    MutationObserver: class {
      constructor(callback) {
        this.callback = callback;
        observers.push(this);
      }
      observe() {
        this.active = true;
      }
      disconnect() {
        this.active = false;
      }
    },
    fetch: async (url, request) => {
      const body = JSON.parse(request.body);
      requests.push({ url, ...request, body });
      if (options.fetch) return options.fetch(body, requests.length);
      const data = body.browseId
        ? {
            header: {
              description: { continuationCommand: { token: body.browseId } },
            },
          }
        : {
            onResponseReceivedEndpoints: [
              {
                appendContinuationItemsAction: {
                  continuationItems: [
                    {
                      aboutChannelRenderer: {
                        metadata: {
                          aboutChannelViewModel: {
                            channelId: body.continuation,
                            country: (options.countries || {
                              [brazil]: "Brazil",
                              [unitedStates]: "United States",
                            })[body.continuation],
                          },
                        },
                      },
                    },
                  ],
                },
              },
            ],
          };
      return { ok: true, json: async () => data };
    },
  });
  for (const card of options.cards || []) home.append(card);
  runInContext(resolverSource, context);
  const resolver = runInContext("youtubeChannelCountries", context);
  if (options.userscript !== false) runInContext(userscriptSource, context);
  return {
    context,
    home,
    documentElement,
    requests,
    resolver,
    storage,
    advance: (milliseconds) => {
      now += milliseconds;
    },
    visible: (...cards) =>
      observers[0].callback(
        cards.map((target) => ({ target, isIntersecting: true })),
      ),
    mutate: (target, addedNodes = [], removedNodes = []) => {
      if (observers[1].active)
        observers[1].callback([{ target, addedNodes, removedNodes }]);
    },
    navigate: (pathname) => {
      events.get("yt-navigate-start")();
      context.location.pathname = pathname;
      events.get("yt-navigate-finish")();
    },
    observed: () => observers[0].observed,
  };
}

export async function settle() {
  for (let count = 0; count < 5; count += 1) await setImmediate();
}
