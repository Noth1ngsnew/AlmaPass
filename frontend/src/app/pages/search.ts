import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { EventCard } from '../components/event-card';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { I18n, TPipe } from '../core/i18n';
import { SearchResult } from '../core/models';

@Component({
  selector: 'app-search',
  imports: [FormsModule, RouterLink, TPipe, EventCard],
  template: `
    <div class="container page">
      <h1 class="page__title">{{ 'search.title' | t }}</h1>

      <form class="search-form" role="search" (ngSubmit)="submit()">
        <input
          type="search"
          name="q"
          [(ngModel)]="text"
          [placeholder]="'nav.search' | t"
          [attr.aria-label]="'nav.search' | t"
          autofocus
        />
        <button class="btn" type="submit">{{ 'search.button' | t }}</button>
      </form>

      @if (tooShort()) {
        <p class="state">{{ 'search.hint' | t }}</p>
      } @else if (error()) {
        <p class="state state--error">{{ 'common.error' | t }}</p>
      } @else if (result(); as res) {
        @if (!res.total) {
          <p class="state">{{ 'search.nothing' | t: { query: res.query } }}</p>
        } @else {
          <p class="count">{{ 'search.results' | t: { query: res.query, count: res.total } }}</p>

          @if (res.events.length) {
            <section class="results">
              <h2 class="results__title">{{ 'search.events' | t }} <span>{{ res.events.length }}</span></h2>
              <div class="grid">
                @for (event of res.events; track event.id) {
                  <app-event-card [event]="event" />
                }
              </div>
            </section>
          }

          @if (res.venues.length) {
            <section class="results">
              <h2 class="results__title">{{ 'search.venues' | t }} <span>{{ res.venues.length }}</span></h2>
              <div class="rows">
                @for (venue of res.venues; track venue.id) {
                  <a class="row" routerLink="/" [queryParams]="{ venue: venue.id }">
                    <span class="row__icon row__icon--venue" aria-hidden="true">
                      <svg viewBox="0 0 24 24" width="20" height="20">
                        <path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z" /><circle cx="12" cy="10" r="2.5" />
                      </svg>
                    </span>
                    <span class="row__main">
                      <strong>{{ venue.name }}</strong>
                      <small>{{ venue.address }}</small>
                    </span>
                    <span class="row__side">{{ 'search.eventsCount' | t: { count: venue.events_count } }}</span>
                  </a>
                }
              </div>
            </section>
          }

          @if (res.organizers.length) {
            <section class="results">
              <h2 class="results__title">{{ 'search.organizers' | t }} <span>{{ res.organizers.length }}</span></h2>
              <div class="rows">
                @for (organizer of res.organizers; track organizer.id) {
                  <a class="row" routerLink="/" [queryParams]="{ organizer: organizer.id }">
                    <span class="row__icon" aria-hidden="true">{{ organizer.name.charAt(0) }}</span>
                    <span class="row__main">
                      <strong>
                        {{ organizer.name }}
                        @if (organizer.is_verified) {
                          <span class="verified">✓ {{ 'event.verified' | t }}</span>
                        }
                      </strong>
                      <small>{{ organizer.description }}</small>
                    </span>
                    <span class="row__side">{{ 'search.eventsCount' | t: { count: organizer.events_count } }}</span>
                  </a>
                }
              </div>
            </section>
          }
        }
      } @else {
        <p class="state">{{ 'common.loading' | t }}</p>
      }
    </div>
  `,
})
export class Search {
  private api = inject(EventsApi);
  private i18n = inject(I18n);
  private auth = inject(Auth);
  private router = inject(Router);

  /** Параметр адреса /search?q=... */
  readonly q = input<string>();

  protected text = '';
  protected readonly result = signal<SearchResult | null>(null);
  protected readonly error = signal(false);
  protected readonly tooShort = computed(() => (this.q() ?? '').trim().length < 2);

  constructor() {
    effect((onCleanup) => {
      const query = (this.q() ?? '').trim();
      this.i18n.lang();
      this.auth.isLoggedIn();
      this.text = query;
      if (query.length < 2) return;
      const sub = this.api.search(query).subscribe({
        next: (res) => {
          this.result.set(res);
          this.error.set(false);
        },
        error: () => this.error.set(true),
      });
      onCleanup(() => sub.unsubscribe());
    });
  }

  protected submit(): void {
    this.router.navigate(['/search'], { queryParams: { q: this.text.trim() } });
  }
}
