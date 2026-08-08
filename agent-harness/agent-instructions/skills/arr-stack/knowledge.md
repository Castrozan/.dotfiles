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

<kavita_names_series_from_the_filename_until_the_library_reads_embedded_metadata>
Suwayomi names every archive after the scanlation group before the chapter, and Kavita parses a series name out of the
filename ahead of the containing folder, so a library created with embedded metadata reading off shows each series named
after the scanlation group instead of the title. Suwayomi exposes no setting for the download filename pattern, so do
not hunt for one; it does write a correct `ComicInfo.xml` into every archive, and switching the library to read embedded
metadata is what recovers the real titles. Delete the mis-parsed series before the forced rescan rather than trusting
the rescan to rename it in place.
</kavita_names_series_from_the_filename_until_the_library_reads_embedded_metadata>

<a_newly_declared_front_end_does_not_start_on_the_rebuild_that_declares_it>
The unit that runs compose up for the always-on front ends is declared neither to restart nor to stop when it changes,
and to remain after exit, so a rebuild that adds a front end leaves it resting on the start script it already ran and
the new container simply never appears, with no failed unit and no error anywhere. Bring the one missing service up
against the deployed compose file, env file and project name instead of restarting that unit, whose stop step tears
down the entire on-demand download chain and interrupts live torrents. The container spec still comes wholly from the
repo, so that is convergence rather than drift.
</a_newly_declared_front_end_does_not_start_on_the_rebuild_that_declares_it>

<kavita_is_the_one_stack_app_the_repo_provisions_nothing_for>
Nothing here declares Kavita's admin account, its libraries or its settings, so that state exists only inside its config
volume and a wipe loses all of it. Its registration endpoint mints the first administrator on the first call carrying a
valid body, so probing that endpoint creates a real admin rather than describing itself. Library create and update also
require the file group list and the exclude patterns under field names the read response does not use, which is what
makes an update assembled from a read fail validation.
</kavita_is_the_one_stack_app_the_repo_provisions_nothing_for>
