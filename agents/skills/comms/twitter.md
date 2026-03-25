<tool_selection>
Single backend: twikit-cli. Supports search, user profiles, tweets, replies, threads, trends, timeline, followers, following, post, like, retweet, bookmark, DM. Run `twikit-cli --help` for all commands.
</tool_selection>

<auth>
Cookie-based auth extracted from Chrome. Cookies (auth_token, ct0) last ~13 months. Run `twikit-cli extract-cookies` to refresh — decrypts cookies from any Chrome/Chromium profile where user is logged into x.com. No manual steps needed beyond being logged in.
</auth>

<troubleshooting>
Auth error or 401: run `twikit-cli extract-cookies`. If that fails with "missing auth_token/ct0", user needs to log into x.com in Chrome first, then re-run extract-cookies. Direct `twikit-cli login` won't work — Cloudflare blocks programmatic login from this IP.
</troubleshooting>
