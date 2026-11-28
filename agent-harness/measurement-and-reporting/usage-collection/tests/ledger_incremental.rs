mod ledger_support;

use ledger_support::{SampleUsage, append_lines, ingest, pricing, report};
use proptest::prelude::*;

fn sample_usage() -> impl Strategy<Value = SampleUsage> {
    (
        0u8..6,
        prop::option::of(0u8..3),
        any::<bool>(),
        0u8..3,
        prop::sample::select(vec!["claude-opus-5-5", "claude-haiku-5-5"]),
        0u32..500,
        0u32..500,
    )
        .prop_map(
            |(message, request, is_sidechain, day, model, input, output)| SampleUsage {
                message,
                request,
                is_sidechain,
                day,
                model,
                input,
                output,
            },
        )
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(64))]

    #[test]
    fn appending_in_any_chunks_reports_what_one_full_read_reports(
        usages in prop::collection::vec(sample_usage(), 1..40),
        cut_points in prop::collection::vec(any::<prop::sample::Index>(), 0..5),
    ) {
        let lines: Vec<String> = usages.iter().map(SampleUsage::line).collect();
        let pricing = pricing();

        let whole = tempfile::tempdir().unwrap();
        let whole_transcript = whole.path().join("session.jsonl");
        append_lines(&whole_transcript, &lines);
        ingest(&whole.path().join("ledger.sqlite3"), &[whole_transcript], &pricing);

        let chunked = tempfile::tempdir().unwrap();
        let chunked_transcript = chunked.path().join("session.jsonl");
        let chunked_ledger = chunked.path().join("ledger.sqlite3");
        let mut boundaries: Vec<usize> = cut_points.iter().map(|cut| cut.index(lines.len() + 1)).collect();
        boundaries.push(lines.len());
        boundaries.sort_unstable();
        let mut written = 0;
        for boundary in boundaries {
            append_lines(&chunked_transcript, &lines[written..boundary]);
            written = boundary;
            ingest(&chunked_ledger, std::slice::from_ref(&chunked_transcript), &pricing);
        }

        prop_assert_eq!(report(&whole.path().join("ledger.sqlite3")), report(&chunked_ledger));
    }

    #[test]
    fn a_copied_transcript_never_counts_twice(
        usages in prop::collection::vec(sample_usage(), 1..40),
    ) {
        let lines: Vec<String> = usages.iter().map(SampleUsage::line).collect();
        let pricing = pricing();
        let directory = tempfile::tempdir().unwrap();
        let original = directory.path().join("original.jsonl");
        let copy = directory.path().join("resumed.jsonl");
        append_lines(&original, &lines);
        append_lines(&copy, &lines);
        let ledger = directory.path().join("ledger.sqlite3");

        ingest(&ledger, std::slice::from_ref(&original), &pricing);
        let before_copy = report(&ledger);
        ingest(&ledger, &[original, copy], &pricing);

        prop_assert_eq!(before_copy, report(&ledger));
    }
}
