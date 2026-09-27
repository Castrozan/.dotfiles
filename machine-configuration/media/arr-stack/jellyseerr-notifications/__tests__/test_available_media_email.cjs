const assert = require("node:assert/strict");
const { createRequire } = require("node:module");
const requireApplication = createRequire("/app/package.json");
const { getSettings } = requireApplication("./dist/lib/settings");
const EmailAgent = requireApplication(
  "./dist/lib/notifications/agents/email",
).default;
const { Notification } = requireApplication("./dist/lib/notifications");
const { renderFile } = requireApplication("pug");

const settings = getSettings();
const applicationUrl = "https://requests.example.invalid";
const watchUrl = "https://watch.lucaszanoni.com/web/#/home";
settings.main.applicationUrl = applicationUrl;
settings.main.applicationTitle = "Jellyseerr";
const agent = new EmailAgent();

function buildMessage(type, payload) {
  return agent.buildMessage(type, payload, "friend@example.invalid", "Friend");
}

function renderMessage(message) {
  return renderFile(`${message.template}/html.pug`, message.locals);
}

for (const mediaType of ["movie", "tv"]) {
  for (const is4k of [false, true]) {
    const payload = {
      media: { mediaType, tmdbId: 94664 },
      request: { is4k, requestedBy: { displayName: "Friend" } },
      subject: "Requested title",
      image: "https://images.example.invalid/poster.jpg",
    };
    const available = buildMessage(Notification.MEDIA_AVAILABLE, payload);
    assert.equal(available.locals.actionUrl, watchUrl);
    assert.equal(available.locals.applicationUrl, applicationUrl);
    const html = renderMessage(available);
    assert.equal(html.split(`href="${watchUrl}"`).length - 1, 3);
    assert.ok(html.includes("Watch in Jellyfin"));
    assert.ok(!html.includes(`${applicationUrl}/${mediaType}/94664`));

    for (const type of [
      Notification.MEDIA_PENDING,
      Notification.MEDIA_APPROVED,
      Notification.MEDIA_AUTO_APPROVED,
      Notification.MEDIA_AUTO_REQUESTED,
      Notification.MEDIA_DECLINED,
      Notification.MEDIA_FAILED,
    ]) {
      const message = buildMessage(type, payload);
      assert.equal(
        message.locals.actionUrl,
        `${applicationUrl}/${mediaType}/94664`,
      );
      const html = renderMessage(message);
      assert.ok(html.includes("View Media in Jellyseerr"));
      assert.ok(!html.includes(watchUrl));
    }

    settings.main.applicationUrl = "";
    assert.equal(
      buildMessage(Notification.MEDIA_AVAILABLE, payload).locals.actionUrl,
      watchUrl,
    );
    assert.equal(
      buildMessage(Notification.MEDIA_PENDING, payload).locals.actionUrl,
      undefined,
    );
    settings.main.applicationUrl = applicationUrl;
  }
}

const issue = buildMessage(Notification.ISSUE_CREATED, {
  issue: { id: 42, issueType: 1, createdBy: { displayName: "Friend" } },
});
assert.equal(issue.locals.actionUrl, `${applicationUrl}/issues/42`);
const test = buildMessage(Notification.TEST_NOTIFICATION, { message: "Test" });
assert.equal(test.locals.applicationUrl, applicationUrl);
assert.ok(!renderMessage(test).includes(watchUrl));
assert.equal(buildMessage(Notification.MEDIA_AVAILABLE, {}), undefined);
console.log(
  "Available-media email links and other notification routes verified",
);
process.exit(0);
