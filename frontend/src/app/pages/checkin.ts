import { HttpErrorResponse } from '@angular/common/http';
import { Component, effect, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { EventDatePipe, TPipe } from '../core/i18n';
import { Visit } from '../core/models';

@Component({
  selector: 'app-checkin',
  imports: [RouterLink, TPipe, EventDatePipe],
  template: `
    <div class="container notice">
      @if (visit(); as item) {
        <div class="panel notice__card">
          <div class="notice__icon notice__icon--ok" aria-hidden="true">✓</div>
          <h1>{{ (item.already_checked_in ? 'checkin.againTitle' : 'checkin.successTitle') | t }}</h1>
          <p class="notice__event">
            <a [routerLink]="['/events', item.event.id]">{{ item.event.title }}</a>
            <small>{{ item.event.venue.name }} · {{ item.event.start_at | eventDate }}</small>
          </p>
          <p class="muted">{{ 'checkin.successText' | t }}</p>
          @if (!auth.user()?.wallet_address) {
            <p class="form-error">{{ 'checkin.noWallet' | t }}</p>
            <a class="btn" routerLink="/profile">{{ 'checkin.toProfile' | t }}</a>
          }
          <a class="btn btn--ghost" routerLink="/visits">{{ 'checkin.toVisits' | t }}</a>
        </div>
      } @else if (errorCode(); as code) {
        <div class="panel notice__card">
          <div class="notice__icon notice__icon--fail" aria-hidden="true">!</div>
          <h1>{{ 'checkin.failTitle' | t }}</h1>
          <p class="muted">{{ 'checkin.error.' + code | t }}</p>
          <a class="btn" routerLink="/scan">{{ 'checkin.retry' | t }}</a>
        </div>
      } @else {
        <p class="state">{{ 'checkin.working' | t }}</p>
      }
    </div>
  `,
})
export class Checkin {
  private api = inject(EventsApi);
  protected auth = inject(Auth);

  /** Параметр маршрута /checkin/:token — код из QR */
  readonly token = input.required<string>();

  protected readonly visit = signal<Visit | null>(null);
  protected readonly errorCode = signal('');

  constructor() {
    effect((onCleanup) => {
      const sub = this.api.checkin(this.token()).subscribe({
        next: (visit) => this.visit.set(visit),
        error: (error: HttpErrorResponse) => {
          const code = error.status === 400 ? error.error?.code : '';
          this.errorCode.set(['invalid', 'not_started', 'ended'].includes(code) ? code : 'unknown');
        },
      });
      onCleanup(() => sub.unsubscribe());
    });
  }
}
