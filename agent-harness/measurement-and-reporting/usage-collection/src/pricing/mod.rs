mod litellm_document;

use std::collections::HashMap;

use crate::transcript::TokenCounts;

const TIER_THRESHOLD_TOKENS: u64 = 200_000;
const DATE_SUFFIX_DIGITS: usize = 8;

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct TieredRate {
    pub base: f64,
    pub above_threshold: Option<f64>,
}

impl TieredRate {
    pub fn cost_usd(&self, tokens: u64) -> f64 {
        match self.above_threshold {
            Some(above_threshold) if tokens > TIER_THRESHOLD_TOKENS => {
                TIER_THRESHOLD_TOKENS as f64 * self.base
                    + (tokens - TIER_THRESHOLD_TOKENS) as f64 * above_threshold
            }
            _ => tokens as f64 * self.base,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub struct ModelPrice {
    pub input: TieredRate,
    pub output: TieredRate,
    pub cache_creation_five_minute: TieredRate,
    pub cache_creation_one_hour: TieredRate,
    pub cache_read: TieredRate,
    pub fast_multiplier: f64,
}

impl ModelPrice {
    pub fn cost_usd(&self, tokens: &TokenCounts, is_fast: bool) -> f64 {
        let speed_multiplier = if is_fast { self.fast_multiplier } else { 1.0 };
        (self.input.cost_usd(tokens.input)
            + self.output.cost_usd(tokens.output)
            + self
                .cache_creation_five_minute
                .cost_usd(tokens.cache_creation_five_minute)
            + self
                .cache_creation_one_hour
                .cost_usd(tokens.cache_creation_one_hour)
            + self.cache_read.cost_usd(tokens.cache_read))
            * speed_multiplier
    }
}

pub struct PricingTable {
    prices: HashMap<String, ModelPrice>,
    fingerprint: String,
}

impl PricingTable {
    pub fn new(prices: HashMap<String, ModelPrice>, fingerprint: String) -> Self {
        Self {
            prices,
            fingerprint,
        }
    }

    pub fn fingerprint(&self) -> &str {
        &self.fingerprint
    }

    pub fn price_for(&self, model: &str) -> Option<&ModelPrice> {
        self.prices
            .get(model)
            .or_else(|| without_date_suffix(model).and_then(|model| self.prices.get(model)))
    }

    pub fn usage_cost_usd(
        &self,
        model: &str,
        is_fast: bool,
        tokens: &TokenCounts,
        reported_cost_usd: Option<f64>,
    ) -> f64 {
        reported_cost_usd.unwrap_or_else(|| {
            self.price_for(model)
                .map_or(0.0, |price| price.cost_usd(tokens, is_fast))
        })
    }
}

fn without_date_suffix(model: &str) -> Option<&str> {
    let (base, suffix) = model.rsplit_once('-')?;
    (suffix.len() == DATE_SUFFIX_DIGITS && suffix.bytes().all(|byte| byte.is_ascii_digit()))
        .then_some(base)
}
