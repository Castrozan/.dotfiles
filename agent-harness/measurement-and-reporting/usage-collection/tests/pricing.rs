use claude_usage_collector::pricing::PricingTable;
use claude_usage_collector::transcript::TokenCounts;

const PRICING_DOCUMENT: &str = r#"{
    "sample_spec": {"input_cost_per_token": 0},
    "claude-opus-5-5": {
        "input_cost_per_token": 4e-6, "output_cost_per_token": 2e-5,
        "cache_creation_input_token_cost": 5e-6, "cache_creation_input_token_cost_above_1hr": 8e-6,
        "cache_read_input_token_cost": 2e-7, "provider_specific_entry": {"fast": 2}
    },
    "claude-sonnet-4-20250514": {
        "input_cost_per_token": 3e-6, "output_cost_per_token": 1.5e-5,
        "input_cost_per_token_above_200k_tokens": 6e-6
    },
    "claude-haiku-5-5": {"input_cost_per_token": 1e-7, "output_cost_per_token": 5e-7}
}"#;

fn pricing() -> PricingTable {
    PricingTable::from_litellm_document(PRICING_DOCUMENT.as_bytes()).unwrap()
}

fn assert_close(actual: f64, expected: f64) {
    assert!((actual - expected).abs() < 1e-12, "{actual} != {expected}");
}

#[test]
fn prices_every_token_category_with_its_own_rate() {
    let tokens = TokenCounts {
        input: 1_000,
        output: 100,
        cache_creation_five_minute: 1_000,
        cache_creation_one_hour: 1_000,
        cache_read: 10_000,
    };
    let cost = pricing().usage_cost_usd("claude-opus-5-5", false, &tokens, None);
    assert_close(
        cost,
        1_000.0 * 4e-6 + 100.0 * 2e-5 + 1_000.0 * 5e-6 + 1_000.0 * 8e-6 + 10_000.0 * 2e-7,
    );
}

#[test]
fn multiplies_fast_mode_by_the_published_multiplier() {
    let tokens = TokenCounts {
        output: 1_000,
        ..TokenCounts::default()
    };
    let table = pricing();
    let standard = table.usage_cost_usd("claude-opus-5-5", false, &tokens, None);
    assert_close(
        table.usage_cost_usd("claude-opus-5-5", true, &tokens, None),
        standard * 2.0,
    );
}

#[test]
fn derives_missing_cache_rates_from_the_input_rate() {
    let tokens = TokenCounts {
        cache_creation_five_minute: 100,
        cache_creation_one_hour: 100,
        cache_read: 100,
        ..TokenCounts::default()
    };
    let cost = pricing().usage_cost_usd("claude-haiku-5-5", false, &tokens, None);
    assert_close(cost, 100.0 * 1e-7 * (1.25 + 2.0 + 0.1));
}

#[test]
fn tiers_each_category_above_two_hundred_thousand_tokens() {
    let tokens = TokenCounts {
        input: 300_000,
        ..TokenCounts::default()
    };
    let cost = pricing().usage_cost_usd("claude-sonnet-4-20250514", false, &tokens, None);
    assert_close(cost, 200_000.0 * 3e-6 + 100_000.0 * 6e-6);
}

#[test]
fn falls_back_from_a_dated_model_to_its_base_and_back() {
    let table = pricing();
    assert!(table.price_for("claude-opus-5-5-20261101").is_some());
    assert!(table.price_for("claude-sonnet-4-20250514").is_some());
    assert!(table.price_for("claude-opus-5").is_none());
    assert!(table.price_for("sample_spec").is_none());
}

#[test]
fn prefers_the_cost_the_transcript_reported_and_prices_unknown_models_at_zero() {
    let tokens = TokenCounts {
        input: 10,
        ..TokenCounts::default()
    };
    let table = pricing();
    assert_close(
        table.usage_cost_usd("claude-opus-5-5", false, &tokens, Some(0.5)),
        0.5,
    );
    assert_close(
        table.usage_cost_usd("gpt-6.1-sol", false, &tokens, None),
        0.0,
    );
}

#[test]
fn fingerprints_the_document_so_a_new_price_list_is_detected() {
    let changed = PRICING_DOCUMENT.replace("4e-6", "5e-6");
    let other = PricingTable::from_litellm_document(changed.as_bytes()).unwrap();
    assert_ne!(pricing().fingerprint(), other.fingerprint());
}
