# Addressing decision evaluation

`addressing_evaluation.py` drives the production `VoiceAddressing` path against the live OpenAI Decisions API
(`gpt-6-luna`, 1.5 s timeout) over `addressing-cases.json`: 70 labeled utterances in English, Portuguese and
Japanese, 14 of them held out. Live Servants in every case are Ishtar, Astolfo, Anastasia, Shuten-dōji and Medea; a
case with a holder runs the conversation phase, a case without one runs the wake phase. Candidate names are heard by
the same deterministic gate as production, with the unit tests' ordinary-word list instead of the deployed 50k lists.

Run it by hand, never in CI: `python3 __tests__/live/addressing_evaluation.py` for the tuning set, `--holdout` for the
held-out set.

## Result

Chosen confidence floor: 0.8 (`CONFIDENCE_FLOOR`). On the final wording, candidate choices on utterances that must not
move the floor peaked at 0.46 and real addresses bottomed at 0.90, so 0.8 sits inside that gap on the safe side.

| set | cases | accuracy | false switches | missed addresses | API calls | latency p50 | latency p95 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tuning | 56 | 96.4% | 0 | 2 | 54 | 314 ms | 519 ms |
| held out, run once | 14 | 100.0% | 0 | 0 | 14 | 310 ms | 549 ms |

Both tuning misses are Japanese addresses written in katakana (`ねえシュテン、聞こえる？`, `メデア、テストを実行して`): the
name gate only hears Latin-script names, so no API call was made. Every utterance that reached the API was decided
correctly.

## Tuning history

| run | wording | false switches | missed addresses |
| --- | --- | --- | --- |
| 1 | initial: "turns to it and speaks to it directly" | 2 (en-16, wake-13 relays at 0.93 and 0.92) | 2 (gate) |
| 2 | relays, requests for or about an agent, and singing named as not addressing | 0 | 2 (gate) |
| 3 | unchanged from run 2, repeated to measure variance | 0 | 2 (gate) |

No floor below 0.95 removed the run 1 relay switches, and 0.95 cost three real addresses, so the fix went into the
wording rather than the floor. Runs 2 and 3 made the same choice on every utterance that must not switch.

## Floor sweep on the final tuning run

| floor | false switches | missed addresses |
| --- | --- | --- |
| 0.5 | 0 | 2 |
| 0.6 | 0 | 2 |
| 0.7 | 0 | 2 |
| 0.75 | 0 | 2 |
| 0.8 | 0 | 2 |
| 0.85 | 0 | 2 |
| 0.9 | 0 | 2 |
| 0.95 | 0 | 3 |
| 0.98 | 0 | 5 |

## Tuning set, final run

