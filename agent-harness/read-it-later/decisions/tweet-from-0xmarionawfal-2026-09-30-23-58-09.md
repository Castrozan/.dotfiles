# Tweet from 0xMarioNawfal — GhostTrack

Capture: `ReadItLater Inbox/Tweet from 0xMarioNawfal (2026-09-30 23-58-09).md`
Origin: https://x.com/RoundtableSpace/status/2105270969975579109
Linked project: https://github.com/HunxByts/GhostTrack
Verdict: **drop**

## The origin as resolved

Read through the twitter skill with `twikit-cli tweet 2105270969975579109`, not a topic search. The tweet
claims that GhostTrack takes a phone number, finds the platforms where its owner has registered accounts,
and reports IP location and carrier information. Its GitHub shortlink resolves to
`HunxByts/GhostTrack`, so I read the repository README, dependency list and complete program at the current
`main` commit, `a5cb8ad4c08acd803f166fb067b7dac724d6cb3d` (last committed 2024-01-11).

The source does not implement the capability the tweet describes. There is no path from a phone number to
an IP address, account, username or platform lookup, and no service call in the phone-number function.

## What it actually is

GhostTrack is one 11.5 KB interactive Python script with two dependencies, `requests` and `phonenumbers`,
and four independent menu choices:

- **Phone Number Tracker** parses the supplied number locally with Google's libphonenumber data. It prints
  the region, timezones, carrier label, validity, formatting and number type. Those are numbering-plan
  metadata, not live location or information about a subscriber. This is all visible in
  `GhostTR.py:81-118` upstream.
- **IP Tracker** asks for an IP address separately, sends it to `http://ipwho.is/` over unencrypted HTTP and
  prints that service's geolocation and network metadata (`GhostTR.py:40-77`). It does not discover an IP
  from a phone number.
- **Username Tracker** asks for a username separately and treats HTTP 200 responses from a hard-coded list
  of profile URLs as account matches (`GhostTR.py:121-158`). It neither derives the username from a phone
  number nor accounts for sites that return 200 for login walls, rate limits or missing profiles.
- **Show Your IP** calls ipify and prints the caller's own public IP.

The repository declares no license through GitHub and contains no license file. Its latest code commit
predates the capture by more than two years. Popularity does not repair the mismatch between the claim and
the implementation.

## What it touches here

Nothing in the running configuration. A repository-wide search found no GhostTrack, libphonenumber, ipwho
or OSINT integration to extend or replace. The only plausible installation surface would be the general
user package set at
`machine-configuration/machines/user-packages-lucas-zanoni-home-manager.nix:9-105`, but packaging this
script would add a new maintenance and trust surface without adding the advertised capability.

It replaces nothing, deletes nothing and unblocks nothing. This pull request adds only this decision file,
the required reviewable audit trail for a no-code verdict.

## Reasoning

**Drop**, rather than adopt or trial. The strongest reason is not that the tool is small; it is that the
saved claim is false in exactly the part that would make the tool useful. A trial cannot reveal a hidden
phone-to-account capability because the complete source contains no such code path.

The remaining functions do not justify a narrower adoption:

- libphonenumber already supplies the phone metadata, so GhostTrack is only a menu around a mature library;
- the IP lookup requires an IP the operator already has and sends it over plaintext HTTP;
- the username checks are naive status-code probes likely to produce false positives;
- installing an unlicensed, effectively dormant upstream adds provenance and maintenance cost for no local
  workflow named in this repository.

It is not worth filing as a reference either. The useful lesson fits in one sentence: inspect an OSINT
tool's data flow before believing a viral capability claim. The repository itself is not a reliable tool to
return to, and retaining it would soften a discard without preserving actionable knowledge.

## Vault entry

None. A drop files nothing.
