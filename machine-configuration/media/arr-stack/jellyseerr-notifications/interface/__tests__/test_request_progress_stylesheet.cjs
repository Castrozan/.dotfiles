const assert = require("node:assert/strict");
const { createHash } = require("node:crypto");
const { readFileSync } = require("node:fs");
const { createRequire } = require("node:module");
const requireApplication = createRequire("/app/package.json");
const React = requireApplication("react");
const Document = requireApplication(
  "./.next/server/pages/_document.js",
).default;
const stylesheetVersion = createHash("sha256")
  .update(readFileSync("/app/public/request-progress.css"))
  .digest("hex")
  .slice(0, 12);

async function verifyDocumentStyles() {
  const nativeStyle = React.createElement("style", {
    id: "native-styles",
    key: "native-styles",
  });
  const nativeProps = {
    html: "native-page",
    head: ["native-head"],
    styles: [nativeStyle],
  };
  const props = await Document.getInitialProps({
    defaultGetInitialProps: async () => nativeProps,
  });
  assert.equal(props.html, nativeProps.html);
  assert.equal(props.head, nativeProps.head);
  assert.equal(props.styles.length, 2);
  assert.equal(props.styles[0].props.id, "native-styles");
  assert.equal(props.styles[1].type, "link");
  assert.equal(props.styles[1].props.rel, "stylesheet");
  assert.equal(
    props.styles[1].props.href,
    `/request-progress.css?v=${stylesheetVersion}`,
  );
}

verifyDocumentStyles().then(() => {
  console.log(
    "Request-progress stylesheet preserves native styles and versions its URL",
  );
  process.exit(0);
});
