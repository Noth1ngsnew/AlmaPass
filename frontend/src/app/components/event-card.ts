import { Component, input, output } from '@angular/core';
import { RouterLink } from '@angular/router';
import { EventDatePipe, TPipe } from '../core/i18n';
import { EventItem } from '../core/models';
import { FavoriteToggle } from './favorite-toggle';

@Component({
  selector: 'app-event-card',
  imports: [RouterLink, TPipe, EventDatePipe, FavoriteToggle],
  template: `
    @let item = event();
    <article class="card">
      <a [routerLink]="['/events', item.id]" class="card__media">
        @if (item.image_url) {
          <img [src]="item.image_url" [alt]="item.title" loading="lazy" (error)="hide($event)" />
        }
        <span class="card__date">{{ item.start_at | eventDate: 'day' }}</span>
      </a>
      <div class="card__body">
        <div class="card__meta">
          <span class="tag">{{ item.category.name }}</span>
          <span class="card__time">{{ item.start_at | eventDate: 'time' }}</span>
        </div>
        <h3 class="card__title">
          <a [routerLink]="['/events', item.id]">{{ item.title }}</a>
        </h3>
        <p class="card__venue">{{ item.venue.name }}</p>
        <div class="card__foot">
          <span class="price" [class.price--free]="isFree()">
            {{ isFree() ? ('event.free' | t) : priceLabel() }}
          </span>
          <app-favorite-toggle [event]="item" compact (changed)="changed.emit($event)" />
        </div>
      </div>
    </article>
  `,
})
export class EventCard {
  readonly event = input.required<EventItem>();
  readonly changed = output<boolean>();

  /** Если картинка не загрузилась, остаётся фоновый градиент. */
  protected hide(event: Event): void {
    (event.target as HTMLElement).hidden = true;
  }

  protected isFree(): boolean {
    return Number(this.event().price) === 0;
  }

  protected priceLabel(): string {
    return `${Number(this.event().price).toLocaleString('ru-RU')} ₸`;
  }
}
