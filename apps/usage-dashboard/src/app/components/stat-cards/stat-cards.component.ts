import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { UsageSummary } from '../../models/account-view.model';
import { cacheReadSharePercent, formatTokenCount } from '../../shared/token-formatting';

interface StatCard {
  label: string;
  value: string;
  subtitle: string;
}

@Component({
  selector: 'app-stat-cards',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <div class="cards">
      @for (card of cards(); track card.label) {
        <div class="card">
          <div class="card-value">{{ card.value }}</div>
          <div class="card-label">{{ card.label }}</div>
          <div class="card-subtitle">{{ card.subtitle }}</div>
        </div>
      }
    </div>
  `,
})
export class StatCardsComponent {
  readonly summary = input.required<UsageSummary>();

  readonly cards = computed<StatCard[]>(() => {
    const summary = this.summary();
    const tokenTotals = summary.token_totals;
    const savings = summary.memory_recall_savings;
    return [
      {
        label: 'accounts tracked',
        value: String(summary.account_count),
        subtitle: `across ${summary.machine_count} machine(s)`,
      },
      {
        label: 'cache-read tokens',
        value: formatTokenCount(tokenTotals.cache_read_input_tokens),
        subtitle: 'the dominant cost driver',
      },
      {
        label: 'cache-read share',
        value: `${cacheReadSharePercent(tokenTotals)}%`,
        subtitle: 'of all input-side tokens',
      },
      {
        label: 'recall events suppressed',
        value: String(savings.suppressed_recall_event_total),
        subtitle: 'budget + debounce + dedup',
      },
      {
        label: 'dedup chars saved',
        value: formatTokenCount(savings.dedup_suppressed_character_total),
        subtitle: 'duplicate recalls stopped',
      },
    ];
  });
}
