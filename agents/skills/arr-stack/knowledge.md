<a_request_stalls_forever_on_zero_active_indexers>
A request that sits at processing for days with abundant sources available is usually not the scrape pipeline and not
the quality profile. The requester does its job and triggers the on-add search, but if that search runs at a moment
when zero indexers are active it finds nothing, and the arr applications never automatically retry a search that
returned no results. Nothing surfaces this: the request simply stays pending forever. Re-run the search by hand once
indexers are back, and treat a long-pending request as a missed search rather than a broken pipeline.
</a_request_stalls_forever_on_zero_active_indexers>

<a_finished_download_that_never_imports_is_a_title_mismatch>
When a grab reaches full completion in the client but the media file never appears, the usual cause is a title mismatch
that blocks automatic import, because the release name parses to a different title than the metadata provider's even
though the same application grabbed it. The trap is diagnostic rather than structural: the blocking queue item is
invisible in the default queue response and appears only when unknown items are explicitly included. Query with that
flag before concluding the queue is empty.
</a_finished_download_that_never_imports_is_a_title_mismatch>

<credentials_that_are_present_but_never_autofill>
A password manager reporting nothing for these applications has, at least once, been a client-side matching setting
rather than a missing entry: a global URI match set to exact silently kills autofill for every URL that carries a path,
which is all of them here. Check the vault contents and the match mode before concluding a credential was never saved.
</credentials_that_are_present_but_never_autofill>
