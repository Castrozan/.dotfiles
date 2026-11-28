use claude_usage_collector::transcript::{MessageIdentity, TokenCounts, parse_usage_entry};

fn assistant_line(message: &str) -> String {
    format!(
        r#"{{"type":"assistant","timestamp":"2026-11-20T10:00:00.000Z","requestId":"req_1","message":{message}}}"#
    )
}

#[test]
fn reads_tokens_identity_and_utc_day_from_an_assistant_line() {
    let line = r#"{"timestamp":"2026-01-02T01:00:00.000+02:00","requestId":"req_9","isSidechain":true,"message":{"id":"msg_9","model":"claude-opus-5-5","usage":{"input_tokens":3,"output_tokens":5,"cache_creation_input_tokens":7,"cache_read_input_tokens":11}}}"#;
    let entry = parse_usage_entry(line).unwrap();
    assert_eq!(entry.usage_date, "2026-01-01");
    assert_eq!(
        entry.identity,
        Some(MessageIdentity {
            message_id: "msg_9".into(),
            request_id: Some("req_9".into())
        })
    );
    assert!(entry.is_sidechain);
    assert_eq!(
        entry.tokens,
        TokenCounts {
            input: 3,
            output: 5,
            cache_creation_five_minute: 7,
            cache_creation_one_hour: 0,
            cache_read: 11
        }
    );
}

#[test]
fn splits_cache_creation_by_lifetime_when_the_breakdown_is_present() {
    let line = assistant_line(
        r#"{"id":"m","model":"claude-sonnet-5-5","usage":{"input_tokens":1,"output_tokens":1,"cache_creation_input_tokens":999,"cache_creation":{"ephemeral_5m_input_tokens":200,"ephemeral_1h_input_tokens":800}}}"#,
    );
    let tokens = parse_usage_entry(&line).unwrap().tokens;
    assert_eq!(
        (
            tokens.cache_creation_five_minute,
            tokens.cache_creation_one_hour
        ),
        (200, 800)
    );
}

#[test]
fn labels_fast_mode_as_its_own_model() {
    let line = assistant_line(
        r#"{"id":"m","model":"claude-opus-5-5","usage":{"input_tokens":1,"output_tokens":1,"speed":"fast"}}"#,
    );
    let entry = parse_usage_entry(&line).unwrap();
    assert!(entry.is_fast);
    assert_eq!(entry.model_label(), "claude-opus-5-5-fast");
}

#[test]
fn reads_agent_progress_lines() {
    let line = r#"{"type":"progress","data":{"message":{"timestamp":"2026-11-20T23:59:59Z","requestId":"req_p","message":{"id":"msg_p","model":"claude-haiku-5-5","usage":{"input_tokens":4,"output_tokens":2}}}}}"#;
    let entry = parse_usage_entry(line).unwrap();
    assert_eq!(
        (entry.model.as_str(), entry.usage_date.as_str()),
        ("claude-haiku-5-5", "2026-11-20")
    );
    assert_eq!(entry.identity.unwrap().request_id.as_deref(), Some("req_p"));
}

#[test]
fn skips_lines_without_a_billable_model() {
    for model in [r#""model":"<synthetic>","#, r#""model":"","#, ""] {
        let line = assistant_line(&format!(
            r#"{{"id":"m",{model}"usage":{{"input_tokens":1,"output_tokens":1}}}}"#
        ));
        assert_eq!(parse_usage_entry(&line), None, "{line}");
    }
}

#[test]
fn skips_lines_that_are_not_usage_records() {
    assert_eq!(
        parse_usage_entry(r#"{"type":"user","message":{"role":"user"}}"#),
        None
    );
    assert_eq!(parse_usage_entry(r#"{"usage":{ not json"#), None);
    let missing_output =
        assistant_line(r#"{"id":"m","model":"claude-opus-5-5","usage":{"input_tokens":1}}"#);
    assert_eq!(parse_usage_entry(&missing_output), None);
}

#[test]
fn keeps_a_reported_cost_and_a_missing_request_id() {
    let line = r#"{"timestamp":"2026-11-20T10:00:00Z","costUSD":0.25,"message":{"id":"msg_1","model":"claude-opus-5-5","usage":{"input_tokens":1,"output_tokens":1}}}"#;
    let entry = parse_usage_entry(line).unwrap();
    assert_eq!(entry.reported_cost_usd, Some(0.25));
    assert_eq!(entry.identity.unwrap().request_id, None);
}

#[test]
fn accepts_null_fields_that_the_entry_does_not_need() {
    let line = r#"{"timestamp":"2026-11-20T10:00:00Z","requestId":null,"costUSD":null,"isApiErrorMessage":null,"message":{"id":"msg_1","model":"claude-opus-5-5","content":[{"id":null}],"usage":{"input_tokens":1,"output_tokens":2,"cache_read_input_tokens":null}}}"#;
    let entry = parse_usage_entry(line).unwrap();
    assert_eq!(entry.tokens.total(), 3);
    assert_eq!(entry.reported_cost_usd, None);
}
