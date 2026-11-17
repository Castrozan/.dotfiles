# A merge request was about to be opened on Betha's GitLab with no assignee

A merge request with no assignee is missing from its owner's queue. Name the
assignee in the command that creates it:

    glab mr create --assignee @me ...

`@me` is the account the CLI is authenticated as.

Creating through the REST API takes the numeric user id, which `glab api user`
prints:

    glab api -X POST projects/<id>/merge_requests -F assignee_id=<id> ...

The guard reads the command line only. When the request body lives in a file,
pass `assignee_id` as a field or as a query parameter on the URL, or use
`glab mr create`.

`git push -o merge_request.create` passes untouched, because GitLab assigns
that merge request to whoever pushed.

## Where the guard applies

Only a creation aimed at `gitlab.services.betha.cloud` is held. `gh pr create`,
every other GitLab host, and a target the guard cannot read all pass.

The guard reads the target the way `glab` picks it, and the first of these that
answers decides:

1. A host named on the command: a `-R`/`--repo` URL, `--hostname`, or the
   address of the request. A `curl` call is judged by its address alone.
2. `GITLAB_HOST` or `GL_HOST`, set on the command, exported earlier in it, or
   inherited by the session. `gitlab.com` there overrides nothing.
3. The git remotes of the directory the command runs in, following any `cd` in
   the same command and resolving SSH host aliases. One Betha remote is enough.
4. Outside any checkout, the host `glab config get host` prints.

For a Betha repository where you cannot assign anyone, prefix the command with
`MERGE_REQUEST_WITHOUT_ASSIGNEE_SANCTIONED=1`.
