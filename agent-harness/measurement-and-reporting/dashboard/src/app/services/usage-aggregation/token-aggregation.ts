import {
  DailyModelTokens,
  ModelTokenTotals,
  ModelUsageTotals,
} from '../../models/usage-snapshot.model';
import { TokenTotals } from '../../models/account-view.model';

export const AGGREGATE_TOKEN_FIELDS: (keyof TokenTotals)[] = [
  'input_tokens',
  'output_tokens',
  'cache_read_input_tokens',
  'cache_creation_input_tokens',
  'cost_usd',
];

function accumulateModelTokenTotals(
  accumulated: ModelTokenTotals,
  modelTotals: ModelTokenTotals,
): void {
  for (const [fieldName, fieldValue] of Object.entries(modelTotals)) {
    const key = fieldName as keyof ModelTokenTotals;
    accumulated[key] = (accumulated[key] ?? 0) + (fieldValue ?? 0);
  }
}

export function sumModelUsageTotals(modelUsageTotalsList: ModelUsageTotals[]): ModelUsageTotals {
  const summed: ModelUsageTotals = {};
  for (const modelUsageTotals of modelUsageTotalsList) {
    for (const [modelName, modelTotals] of Object.entries(modelUsageTotals)) {
      const accumulated = (summed[modelName] ??= {});
      accumulateModelTokenTotals(accumulated, modelTotals);
    }
  }
  return summed;
}

export function aggregateTokenFields(modelUsageTotals: ModelUsageTotals): TokenTotals {
  const modelTotalsList = Object.values(modelUsageTotals);
  const sumField = (fieldName: keyof TokenTotals): number =>
    modelTotalsList.reduce((runningTotal, modelTotals) => {
      const value = (modelTotals as Record<string, number | undefined>)[fieldName];
      return runningTotal + (value ?? 0);
    }, 0);
  return {
    input_tokens: sumField('input_tokens'),
    output_tokens: sumField('output_tokens'),
    cache_read_input_tokens: sumField('cache_read_input_tokens'),
    cache_creation_input_tokens: sumField('cache_creation_input_tokens'),
    cost_usd: sumField('cost_usd'),
  };
}

function accumulateDailyTokenTotal(
  dailyTotalTokens: Record<string, number>,
  dailyEntry: DailyModelTokens,
  entryDate: string,
): void {
  const dayTokenSum = Object.values(dailyEntry.tokens_by_model ?? {}).reduce(
    (runningTotal, tokenCount) => runningTotal + tokenCount,
    0,
  );
  dailyTotalTokens[entryDate] = (dailyTotalTokens[entryDate] ?? 0) + dayTokenSum;
}

export function combineDailyTotalTokens(
  dailyModelTokensList: DailyModelTokens[][],
): Record<string, number> {
  const dailyTotalTokens: Record<string, number> = {};
  for (const dailyModelTokens of dailyModelTokensList) {
    for (const dailyEntry of dailyModelTokens) {
      const entryDate = dailyEntry.date;
      if (!entryDate) {
        continue;
      }
      accumulateDailyTokenTotal(dailyTotalTokens, dailyEntry, entryDate);
    }
  }
  return dailyTotalTokens;
}
