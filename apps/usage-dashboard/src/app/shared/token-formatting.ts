import { TokenTotals } from '../models/account-view.model';

const TOKEN_MAGNITUDE_DIVISORS: [number, string][] = [
  [1_000_000_000, 'B'],
  [1_000_000, 'M'],
  [1_000, 'K'],
];

export const OTEL_TOKEN_TYPE_LABELS: Record<string, string> = {
  cacheRead: 'cache read',
  cacheCreation: 'cache creation',
  input: 'input',
  output: 'output',
};

export const OTEL_TOKEN_TYPE_ORDER = ['cacheRead', 'cacheCreation', 'input', 'output'];

export const ACCOUNT_SERIES_COLORS = ['#58a6ff', '#3fb950', '#d29922', '#bc8cff', '#f85149'];

export function formatTokenCount(tokenCount: number): string {
  for (const [divisor, suffix] of TOKEN_MAGNITUDE_DIVISORS) {
    if (tokenCount >= divisor) {
      return `${(tokenCount / divisor).toFixed(2)}${suffix}`;
    }
  }
  return String(Math.trunc(tokenCount));
}

export function cacheReadSharePercent(tokenTotals: TokenTotals): number {
  const cacheRead = tokenTotals.cache_read_input_tokens ?? 0;
  const cacheCreation = tokenTotals.cache_creation_input_tokens ?? 0;
  const freshInput = tokenTotals.input_tokens ?? 0;
  const inputSideTotal = cacheRead + cacheCreation + freshInput;
  if (inputSideTotal === 0) {
    return 0;
  }
  return Math.round((cacheRead / inputSideTotal) * 1000) / 10;
}

export function orderedOtelTokenTypes(tokenUsageByType: Record<string, number>): string[] {
  const known = OTEL_TOKEN_TYPE_ORDER.filter((tokenType) => tokenType in tokenUsageByType);
  const extra = Object.keys(tokenUsageByType)
    .filter((tokenType) => !OTEL_TOKEN_TYPE_ORDER.includes(tokenType))
    .sort();
  return [...known, ...extra];
}
