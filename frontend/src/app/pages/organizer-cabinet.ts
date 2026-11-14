import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { EventDatePipe, I18n, TPipe } from '../core/i18n';
import { EventItem, Organizer } from '../core/models';

@Component({
  selector: 'app-organizer-cabinet',
  imports: [FormsModule, RouterLink, TPipe, EventDatePipe],
  template: `
    <div class="container page">
      @if (!auth.user()) {
        <p class="state">{{ 'common.loading' | t }}</p>
      } @else if (!auth.user()?.organizer_id) {
        <!-- Заявка: у пользователя ещё нет профиля организатора -->
        <div class="page--narrow apply">
          <h1 class="page__title">{{ 'org.applyTitle' | t }}</h1>
          <form class="panel" (ngSubmit)="apply()" #form="ngForm">
            <p class="muted">{{ 'org.applyText' | t }}</p>
            <label class="field">
              <span>{{ 'org.name' | t }}</span>
              <input name="name" [(ngModel)]="name" required maxlength="200" />
            </label>
            <label class="field">
              <span>{{ 'org.description' | t }}</span>
              <textarea name="description" [(ngModel)]="description" rows="3"></textarea>
            </label>
            <label class="field">
              <span>{{ 'org.website' | t }}</span>
              <input name="website" type="url" [(ngModel)]="website" placeholder="https://" />
            </label>
            @for (message of errors(); track message) {
              <p class="form-error" role="alert">{{ message }}</p>
            }
            <button class="btn" type="submit" [disabled]="form.invalid || busy()">{{ 'org.applyButton' | t }}</button>
          </form>
        </div>
      } @else {
        <div class="cabinet__head">
          <div>
            <h1 class="page__title">{{ 'org.title' | t }}</h1>
            @if (organizer(); as org) {
              <p class="muted">
                {{ org.name }} ·
                @if (org.is_verified) {
                  <span class="verified">✓ {{ 'org.verified' | t }}</span>
                } @else {
                  {{ 'org.notVerified' | t }}
                }
              </p>
            }
          </div>
          <a class="btn" routerLink="/organizer/events/new">+ {{ 'org.newEvent' | t }}</a>
        </div>

        @if (noticeKey(); as key) {
          <p class="form-ok" role="status">{{ key | t }}</p>
        }

        <div class="stats">
          <div class="stat"><strong>{{ events().length }}</strong><span>{{ 'org.stat.events' | t }}</span></div>
          <div class="stat"><strong>{{ count('published') }}</strong><span>{{ 'org.stat.published' | t }}</span></div>
          <div class="stat"><strong>{{ count('pending') }}</strong><span>{{ 'org.stat.pending' | t }}</span></div>
          <div class="stat stat--accent"><strong>{{ totalVisits() }}</strong><span>{{ 'org.stat.visits' | t }}</span></div>
        </div>

        <h2 class="results__title">{{ 'org.events' | t }}</h2>
        @if (error()) {
          <p class="state state--error">{{ 'common.error' | t }}</p>
        } @else if (loading()) {
          <p class="state">{{ 'common.loading' | t }}</p>
        } @else if (!events().length) {
          <p class="state">{{ 'org.empty' | t }}</p>
        } @else {
          <div class="rows">
            @for (event of events(); track event.id) {
              <div class="row row--event">
                <span class="row__main">
                  <strong><a [routerLink]="['/events', event.id]">{{ event.title }}</a></strong>
                  <small>
                    {{ event.start_at | eventDate }} · {{ event.venue.name }} ·
                    {{ 'org.visits' | t: { count: event.visits_count ?? 0 } }}
                  </small>
                </span>
                <span class="tag" [class]="'tag tag--' + event.status">{{ 'org.status.' + event.status | t }}</span>
                <span class="row__actions">
                  @if (deletingId() === event.id) {
                    <span class="muted">{{ 'org.confirmDelete' | t }}</span>
                    <button type="button" class="btn btn--small" (click)="remove(event)">{{ 'org.delete' | t }}</button>
                    <button type="button" class="btn btn--ghost btn--small" (click)="deletingId.set(null)">
                      {{ 'org.cancel' | t }}
                    </button>
                  } @else {
                    @if (event.status === 'published') {
                      <a class="btn btn--ghost btn--small" [routerLink]="['/events', event.id, 'qr']">{{ 'org.qr' | t }}</a>
                    }
                    <a class="btn btn--ghost btn--small" [routerLink]="['/organizer/events', event.id, 'edit']">
                      {{ 'org.edit' | t }}
                    </a>
                    <button type="button" class="btn btn--ghost btn--small" (click)="deletingId.set(event.id)">
                      {{ 'org.delete' | t }}
                    </button>
                  }
                </span>
              </div>
            }
          </div>
        }
      }
    </div>
  `,
})
export class OrganizerCabinet {
  protected auth = inject(Auth);
  private api = inject(EventsApi);
  private i18n = inject(I18n);

  /** Параметр адреса ?notice=created|updated — сообщение после сохранения формы */
  readonly notice = input<string>();

  protected name = '';
  protected description = '';
  protected website = '';
  protected readonly busy = signal(false);
  protected readonly errors = signal<string[]>([]);

  protected readonly organizer = signal<Organizer | null>(null);
  protected readonly events = signal<EventItem[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly deletingId = signal<number | null>(null);
  private readonly localNotice = signal('');

  protected readonly noticeKey = computed(() => {
    const value = this.localNotice() || this.notice();
    return value && ['created', 'updated', 'deleted'].includes(value) ? `org.${value}` : '';
  });
  protected readonly totalVisits = computed(() =>
    this.events().reduce((sum, event) => sum + (event.visits_count ?? 0), 0),
  );

  constructor() {
    effect(() => {
      this.i18n.lang();
      if (!this.auth.user()?.organizer_id) return;
      this.api.myOrganizer().subscribe({ next: (org) => this.organizer.set(org), error: () => {} });
      this.api.myEvents().subscribe({
        next: (res) => {
          this.events.set(res.results);
          this.loading.set(false);
        },
        error: () => {
          this.error.set(true);
          this.loading.set(false);
        },
      });
    });
  }

  protected count(status: EventItem['status']): number {
    return this.events().filter((event) => event.status === status).length;
  }

  protected apply(): void {
    this.busy.set(true);
    this.errors.set([]);
    this.api
      .applyOrganizer({ name: this.name.trim(), description: this.description.trim(), website: this.website.trim() })
      .subscribe({
        // Роль и organizer_id меняются на сервере — перечитываем профиль
        next: () => this.auth.reload().subscribe(() => this.busy.set(false)),
        error: (error: HttpErrorResponse) => {
          this.busy.set(false);
          const body = error.error;
          this.errors.set(
            error.status === 400 && body && typeof body === 'object'
              ? Object.values(body as Record<string, string[] | string>).flat().map(String)
              : [this.i18n.t('common.error')],
          );
        },
      });
  }

  protected remove(event: EventItem): void {
    this.api.deleteEvent(event.id).subscribe({
      next: () => {
        this.events.update((items) => items.filter((item) => item.id !== event.id));
        this.deletingId.set(null);
        this.localNotice.set('deleted');
      },
      error: () => this.deletingId.set(null),
    });
  }
}
