mod ledger_support;

use std::io::Write;

use claude_usage_collector::pricing::PricingTable;
use ledger_support::{SampleUsage, append_lines, ingest, pricing, report};

fn usage(message: u8, request: Option<u8>, is_sidechain: bool, output: u32) -> SampleUsage {
    SampleUsage {
        message,
        request,
        is_sidechain,
        day: 0,
        model: "claude-opus-5-5",
        input: 10,
        output,
    }
}

fn reported_output_tokens(ledger: &std::path::Path) -> Vec<u64> {
    report(ledger)
        .iter()
        .map(|usage| usage.totals.output_tokens)
        .collect()
}

#[test]
fn keeps_the_streamed_line_with_the_most_tokens() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    append_lines(
        &transcript,
        &[
            usage(1, Some(1), false, 5).line(),
            usage(1, Some(1), false, 300).line(),
        ],
    );
    ingest(&ledger, std::slice::from_ref(&transcript), &pricing());
    append_lines(&transcript, &[usage(1, Some(1), false, 40).line()]);
    ingest(&ledger, &[transcript], &pricing());
    assert_eq!(reported_output_tokens(&ledger), vec![300]);
}

#[test]
fn prefers_the_main_conversation_over_a_sidechain_replay() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    append_lines(
        &transcript,
        &[
            usage(2, Some(1), true, 900).line(),
            usage(2, Some(7), false, 20).line(),
        ],
    );
    ingest(&ledger, &[transcript], &pricing());
    assert_eq!(reported_output_tokens(&ledger), vec![20]);
}

#[test]
fn counts_distinct_requests_of_one_message_separately() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    append_lines(
        &transcript,
        &[
            usage(3, Some(1), false, 20).line(),
            usage(3, Some(2), false, 30).line(),
        ],
    );
    ingest(&ledger, &[transcript], &pricing());
    assert_eq!(reported_output_tokens(&ledger), vec![50]);
}

#[test]
fn waits_for_a_partial_line_to_finish_before_counting_it() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    let line = usage(4, Some(1), false, 70).line();
    let (head, tail) = line.split_at(line.len() / 2);
    std::fs::write(&transcript, head).unwrap();
    assert_eq!(
        ingest(&ledger, std::slice::from_ref(&transcript), &pricing()),
        0
    );
    let mut file = std::fs::OpenOptions::new()
        .append(true)
        .open(&transcript)
        .unwrap();
    writeln!(file, "{tail}").unwrap();
    assert_eq!(ingest(&ledger, &[transcript], &pricing()), 1);
    assert_eq!(reported_output_tokens(&ledger), vec![70]);
}

#[test]
fn rereads_a_replaced_transcript_without_counting_it_twice() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    append_lines(
        &transcript,
        &[
            usage(5, Some(1), false, 10).line(),
            usage(6, Some(1), false, 20).line(),
        ],
    );
    ingest(&ledger, std::slice::from_ref(&transcript), &pricing());
    let rewritten = directory.path().join("rewritten.jsonl");
    append_lines(
        &rewritten,
        &[
            usage(6, Some(1), false, 20).line(),
            usage(7, Some(1), false, 40).line(),
        ],
    );
    std::fs::rename(&rewritten, &transcript).unwrap();
    ingest(&ledger, &[transcript], &pricing());
    assert_eq!(reported_output_tokens(&ledger), vec![70]);
}

#[test]
fn reprices_recorded_usage_when_the_price_list_changes() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    append_lines(&transcript, &[usage(8, Some(1), false, 1_000).line()]);
    ingest(&ledger, std::slice::from_ref(&transcript), &pricing());
    let doubled_output_price = ledger_support::PRICING_DOCUMENT.replace("2e-5", "4e-5");
    let repriced = PricingTable::from_litellm_document(doubled_output_price.as_bytes()).unwrap();
    assert_eq!(ingest(&ledger, &[transcript], &repriced), 0);
    let cost = report(&ledger)[0].totals.cost_usd;
    assert!(
        (cost - (10.0 * 4e-6 + 1_000.0 * 4e-5)).abs() < 1e-12,
        "{cost}"
    );
}

#[test]
fn counts_every_line_that_has_no_message_id() {
    let directory = tempfile::tempdir().unwrap();
    let transcript = directory.path().join("session.jsonl");
    let ledger = directory.path().join("ledger.sqlite3");
    let line = r#"{"timestamp":"2026-11-10T12:00:00Z","message":{"model":"claude-opus-5-5","usage":{"input_tokens":1,"output_tokens":9}}}"#;
    append_lines(&transcript, &[line.to_string(), line.to_string()]);
    ingest(&ledger, &[transcript], &pricing());
    assert_eq!(reported_output_tokens(&ledger), vec![18]);
}
