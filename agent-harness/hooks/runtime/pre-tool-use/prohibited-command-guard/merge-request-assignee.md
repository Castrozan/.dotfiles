# A merge request was about to be opened with no assignee

A merge request or pull request with no assignee is missing from its owner's
queue. Name the assignee in the command that creates it:

    glab mr create --assignee @me ...
    gh pr create --assignee @me ...

`@me` is the account the CLI is authenticated as.

Creating through the REST API takes the numeric user id, which `glab api user`
prints:

    glab api -X POST projects/<id>/merge_requests -F assignee_id=<id> ...

The guard reads the command line only. When the request body lives in a file,
pass `assignee_id` as a field or as a query parameter on the URL, or use
`glab mr create`.

`git push -o merge_request.create` passes untouched, because GitLab assigns
that merge request to whoever pushed.

For a repository where you cannot assign anyone, such as a pull request to a
project you only contribute to, prefix the command with
`MERGE_REQUEST_WITHOUT_ASSIGNEE_SANCTIONED=1`.
