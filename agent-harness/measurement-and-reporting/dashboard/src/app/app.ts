import { ChangeDetectionStrategy, Component } from '@angular/core';
import { DashboardComponent } from './components/dashboard/dashboard.component';

@Component({
  selector: 'app-root',
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [DashboardComponent],
  template: `<app-dashboard />`,
})
export class App {}
