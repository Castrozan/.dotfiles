(() => {
  const { createHash } = require("node:crypto");
  const { readFileSync } = require("node:fs");
  const { createRequire } = require("node:module");
  const requireApplication = createRequire("/app/package.json");
  const React = requireApplication("react");
  const Document = module.exports.default;
  const getInitialProps = Document.getInitialProps;
  const stylesheetVersion = createHash("sha256")
    .update(readFileSync("/app/public/request-progress.css"))
    .digest("hex")
    .slice(0, 12);

  Document.getInitialProps = async function (context) {
    const initialProps = await getInitialProps.call(this, context);
    return {
      ...initialProps,
      styles: [
        ...React.Children.toArray(initialProps.styles),
        React.createElement("link", {
          key: "request-progress",
          rel: "stylesheet",
          href: `/request-progress.css?v=${stylesheetVersion}`,
        }),
      ],
    };
  };
})();
