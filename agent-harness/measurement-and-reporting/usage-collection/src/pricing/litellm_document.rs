use std::collections::HashMap;

use anyhow::{Context, Result};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

use super::{ModelPrice, PricingTable, TieredRate};

const CACHE_CREATION_FIVE_MINUTE_INPUT_MULTIPLIER: f64 = 1.25;
const CACHE_CREATION_ONE_HOUR_INPUT_MULTIPLIER: f64 = 2.0;
const CACHE_READ_INPUT_MULTIPLIER: f64 = 0.1;

impl PricingTable {
    pub fn from_litellm_document(document_bytes: &[u8]) -> Result<Self> {
        let document: Map<String, Value> = serde_json::from_slice(document_bytes)
            .context("the LiteLLM pricing document must be a JSON object")?;
        let prices: HashMap<String, ModelPrice> = document
            .iter()
            .filter_map(|(model, entry)| {
                model_price(entry.as_object()?).map(|price| (model.clone(), price))
            })
            .collect();
        let fingerprint = format!("{:x}", Sha256::digest(document_bytes));
        Ok(Self::new(prices, fingerprint))
    }
}

fn model_price(entry: &Map<String, Value>) -> Option<ModelPrice> {
    let rate = |field: &str| entry.get(field).and_then(Value::as_f64);
    let input = rate("input_cost_per_token")?;
    let output = rate("output_cost_per_token")?;
    let input_above_threshold = rate("input_cost_per_token_above_200k_tokens");
    Some(ModelPrice {
        input: TieredRate {
            base: input,
            above_threshold: input_above_threshold,
        },
        output: TieredRate {
            base: output,
            above_threshold: rate("output_cost_per_token_above_200k_tokens"),
        },
        cache_creation_five_minute: TieredRate {
            base: rate("cache_creation_input_token_cost")
                .unwrap_or(input * CACHE_CREATION_FIVE_MINUTE_INPUT_MULTIPLIER),
            above_threshold: rate("cache_creation_input_token_cost_above_200k_tokens"),
        },
        cache_creation_one_hour: TieredRate {
            base: rate("cache_creation_input_token_cost_above_1hr")
                .unwrap_or(input * CACHE_CREATION_ONE_HOUR_INPUT_MULTIPLIER),
            above_threshold: rate("cache_creation_input_token_cost_above_1hr_above_200k_tokens")
                .or(input_above_threshold
                    .map(|above| above * CACHE_CREATION_ONE_HOUR_INPUT_MULTIPLIER)),
        },
        cache_read: TieredRate {
            base: rate("cache_read_input_token_cost")
                .unwrap_or(input * CACHE_READ_INPUT_MULTIPLIER),
            above_threshold: rate("cache_read_input_token_cost_above_200k_tokens"),
        },
        fast_multiplier: entry
            .get("provider_specific_entry")
            .and_then(|provider_entry| provider_entry.get("fast"))
            .and_then(Value::as_f64)
            .unwrap_or(1.0),
    })
}
