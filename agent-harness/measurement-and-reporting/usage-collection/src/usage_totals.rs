#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct ModelUsageTotals {
    pub input_tokens: u64,
    pub output_tokens: u64,
    pub cache_read_input_tokens: u64,
    pub cache_creation_input_tokens: u64,
    pub cost_usd: f64,
}

impl ModelUsageTotals {
    pub fn token_total(&self) -> u64 {
        self.input_tokens
            + self.output_tokens
            + self.cache_read_input_tokens
            + self.cache_creation_input_tokens
    }

    pub fn add(&mut self, other: &Self) {
        self.input_tokens += other.input_tokens;
        self.output_tokens += other.output_tokens;
        self.cache_read_input_tokens += other.cache_read_input_tokens;
        self.cache_creation_input_tokens += other.cache_creation_input_tokens;
        self.cost_usd += other.cost_usd;
    }
}

#[derive(Debug, Clone, PartialEq)]
pub struct DailyModelUsage {
    pub usage_date: String,
    pub model: String,
    pub is_fast: bool,
    pub totals: ModelUsageTotals,
}

impl DailyModelUsage {
    pub fn model_label(&self) -> String {
        crate::transcript::model_label(&self.model, self.is_fast)
    }
}
