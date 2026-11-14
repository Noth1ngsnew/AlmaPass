import { Component, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { EventsApi } from '../core/events-api';
import { EventDatePipe, I18n, TPipe } from '../core/i18n';
import { Visit } from '../core/models';

@Component({
  selector: 'app-visits',
  imports: [RouterLink, TPipe, EventDatePipe],
  template: `
    <div class="container page">
      <h1 class="page__title">{{ 'visits.title' | t }}</h1>

      @if (error()) {
        <p class="state state--error">{{ 'common.error' | t }}</p>
      } @else if (loading()) {
        <p class="state">{{ 'common.loading' | t }}</p>
      } @else if (!visits().length) {
        <p class="state">{{ 'visits.empty' | t }}</p>
        <p class="center"><a class="btn" routerLink="/scan">{{ 'nav.scan' | t }}</a></p>
      } @else {
        <div class="rows">
          @for (visit of visits(); track visit.id) {
            <a class="row" [routerLink]="['/events', visit.event.id]">
              <span class="row__icon row__icon--nft" aria-hidden="true">NFT</span>
              <span class="row__main">
                <strong>{{ visit.event.title }}</strong>
                <small>
                  {{ visit.event.venue.name }} ·
                  {{ 'visits.checkedIn' | t: { date: (visit.checked_in_at | eventDate) } }}
                </small>
              </span>
              @if (visit.nft_reward; as nft) {
                <span class="tag" [class.tag--warn]="nft.status === 'pending'" [class.tag--fail]="nft.status === 'failed'">
                  {{ 'visits.nft.' + nft.status | t }}
                </span>
              }
            </a>
          }
        </div>
      }
    </div>
  `,
})
export class Visits {
  private api = inject(EventsApi);
  private i18n = inject(I18n);

  protected readonly visits = signal<Visit[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);

  constructor() {
    effect((onCleanup) => {
      this.i18n.lang();
      const sub = this.api.visits().subscribe({
        next: (res) => {
          this.visits.set(res.results);
          this.loading.set(false);
        },
        error: () => {
          this.error.set(true);
          this.loading.set(false);
        },
      });
      onCleanup(() => sub.unsubscribe());
    });
  }
}
