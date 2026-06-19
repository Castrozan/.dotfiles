import { ChangeDetectionStrategy, Component, DestroyRef, inject, signal } from '@angular/core';
import { DASHBOARD_CONFIGURATION } from '../../config/dashboard-config';
import { UsageViewModel } from '../../models/account-view.model';
import { UsageAggregationService } from '../../services/usage-aggregation/usage-aggregation.service';
import { UsageSnapshotClientService } from '../../services/usage-snapshot-client.service';
import { StatCardsComponent } from '../stat-cards/stat-cards.component';
import { DailyTokensChartComponent } from '../daily-tokens-chart/daily-tokens-chart.component';
import { OtelPanelComponent } from '../otel-panel/otel-panel.component';
import { AccountTableComponent } from '../account-table/account-table.component';

@Component({
  selector: 'app-dashboard',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    StatCardsComponent,
    DailyTokensChartComponent,
    OtelPanelComponent,
    AccountTableComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.css',
})
export class DashboardComponent {
  private readonly snapshotClient = inject(UsageSnapshotClientService);
  private readonly aggregation = inject(UsageAggregationService);

  readonly viewModel = signal<UsageViewModel | null>(null);
  readonly errorMessage = signal<string | null>(null);
  readonly isLoading = signal<boolean>(true);
  readonly lastUpdatedLabel = signal<string | null>(null);

  constructor() {
    this.refreshUsage();
    const refreshTimer = setInterval(
      () => this.refreshUsage(),
      DASHBOARD_CONFIGURATION.liveRefreshIntervalMilliseconds,
    );
    inject(DestroyRef).onDestroy(() => clearInterval(refreshTimer));
  }

  async refreshUsage(): Promise<void> {
    try {
      const snapshots = await this.snapshotClient.fetchAllSnapshots();
      this.viewModel.set(this.aggregation.buildUsageViewModel(snapshots));
      this.errorMessage.set(null);
      this.lastUpdatedLabel.set(new Date().toLocaleTimeString('en-US'));
    } catch (error) {
      this.errorMessage.set(
        error instanceof Error ? error.message : 'failed to load usage snapshots',
      );
    } finally {
      this.isLoading.set(false);
    }
  }
}