| case | language | kind | expected | result | choice | confidence | ms | outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| probe-01 | en | wake-word talk | keep | keep | Astolfo | 0.46 | 367 | ok |
| probe-02 | en | address | Astolfo | Astolfo | Astolfo | 1.0 | 297 | ok |
| probe-03 | en | address | Anastasia | Anastasia | Anastasia | 1.0 | 283 | ok |
| probe-04 | en | singing | keep | keep | holder | 0.28 | 317 | ok |
| probe-05 | en | past tense | keep | keep | holder | 0.93 | 478 | ok |
| probe-06 | en | address | Anastasia | Anastasia | Anastasia | 0.97 | 357 | ok |
| probe-07 | pt | relay | keep | keep | holder | 0.8 | 277 | ok |
| probe-08 | pt | address | Astolfo | Astolfo | Astolfo | 1.0 | 292 | ok |
| probe-09 | ja | address | Shuten | keep | no candidate heard | - | - | MISSED |
| probe-10 | en | relay | keep | keep | holder | 0.79 | 303 | ok |
| en-01 | en | address | Medea | Medea | Medea | 1.0 | 283 | ok |
| en-02 | en | address | Medea | Medea | Medea | 0.99 | 310 | ok |
| en-03 | en | mention | keep | keep | holder | 0.97 | 301 | ok |
| en-05 | en | relay | keep | keep | holder | 0.93 | 346 | ok |
| en-06 | en | wake-word talk | keep | keep | nobody | 0.11 | 429 | ok |
| en-07 | en | wake-word talk | keep | keep | holder | 0.64 | 356 | ok |
| en-09 | en | address | Shuten | Shuten | Shuten | 1.0 | 291 | ok |
| en-10 | en | address | Medea | Medea | Medea | 0.99 | 353 | ok |
| en-12 | en | past tense | keep | keep | holder | 0.91 | 288 | ok |
| en-13 | en | singing | keep | keep | nobody | 0.48 | 287 | ok |
| en-14 | en | thinking aloud | keep | keep | holder | 0.27 | 270 | ok |
| en-16 | en | relay | keep | keep | holder | 0.86 | 300 | ok |
| en-17 | en | address | Anastasia | Anastasia | Anastasia | 1.0 | 428 | ok |
| en-18 | en | talking to a person | keep | keep | holder | 0.89 | 302 | ok |
| ctx-01 | en | wake-word talk | keep | keep | holder | 0.7 | 375 | ok |
| ctx-02 | en | address | Medea | Medea | Medea | 1.0 | 318 | ok |
| ctx-04 | en | address | Shuten | Shuten | Shuten | 1.0 | 321 | ok |
| ctx-05 | en | relay | keep | keep | holder | 0.66 | 293 | ok |
| ctx-06 | pt | singing | keep | keep | nobody | 0.46 | 293 | ok |
| pt-01 | pt | address | Medea | Medea | Medea | 1.0 | 365 | ok |
| pt-02 | pt | address | Anastasia | Anastasia | Anastasia | 0.99 | 288 | ok |
| pt-03 | pt | past tense | keep | keep | holder | 0.61 | 300 | ok |
| pt-05 | pt | address | Shuten | Shuten | Shuten | 1.0 | 279 | ok |
| pt-06 | pt | thinking aloud | keep | keep | holder | 0.96 | 320 | ok |
| pt-07 | pt | past tense | keep | keep | holder | 0.96 | 277 | ok |
| pt-09 | pt | wake-word talk | keep | keep | Astolfo | 0.25 | 295 | ok |
| ja-01 | ja | address | Medea | Medea | Medea | 0.99 | 407 | ok |
| ja-02 | ja | past tense | keep | keep | holder | 0.89 | 297 | ok |
| ja-03 | ja | relay | keep | keep | holder | 0.7 | 465 | ok |
| ja-05 | ja | singing | keep | keep | nobody | 0.49 | 319 | ok |
| ja-06 | ja | address | Medea | Medea | Medea | 0.97 | 410 | ok |
| ja-08 | ja | address | Medea | keep | no candidate heard | - | - | MISSED |
| wake-01 | en | address | Anastasia | Anastasia | Anastasia | 1.0 | 351 | ok |
| wake-02 | en | mention | nobody | nobody | nobody | 0.1 | 309 | ok |
| wake-03 | en | address | Medea | Medea | Medea | 0.98 | 353 | ok |
| wake-05 | en | address | Shuten | Shuten | Shuten | 1.0 | 285 | ok |
| wake-06 | pt | address | Medea | Medea | Medea | 1.0 | 321 | ok |
| wake-07 | pt | mention | nobody | nobody | Medea | 0.46 | 376 | ok |
| wake-09 | en | talking to a person | nobody | nobody | nobody | 0.6 | 347 | ok |
| wake-10 | ja | address | Ishtar | Ishtar | Ishtar | 0.98 | 358 | ok |
| wake-11 | en | singing | nobody | nobody | nobody | 0.76 | 286 | ok |
| wake-13 | en | relay | nobody | nobody | Medea | 0.34 | 641 | ok |
| wake-14 | en | address | Anastasia | Anastasia | Anastasia | 0.9 | 283 | ok |
| holder-01 | en | address | Ishtar | Ishtar | Ishtar | 1.0 | 718 | ok |
| holder-02 | en | relay | keep | keep | holder | 0.96 | 279 | ok |
| holder-04 | pt | mention | keep | keep | holder | 0.79 | 391 | ok |

## Held-out set

| case | language | kind | expected | result | choice | confidence | ms | outcome |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| en-04 | en | mention | keep | keep | holder | 0.86 | 377 | ok |
| en-08 | en | wake-word talk | keep | keep | holder | 0.45 | 292 | ok |
| en-11 | en | address | Astolfo | Astolfo | Astolfo | 1.0 | 313 | ok |
| en-15 | en | mention | keep | keep | holder | 0.88 | 405 | ok |
| ctx-03 | en | mention | keep | keep | holder | 0.89 | 303 | ok |
| ctx-07 | pt | address | Shuten | Shuten | Shuten | 1.0 | 298 | ok |
| pt-04 | pt | relay | keep | keep | holder | 0.89 | 368 | ok |
| pt-08 | pt | address | Medea | Medea | Medea | 0.99 | 520 | ok |
| ja-04 | ja | address | Anastasia | Anastasia | Anastasia | 0.99 | 272 | ok |
| ja-07 | ja | wake-word talk | keep | keep | holder | 0.56 | 355 | ok |
| wake-04 | en | mention | nobody | nobody | Astolfo | 0.2 | 306 | ok |
| wake-08 | en | address | Ishtar | Ishtar | Ishtar | 1.0 | 320 | ok |
| wake-12 | en | wake-word talk | nobody | nobody | Astolfo | 0.12 | 286 | ok |
| holder-03 | en | address | Anastasia | Anastasia | Anastasia | 0.98 | 299 | ok |
