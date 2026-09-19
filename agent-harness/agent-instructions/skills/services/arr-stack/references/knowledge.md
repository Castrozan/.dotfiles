### A request stalls forever on zero active indexers

A request that sits at processing for days with abundant sources available is usually not the scrape pipeline and not
the quality profile. The requester does its job and triggers the on-add search, but if that search runs at a moment when
zero indexers are active it finds nothing, and the arr applications never automatically retry a search that returned no
results. Nothing surfaces this: the request simply stays pending forever. Re-run the search by hand once indexers are
back, and treat a long-pending request as a missed search rather than a broken pipeline.

### A finished download that never imports is a title mismatch

When a grab reaches full completion in the client but the media file never appears, the usual cause is a title mismatch
that blocks automatic import, because the release name parses to a different title than the metadata provider's even
though the same application grabbed it. The trap is diagnostic rather than structural: the blocking queue item is
invisible in the default queue response and appears only when unknown items are explicitly included. Query with that
flag before concluding the queue is empty.

### Credentials that are present but never autofill

A password manager reporting nothing for these applications has, at least once, been a client-side matching setting
rather than a missing entry: a global URI match set to exact silently kills autofill for every URL that carries a path,
which is all of them here. Check the vault contents and the match mode before concluding a credential was never saved.

### Kavita names series from the filename until the library reads embedded metadata

Suwayomi names every archive after the scanlation group before the chapter, and Kavita parses a series name out of the
filename ahead of the containing folder, so a library created with embedded metadata reading off shows each series named
after the scanlation group instead of the title. Suwayomi exposes no setting for the download filename pattern, so do
not hunt for one; it does write a correct `ComicInfo.xml` into every archive, and switching the library to read embedded
metadata is what recovers the real titles. Delete the mis-parsed series before the forced rescan rather than trusting
the rescan to rename it in place.

### Fetching additional data is ffmpeg lifting subtitles out of the container

The spinner the Jellyfin player raises over its transport bar is the client waiting on one subtitle request and nothing
else, so do not read it as metadata, as the requester, or as a plugin. Serving that request runs ffmpeg over the whole
media file to lift every embedded text track out of the container, so the wait tracks file size rather than subtitle
size and costs tens of seconds off a spinning disk.

The extraction is cached per file forever, which is why the stall hits only whoever opens a title first and never
reproduces on a second try. Paying that in advance is what the subtitle extraction warmer module is for, so when the
spinner returns read its unit log before suspecting the player: a sweep that deferred to live playback and a genuinely
new file are indistinguishable from the client side.

### Logging into a source means driving the browser that lives inside the server

Suwayomi's WebView runs a full Chromium inside the server process and streams it to a canvas in your browser, so cookies
a login leaves behind land in the jar the source extensions fetch with. That is what makes a members-only source work,
and what clears a Cloudflare interstitial while FlareSolverr is off. Reach it from the globe icon on a source or manga
page. Check the source's own settings first: many carry their login there and need no browser at all.

### The web view chromium is downloaded at runtime so nixos resolves none of its libraries

The server fetches a prebuilt Chromium into its data directory on first start, so nix never patches it and it links
against two dozen libraries this machine keeps only in the store. Without a library search path on the unit it dies on
an UnsatisfiedLinkError for libglib and takes the WebView with it, while the rest of the server stays healthy and
nothing but one startup stack trace says so. The manga module declares that path; when the WebView goes dark after an
upstream Chromium bump, `ldd` the downloaded `libcef.so` for newly missing sonames rather than suspecting the server.

### Kavita is the one stack app the repo provisions nothing for

Nothing here declares Kavita's admin account, its libraries or its settings, so that state exists only inside its config
volume and a wipe loses all of it. Its registration endpoint mints the first administrator on the first call carrying a
valid body, so probing that endpoint creates a real admin rather than describing itself. Library create and update also
require the file group list and the exclude patterns under field names the read response does not use, which is what
makes an update assembled from a read fail validation.
