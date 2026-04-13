<tool_selection>
Single backend: twikit-cli. Supports search, user profiles, tweets, replies, threads, trends, timeline, followers, following, post, like, retweet, bookmark, DM. Run `twikit-cli --help` for all commands.
</tool_selection>

<auth>
Cookie-based auth extracted from Chrome. Cookies (auth_token, ct0) last ~13 months. Run `twikit-cli extract-cookies` to refresh — decrypts cookies from any Chrome/Chromium profile where user is logged into x.com. No manual steps needed beyond being logged in.
</auth>

<troubleshooting>
Auth error or 401: run `twikit-cli extract-cookies`. If that fails with "missing auth_token/ct0", user needs to log into x.com in Chrome first, then re-run extract-cookies. Direct `twikit-cli login` won't work - Cloudflare blocks programmatic login from this IP.
</troubleshooting>

<failure_modes>
`twikit-cli tweet <id>` is unreliable - fails with KeyError/itemContent on some individual tweets. Use `twikit-cli user-tweets` or `twikit-cli search` for discovery. For single-tweet data extraction when twikit fails, use the fxtwitter fallback below.
</failure_modes>

<fxtwitter_fallback>
Read-only public API for tweet data + media URLs. No auth needed. Use as fallback when `twikit-cli tweet` fails, or when you need direct media URLs (images, videos).

`curl -sL "https://api.fxtwitter.com/{user}/status/{tweet_id}"` returns JSON with tweet text, media array with URLs, and engagement metrics. Download media with `curl -sL -o /tmp/image.jpg "{media_url}"`.
</fxtwitter_fallback>
