const http = require("http");

function readJsonResponse(response, resolve, reject, fallbackToRawText) {
  let responseBody = "";
  response.on("data", (chunk) => (responseBody += chunk));
  response.on("end", () => {
    try {
      resolve(JSON.parse(responseBody));
    } catch (error) {
      if (fallbackToRawText) {
        resolve(responseBody);
        return;
      }
      reject(error);
    }
  });
}

class ChromeDevtoolsTargetLocator {
  constructor(devtoolsPort) {
    this.devtoolsPort = devtoolsPort;
  }

  baseUrl() {
    return `http://127.0.0.1:${this.devtoolsPort}`;
  }

  get(routePath) {
    return new Promise((resolve, reject) => {
      http
        .get(`${this.baseUrl()}${routePath}`, (response) =>
          readJsonResponse(response, resolve, reject, false),
        )
        .on("error", reject);
    });
  }

  put(routePath, body) {
    return new Promise((resolve, reject) => {
      const payload = JSON.stringify(body);
      const request = http.request(
        `${this.baseUrl()}${routePath}`,
        {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Content-Length": Buffer.byteLength(payload),
          },
        },
        (response) => readJsonResponse(response, resolve, reject, true),
      );
      request.on("error", reject);
      request.end(payload);
    });
  }

  async findPageTarget(urlFragment) {
    const targets = await this.get("/json");
    return targets.find(
      (target) => target.type === "page" && target.url.includes(urlFragment),
    );
  }

  async openTab(tabUrl) {
    return this.put("/json/new", { url: tabUrl });
  }

  async findOrOpenPageTarget(urlFragment, tabUrl, settleMilliseconds = 3000) {
    const existingTarget = await this.findPageTarget(urlFragment);
    if (existingTarget) {
      return existingTarget;
    }

    console.log(`📺 ChatVRM tab not found, opening ${tabUrl}...`);
    await this.openTab(tabUrl);
    await new Promise((resolve) => setTimeout(resolve, settleMilliseconds));
    return this.findPageTarget(urlFragment);
  }
}

module.exports = { ChromeDevtoolsTargetLocator };
