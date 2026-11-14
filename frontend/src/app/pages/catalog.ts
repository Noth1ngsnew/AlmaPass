import { Component, computed, effect, inject, signal, untracked } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { EventCard } from '../components/event-card';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { I18n, TPipe } from '../core/i18n';
import { Category, EventItem } from '../core/models';

const PAGE_SIZE = 12;

@Component({
  selector: 'app-catalog',
  imports: [FormsModule, TPipe, EventCard],
  template: `
    <section class="hero">
      <div class="container">
        <p class="kicker">{{ 'catalog.kicker' | t }}</p>
        <h1 class="hero__title">{{ 'catalog.title' | t }}</h1>
        <p class="hero__text">{{ 'catalog.subtitle' | t }}</p>
      </div>
    </section>

    <section class="container">
      <div class="filters">
        <div class="chips" role="group">
          <button type="button" class="chip" [class.is-active]="!category()" (click)="setCategory('')">
            {{ 'catalog.all' | t }}
          </button>
          @for (item of categories(); track item.id) {
            <button type="button" class="chip" [class.is-active]="category() === item.slug" (click)="setCategory(item.slug)">
              {{ item.name }}
            </button>
          }
        </div>

        <div class="filters__row">
          <label class="field field--inline">
            <span>{{ 'catalog.from' | t }}</span>
            <input type="date" [ngModel]="dateFrom()" (ngModelChange)="dateFrom.set($event); page.set(1)" />
          </label>
          <label class="field field--inline">
            <span>{{ 'catalog.to' | t }}</span>
            <input type="date" [ngModel]="dateTo()" (ngModelChange)="dateTo.set($event); page.set(1)" />
          </label>
          <label class="check">
            <input type="checkbox" [ngModel]="freeOnly()" (ngModelChange)="freeOnly.set($event); page.set(1)" />
            <span>{{ 'catalog.freeOnly' | t }}</span>
          </label>
          @if (hasFilters()) {
            <button type="button" class="btn btn--ghost" (click)="reset()">{{ 'catalog.reset' | t }}</button>
          }
        </div>
      </div>

      @if (error()) {
        <p class="state state--error">{{ 'common.error' | t }}</p>
      } @else if (loading() && !events().length) {
        <p class="state">{{ 'common.loading' | t }}</p>
      } @else if (!events().length) {
        <p class="state">{{ 'catalog.empty' | t }}</p>
      } @else {
        <p class="count">{{ 'catalog.found' | t: { count: count() } }}</p>
        <div class="grid" [class.is-loading]="loading()">
          @for (event of events(); track event.id) {
            <app-event-card [event]="event" />
          }
        </div>

        @if (totalPages() > 1) {
          <nav class="pager">
            <button type="button" class="btn btn--ghost" [disabled]="page() === 1" (click)="page.set(page() - 1)">
              {{ 'catalog.prev' | t }}
            </button>
            <span>{{ 'catalog.page' | t: { page: page(), total: totalPages() } }}</span>
            <button type="button" class="btn btn--ghost" [disabled]="page() === totalPages()" (click)="page.set(page() + 1)">
              {{ 'catalog.next' | t }}
            </button>
          </nav>
        }
      }
    </section>
  `,
})
export class Catalog {
  private api = inject(EventsApi);
  private i18n = inject(I18n);
  private auth = inject(Auth);

  protected readonly categories = signal<Category[]>([]);
  protected readonly events = signal<EventItem[]>([]);
  protected readonly count = signal(0);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);

  protected readonly category = signal('');
  protected readonly dateFrom = signal('');
  protected readonly dateTo = signal('');
  protected readonly freeOnly = signal(false);
  protected readonly page = signal(1);

  protected readonly totalPages = computed(() => Math.max(1, Math.ceil(this.count() / PAGE_SIZE)));
  protected readonly hasFilters = computed(
    () => !!(this.category() || this.dateFrom() || this.dateTo() || this.freeOnly()),
  );

  constructor() {
    // Названия категорий зависят от языка
    effect(() => {
      this.i18n.lang();
      this.api.categories().subscribe({ next: (items) => this.categories.set(items), error: () => {} });
    });

    // Список перезагружается при смене фильтров, страницы, языка и после входа (отметки избранного)
    effect((onCleanup) => {
      this.i18n.lang();
      this.auth.isLoggedIn();
      const filters = {
        category: this.category(),
        date_from: this.dateFrom(),
        date_to: this.dateTo(),
        free: this.freeOnly(),
        page: this.page(),
      };
      untracked(() => this.loading.set(true));
      const sub = this.api.list(filters).subscribe({
        next: (res) => {
          this.events.set(res.results);
          this.count.set(res.count);
          this.error.set(false);
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

  protected setCategory(slug: string): void {
    this.category.set(slug);
    this.page.set(1);
  }

  protected reset(): void {
    this.category.set('');
    this.dateFrom.set('');
    this.dateTo.set('');
    this.freeOnly.set(false);
    this.page.set(1);
  }
}
