import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { EventsApi } from '../core/events-api';
import { I18n, TPipe } from '../core/i18n';
import { Category, EventPayload, Lang, Venue } from '../core/models';

/** ISO-дата с сервера → значение для поля datetime-local (местное время). */
function toLocalInput(iso: string): string {
  const date = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

@Component({
  selector: 'app-event-form',
  imports: [FormsModule, RouterLink, TPipe],
  template: `
    <div class="container page page--narrow">
      <a routerLink="/organizer" class="back">← {{ 'org.title' | t }}</a>
      <h1 class="page__title">{{ (isEdit() ? 'form.editTitle' : 'form.newTitle') | t }}</h1>

      @if (loadError()) {
        <p class="state state--error">{{ 'event.notFound' | t }}</p>
      } @else if (!ready()) {
        <p class="state">{{ 'common.loading' | t }}</p>
      } @else {
        <form class="panel form" (ngSubmit)="save()" #form="ngForm">
          <p class="muted">{{ 'form.reviewNote' | t }}</p>

          <fieldset>
            <legend>{{ 'form.basics' | t }}</legend>
            <div class="tabs" role="tablist">
              @for (item of languages; track item.code) {
                <button
                  type="button"
                  role="tab"
                  class="tab"
                  [class.is-active]="tab() === item.code"
                  [attr.aria-selected]="tab() === item.code"
                  (click)="tab.set(item.code)"
                >
                  {{ item.label }}
                  <small>{{ (item.code === 'en' ? 'form.required' : 'form.optional') | t }}</small>
                </button>
              }
            </div>
            <!-- Все три языка остаются в форме, вкладка только показывает нужный -->
            @for (item of languages; track item.code) {
              <div [hidden]="tab() !== item.code" class="form__group">
                <label class="field">
                  <span>{{ 'form.title' | t }} ({{ item.label }})</span>
                  <input
                    [name]="'title_' + item.code"
                    [attr.name]="'title_' + item.code"
                    [(ngModel)]="model['title_' + item.code]"
                    [required]="item.code === 'en'"
                    maxlength="200"
                  />
                </label>
                <label class="field">
                  <span>{{ 'form.descriptionField' | t }} ({{ item.label }})</span>
                  <textarea [name]="'description_' + item.code" [attr.name]="'description_' + item.code" [(ngModel)]="model['description_' + item.code]" rows="4"></textarea>
                </label>
              </div>
            }
          </fieldset>

          <fieldset>
            <legend>{{ 'form.details' | t }}</legend>
            <label class="field">
              <span>{{ 'form.category' | t }}</span>
              <select name="category" [(ngModel)]="categoryId" required>
                <option [ngValue]="null" disabled>{{ 'form.choose' | t }}</option>
                @for (item of categories(); track item.id) {
                  <option [ngValue]="item.id">{{ item.name }}</option>
                }
              </select>
            </label>

            <label class="field">
              <span>{{ 'form.venue' | t }}</span>
              <select name="venue" [(ngModel)]="venueId" required>
                <option [ngValue]="null" disabled>{{ 'form.choose' | t }}</option>
                @for (item of venues(); track item.id) {
                  <option [ngValue]="item.id">{{ item.name }} — {{ item.address }}</option>
                }
              </select>
            </label>

            @if (addingVenue()) {
              <div class="subform">
                <label class="field">
                  <span>{{ 'form.venueName' | t }}</span>
                  <input name="venueName" [(ngModel)]="venueName" maxlength="200" />
                </label>
                <label class="field">
                  <span>{{ 'form.venueAddress' | t }}</span>
                  <input name="venueAddress" [(ngModel)]="venueAddress" maxlength="300" />
                </label>
                <div class="form__actions">
                  <button
                    type="button"
                    class="btn btn--small"
                    [disabled]="!venueName.trim() || !venueAddress.trim()"
                    (click)="saveVenue()"
                  >
                    {{ 'form.saveVenue' | t }}
                  </button>
                  <button type="button" class="btn btn--ghost btn--small" (click)="addingVenue.set(false)">
                    {{ 'form.cancel' | t }}
                  </button>
                </div>
              </div>
            } @else {
              <button type="button" class="link link--button" (click)="addingVenue.set(true)">
                + {{ 'form.addVenue' | t }}
              </button>
            }

            <div class="form-row">
              <label class="field">
                <span>{{ 'form.start' | t }}</span>
                <input name="start" type="datetime-local" [(ngModel)]="start" required />
              </label>
              <label class="field">
                <span>{{ 'form.end' | t }}</span>
                <input name="end" type="datetime-local" [(ngModel)]="end" required />
              </label>
            </div>
            <label class="field">
              <span>{{ 'form.price' | t }}</span>
              <input name="price" type="number" min="0" step="100" [(ngModel)]="price" required />
            </label>
          </fieldset>

          <fieldset>
            <legend>{{ 'form.media' | t }}</legend>
            <label class="field">
              <span>{{ 'form.image' | t }}</span>
              <input name="image" type="url" [(ngModel)]="model['image_url']" placeholder="https://" />
            </label>
            <label class="field">
              <span>{{ 'form.source' | t }}</span>
              <input name="source" type="url" [(ngModel)]="model['source_url']" placeholder="https://" />
            </label>
            <label class="field">
              <span>{{ 'form.nftImage' | t }}</span>
              <input name="nftImage" type="url" [(ngModel)]="model['nft_image_url']" placeholder="https://" />
              <small>{{ 'form.nftImageHint' | t }}</small>
            </label>
          </fieldset>

          @for (message of errors(); track message) {
            <p class="form-error" role="alert">{{ message }}</p>
          }

          <div class="form__actions">
            <button class="btn" type="submit" [disabled]="form.invalid || busy()">{{ 'form.save' | t }}</button>
            <a class="btn btn--ghost" routerLink="/organizer">{{ 'form.cancel' | t }}</a>
          </div>
        </form>
      }
    </div>
  `,
})
export class EventForm {
  private api = inject(EventsApi);
  private i18n = inject(I18n);
  private router = inject(Router);

  /** Параметр маршрута /organizer/events/:id/edit; при создании его нет */
  readonly id = input<string>();
  protected readonly isEdit = computed(() => !!this.id());

  protected readonly languages: { code: Lang; label: string }[] = [
    { code: 'en', label: 'English' },
    { code: 'ru', label: 'Русский' },
    { code: 'kk', label: 'Қазақша' },
  ];
  protected readonly tab = signal<Lang>('en');

  protected model: Record<string, string> = {
    title_en: '', title_ru: '', title_kk: '',
    description_en: '', description_ru: '', description_kk: '',
    image_url: '', source_url: '', nft_image_url: '',
  };
  protected categoryId: number | null = null;
  protected venueId: number | null = null;
  protected start = '';
  protected end = '';
  protected price = 0;

  protected venueName = '';
  protected venueAddress = '';
  protected readonly addingVenue = signal(false);

  protected readonly categories = signal<Category[]>([]);
  protected readonly venues = signal<Venue[]>([]);
  protected readonly ready = signal(false);
  protected readonly loadError = signal(false);
  protected readonly busy = signal(false);
  protected readonly errors = signal<string[]>([]);

  constructor() {
    effect(() => {
      this.i18n.lang();
      this.api.categories().subscribe({ next: (items) => this.categories.set(items), error: () => {} });
    });
    this.api.venues().subscribe({ next: (items) => this.venues.set(items), error: () => {} });

    effect(() => {
      const id = this.id();
      if (!id) {
        this.ready.set(true);
        return;
      }
      this.api.get(Number(id)).subscribe({
        next: (event) => {
          for (const key of Object.keys(this.model)) {
            this.model[key] = String((event as unknown as Record<string, unknown>)[key] ?? '');
          }
          this.categoryId = event.category.id;
          this.venueId = event.venue.id;
          this.start = toLocalInput(event.start_at);
          this.end = toLocalInput(event.end_at);
          this.price = Number(event.price);
          this.ready.set(true);
        },
        error: () => this.loadError.set(true),
      });
    });
  }

  protected saveVenue(): void {
    this.api.createVenue({ name: this.venueName.trim(), address: this.venueAddress.trim() }).subscribe({
      next: (venue) => {
        this.venues.update((items) => [...items, venue]);
        this.venueId = venue.id;
        this.venueName = '';
        this.venueAddress = '';
        this.addingVenue.set(false);
      },
      error: (error: HttpErrorResponse) => this.errors.set(this.describe(error)),
    });
  }

  protected save(): void {
    this.errors.set([]);
    if (new Date(this.end) < new Date(this.start)) {
      this.errors.set([this.i18n.t('form.endBeforeStart')]);
      return;
    }
    const payload = {
      ...this.model,
      category_id: this.categoryId,
      venue_id: this.venueId,
      start_at: new Date(this.start).toISOString(),
      end_at: new Date(this.end).toISOString(),
      price: String(this.price ?? 0),
    } as unknown as EventPayload;

    this.busy.set(true);
    const id = this.id();
    const request = id ? this.api.updateEvent(Number(id), payload) : this.api.createEvent(payload);
    request.subscribe({
      next: () => this.router.navigate(['/organizer'], { queryParams: { notice: id ? 'updated' : 'created' } }),
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.errors.set(this.describe(error));
      },
    });
  }

  private describe(error: HttpErrorResponse): string[] {
    const body = error.error;
    if (error.status === 400 && body && typeof body === 'object') {
      return Object.entries(body as Record<string, string[] | string>).map(
        ([field, messages]) => `${field}: ${[messages].flat().join(' ')}`,
      );
    }
    return [this.i18n.t('common.error')];
  }
}
