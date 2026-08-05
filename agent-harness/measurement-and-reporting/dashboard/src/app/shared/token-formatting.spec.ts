import { cacheReadSharePercent, formatTokenCount, orderedOtelTokenTypes } from './token-formatting';
import { TokenTotals } from '../models/account-view.model';

describe('formatTokenCount', () => {
  it('formats billions, millions and thousands with two decimals', () => {
    expect(formatTokenCount(2_500_000_000)).toBe('2.50B');
    expect(formatTokenCount(3_400_000)).toBe('3.40M');
    expect(formatTokenCount(12_300)).toBe('12.30K');
  });

  it('renders sub-thousand counts as bare integers', () => {
    expect(formatTokenCount(999)).toBe('999');
    expect(formatTokenCount(0)).toBe('0');
  });
});

describe('cacheReadSharePercent', () => {
  it('returns the cache-read fraction of input-side tokens', () => {
    const tokenTotals: TokenTotals = {
      input_tokens: 100,
      output_tokens: 0,
      cache_read_input_tokens: 800,
      cache_creation_input_tokens: 100,
      cost_usd: 0,
    };
    expect(cacheReadSharePercent(tokenTotals)).toBe(80);
  });

  it('returns zero when there are no input-side tokens', () => {
    const tokenTotals: TokenTotals = {
      input_tokens: 0,
      output_tokens: 0,
      cache_read_input_tokens: 0,
      cache_creation_input_tokens: 0,
      cost_usd: 0,
    };
    expect(cacheReadSharePercent(tokenTotals)).toBe(0);
  });
});

describe('orderedOtelTokenTypes', () => {
  it('keeps the canonical order then appends unknown types sorted', () => {
    const ordered = orderedOtelTokenTypes({
      output: 1,
      zeta: 1,
      cacheRead: 1,
      alpha: 1,
    });
    expect(ordered).toEqual(['cacheRead', 'output', 'alpha', 'zeta']);
  });
});
