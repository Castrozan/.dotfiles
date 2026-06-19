export interface DashboardConfiguration {
  readonly snapshotsBucket: string;
  readonly snapshotsObjectPrefix: string;
  readonly liveRefreshIntervalMilliseconds: number;
}

export const DASHBOARD_CONFIGURATION: DashboardConfiguration = {
  snapshotsBucket: 'zg-url-shortener-2026-dotfiles-usage-snapshots',
  snapshotsObjectPrefix: 'snapshots/',
  liveRefreshIntervalMilliseconds: 30000,
};
