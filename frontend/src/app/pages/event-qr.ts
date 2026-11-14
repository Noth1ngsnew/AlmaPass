import { Component, OnDestroy, computed, effect, inject, input, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import QRCode from 'qrcode';
import { EventsApi } from '../core/events-api';
import { I18n, TPipe } from '../core/i18n';
import { CheckinCode, EventItem } from '../core/models';

@Component({
  selector: 'app-event-qr',
  imports: [RouterLink, TPipe],
  template: `
    <div class="container page page--narrow">
      <a [routerLink]="['/events', id()]" class="back">← {{ event()?.title }}</a>
      <h1 class="page__title">{{ 'qr.title' | t }}</h1>

      @if (denied()) {
        <p class="state state--error">{{ 'qr.denied' | t }}</p>
      } @else if (code(); as data) {
        <div class="panel qr">
          <p class="muted">{{ 'qr.text' | t }}</p>
          @if (!data.is_published) {
            <p class="form-error">{{ 'qr.notPublished' | t }}</p>
          }

          <div class="qr__body">
            @if (image()) {
              <img class="qr__image" [src]="image()" [alt]="'qr.title' | t" width="320" height="320" />
            }
            <div class="qr__side">
              <div class="qr__counter">
                <strong>{{ data.visits_count }}</strong>
                <span>{{ 'qr.visits' | t }}</span>
              </div>
              <dl class="facts">
                <div>
                  <dt>{{ 'qr.code' | t }}</dt>
                  <dd class="mono">{{ data.token }}</dd>
                </div>
                <div>
                  <dt>{{ 'qr.link' | t }}</dt>
                  <dd class="mono">{{ link() }}</dd>
                </div>
              </dl>
              <button type="button" class="btn btn--ghost" (click)="copy()">
                {{ (copied() ? 'qr.copied' : 'qr.copy') | t }}
              </button>
            </div>
          </div>

          @if (isLocalhost) {
            <p class="muted qr__hint">{{ 'qr.localhostHint' | t }}</p>
          }
        </div>
      } @else {
        <p class="state">{{ 'common.loading' | t }}</p>
      }
    </div>
  `,
})
export class EventQr implements OnDestroy {
  private api = inject(EventsApi);
  private i18n = inject(I18n);

  /** Параметр маршрута /events/:id/qr */
  readonly id = input.required<string>();

  protected readonly event = signal<EventItem | null>(null);
  protected readonly code = signal<CheckinCode | null>(null);
  protected readonly image = signal('');
  protected readonly denied = signal(false);
  protected readonly copied = signal(false);
  protected readonly link = computed(() => `${window.location.origin}/checkin/${this.code()?.token ?? ''}`);
  protected readonly isLocalhost = ['localhost', '127.0.0.1'].includes(window.location.hostname);

  private timer: ReturnType<typeof setInterval> | null = null;

  constructor() {
    effect((onCleanup) => {
      this.i18n.lang();
      const sub = this.api.get(Number(this.id())).subscribe({ next: (item) => this.event.set(item), error: () => {} });
      onCleanup(() => sub.unsubscribe());
    });

    effect(() => {
      const eventId = Number(this.id());
      this.load(eventId, true);
      // Счётчик отметившихся обновляется сам, пока страница открыта
      if (this.timer) clearInterval(this.timer);
      this.timer = setInterval(() => this.load(eventId, false), 5000);
    });
  }

  private load(eventId: number, first: boolean): void {
    this.api.checkinCode(eventId).subscribe({
      next: (data) => {
        this.code.set(data);
        if (first) {
          QRCode.toDataURL(this.link(), { width: 640, margin: 1, color: { dark: '#17231d', light: '#ffffff' } })
            .then((url) => this.image.set(url))
            .catch(() => {});
        }
      },
      error: () => {
        if (first) this.denied.set(true);
      },
    });
  }

  protected copy(): void {
    navigator.clipboard
      ?.writeText(this.link())
      .then(() => {
        this.copied.set(true);
        setTimeout(() => this.copied.set(false), 2000);
      })
      .catch(() => {});
  }

  ngOnDestroy(): void {
    if (this.timer) clearInterval(this.timer);
  }
}
