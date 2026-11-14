import { Component, effect, inject, signal } from '@angular/core';
import { EventCard } from '../components/event-card';
import { EventsApi } from '../core/events-api';
import { I18n, TPipe } from '../core/i18n';
import { EventItem } from '../core/models';

@Component({
  selector: 'app-favorites',
  imports: [TPipe, EventCard],
  template: `
    <div class="container page">
      <h1 class="page__title">{{ 'favorites.title' | t }}</h1>
      @if (error()) {
        <p class="state state--error">{{ 'common.error' | t }}</p>
      } @else if (loading()) {
        <p class="state">{{ 'common.loading' | t }}</p>
      } @else if (!events().length) {
        <p class="state">{{ 'favorites.empty' | t }}</p>
      } @else {
        <div class="grid">
          @for (event of events(); track event.id) {
            <app-event-card [event]="event" (changed)="onChanged(event, $event)" />
          }
        </div>
      }
    </div>
  `,
})
export class Favorites {
  private api = inject(EventsApi);
  private i18n = inject(I18n);

  protected readonly events = signal<EventItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);

  constructor() {
    effect((onCleanup) => {
      this.i18n.lang();
      const sub = this.api.favorites().subscribe({
        next: (res) => {
          this.events.set(res.results);
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

  protected onChanged(event: EventItem, isFavorite: boolean): void {
    if (!isFavorite) this.events.update((items) => items.filter((item) => item.id !== event.id));
  }
}
