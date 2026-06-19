import { ChangeDetectionStrategy, Component, computed, input } from '@angular/core';
import { AccountView } from '../../models/account-view.model';
import { formatTokenCount } from '../../shared/token-formatting';

interface AccountRow {
  account_label: string;
  machine_count: number;
  window: string;
  cache_read: string;
  output: string;
  cost: string;
  recalls_suppressed: number;
}

@Component({
  selector: 'app-account-table',
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <table>
      <thead>
        <tr>
          <th>account</th>
          <th>machines</th>
          <th>window</th>
          <th>cache-read</th>
          <th>output</th>
          <th>cost (notional)</th>
          <th>recalls suppressed</th>
        </tr>
      </thead>
      <tbody>
        @for (row of rows(); track row.account_label) {
          <tr>
            <td>
              <code>{{ row.account_label }}</code>
            </td>
            <td>{{ row.machine_count }}</td>
            <td>{{ row.window }}</td>
            <td>{{ row.cache_read }}</td>
            <td>{{ row.output }}</td>
            <td>{{ row.cost }}</td>
            <td>{{ row.recalls_suppressed }}</td>
          </tr>
        }
      </tbody>
    </table>
  `,
})
export class AccountTableComponent {
  readonly accounts = input.required<AccountView[]>();

  readonly rows = computed<AccountRow[]>(() =>
    this.accounts().map((accountView) => {
      const tokenTotals = accountView.token_totals;
      const firstDate = accountView.first_session_date ?? '-';
      const lastDate = accountView.last_computed_date ?? '-';
      return {
        account_label: accountView.account_label,
        machine_count: accountView.machine_count,
        window: `${firstDate} to ${lastDate}`,
        cache_read: formatTokenCount(tokenTotals.cache_read_input_tokens),
        output: formatTokenCount(tokenTotals.output_tokens),
        cost: `$${Math.round(tokenTotals.cost_usd).toLocaleString('en-US')}`,
        recalls_suppressed: accountView.memory_recall_savings.suppressed_recall_event_total,
      };
    }),
  );
}
