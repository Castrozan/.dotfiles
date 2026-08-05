import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { AggregatedOtelMetrics } from '../../models/account-view.model';
import {
  OTEL_TOKEN_TYPE_LABELS,
  formatTokenCount,
  orderedOtelTokenTypes,
} from '../../shared/token-formatting';

interface OtelChip {
  label: string;
  value: string;
}

@Component({
  selector: 'app-otel-panel',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (otelMetrics().has_data) {
      <div class="chips">
        @for (chip of chips(); track chip.label) {
          <span class="chip">{{ chip.label }}: {{ chip.value }}</span>
        }
      </div>
      <div class="panel">
        <p>
          Live token counts straight from Claude Code's OpenTelemetry stream, aggregated across
          machines and independent of the stats-cache series above. Notional cost on the stream:
          <b>\${{ totalCost() }}</b
          >.
        </p>
      </div>
    } @else {
      <div class="panel">
        <p>
          The local OpenTelemetry collector runs on every machine, but no metrics interval has been
          flushed yet. Real-time token counts by type appear here once Claude Code exports its first
          batch.
        </p>
      </div>
    }
  `,
})
export class OtelPanelComponent {
  readonly otelMetrics = input.required<AggregatedOtelMetrics>();

  readonly chips = computed<OtelChip[]>(() => {
    const tokenUsageByType = this.otelMetrics().token_usage_by_type;
    return orderedOtelTokenTypes(tokenUsageByType).map((tokenType) => ({
      label: OTEL_TOKEN_TYPE_LABELS[tokenType] ?? tokenType,
      value: formatTokenCount(tokenUsageByType[tokenType]),
    }));
  });

  readonly totalCost = computed<string>(() =>
    this.otelMetrics().total_cost_usd.toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }),
  );
}
