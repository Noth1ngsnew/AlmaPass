import { Component, effect, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { FavoriteToggle } from '../components/favorite-toggle';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { EventDatePipe, I18n, TPipe } from '../core/i18n';
import { EventItem } from '../core/models';

@Component({
  selector: 'app-event-detail',
  imports: [RouterLink, TPipe, EventDatePipe, FavoriteToggle],
  template: `
    <div class="container detail">
      <a routerLink="/" class="back">← {{ 'event.back' | t }}</a>

      @if (event(); as item) {
        <div class="detail__grid">
          <div>
            <div class="detail__media">
              @if (item.image_url) {
                <img [src]="item.image_url" [alt]="item.title" (error)="hide($event)" />
              }
            </div>
            <div class="detail__tags">
              <span class="tag">{{ item.category.name }}</span>
              @if (item.status !== 'published') {
                <span class="tag tag--warn">{{ 'event.pending' | t }}</span>
              }
            </div>
            <h1 class="detail__title">{{ item.title }}</h1>
            <h2 class="section-title">{{ 'event.about' | t }}</h2>
            <p class="detail__text">{{ item.description }}</p>
          </div>

          <aside class="panel">
            <dl class="facts">
              <div>
                <dt>{{ 'event.when' | t }}</dt>
                <dd>{{ item.start_at | eventDate }} – {{ item.end_at | eventDate: 'time' }}</dd>
              </div>
              <div>
                <dt>{{ 'event.where' | t }}</dt>
                <dd>{{ item.venue.name }}<small>{{ item.venue.address }}</small></dd>
              </div>
              <div>
                <dt>{{ 'event.price' | t }}</dt>
                <dd>{{ price(item) || ('event.free' | t) }}</dd>
              </div>
              <div>
                <dt>{{ 'event.organizer' | t }}</dt>
                <dd>
                  {{ item.organizer.name }}
                  @if (item.organizer.is_verified) {
                    <span class="verified">✓ {{ 'event.verified' | t }}</span>
                  }
                </dd>
              </div>
            </dl>

            <app-favorite-toggle [event]="item" />
            @if (item.source_url) {
              <a class="btn btn--block" [href]="item.source_url" target="_blank" rel="noopener">{{ 'event.tickets' | t }}</a>
            }

            @if (canManage(item)) {
              <a class="btn btn--ghost btn--block" [routerLink]="['/events', item.id, 'qr']">{{ 'qr.open' | t }}</a>
            }

            <div class="nft">
              <div class="nft__badge" aria-hidden="true">NFT</div>
              <div>
                <strong>{{ 'event.nftTitle' | t }}</strong>
                @if (item.is_visited) {
                  <p class="nft__done">✓ {{ 'event.visited' | t }}</p>
                } @else {
                  <p>{{ 'event.nftText' | t }}</p>
                  <a class="nft__link" routerLink="/scan">{{ 'event.scanCta' | t }} →</a>
                }
              </div>
            </div>
          </aside>
        </div>
      } @else if (error()) {
        <p class="state state--error">{{ 'event.notFound' | t }}</p>
      } @else {
        <p class="state">{{ 'common.loading' | t }}</p>
      }
    </div>
  `,
})
export class EventDetail {
  private api = inject(EventsApi);
  private i18n = inject(I18n);
  private auth = inject(Auth);

  /** Параметр маршрута /events/:id */
  readonly id = input.required<string>();

  protected readonly event = signal<EventItem | null>(null);
  protected readonly error = signal(false);

  constructor() {
    effect((onCleanup) => {
      this.i18n.lang();
      this.auth.isLoggedIn();
      const sub = this.api.get(Number(this.id())).subscribe({
        next: (item) => {
          this.event.set(item);
          this.error.set(false);
        },
        error: () => this.error.set(true),
      });
      onCleanup(() => sub.unsubscribe());
    });
  }

  /** Если картинка не загрузилась, остаётся фоновый градиент. */
  protected hide(event: Event): void {
    (event.target as HTMLElement).hidden = true;
  }

  /** QR-код видят организатор события и администратор. */
  protected canManage(item: EventItem): boolean {
    const user = this.auth.user();
    return !!user && (user.role === 'admin' || user.organizer_id === item.organizer.id);
  }

  protected price(item: EventItem): string {
    const value = Number(item.price);
    return value ? `${value.toLocaleString('ru-RU')} ₸` : '';
  }
}
