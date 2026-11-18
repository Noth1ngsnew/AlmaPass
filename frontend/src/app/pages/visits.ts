import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnDestroy, computed, effect, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { LevelCard } from '../components/level-card';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { EventDatePipe, I18n, TPipe } from '../core/i18n';
import { DiscountCode, LoyaltyInfo, Visit } from '../core/models';

@Component({
  selector: 'app-visits',
  imports: [RouterLink, TPipe, EventDatePipe, LevelCard],
  template: `
    <div class="container page">
      <h1 class="page__title">{{ 'visits.title' | t }}</h1>

      @if (loyalty(); as info) {
        <app-level-card [info]="info" />
      }

      @if (error()) {
        <p class="state state--error">{{ 'common.error' | t }}</p>
      } @else if (loading()) {
        <p class="state">{{ 'common.loading' | t }}</p>
      } @else if (!visits().length) {
        <p class="state">{{ 'visits.empty' | t }}</p>
        <p class="center"><a class="btn" routerLink="/scan">{{ 'nav.scan' | t }}</a></p>
      } @else {
        <p class="count">{{ 'visits.stats' | t: { visits: visits().length, nfts: mintedCount() } }}</p>

        @if (notice(); as key) {
          <p class="form-error" role="alert">
            {{ key | t }}
            @if (key === 'visits.needWallet') {
              <a routerLink="/profile">{{ 'visits.addWallet' | t }} →</a>
            }
          </p>
        }

        <div class="grid grid--nft">
          @for (visit of visits(); track visit.id) {
            @let status = visit.nft_reward?.status ?? 'pending';
            <article class="nft-card" [class.is-minted]="status === 'minted'">
              <a class="nft-card__media" [routerLink]="['/events', visit.event.id]">
                @if (visit.event.nft_image_url || visit.event.image_url; as src) {
                  <img [src]="src" [alt]="visit.event.title" loading="lazy" (error)="hide($event)" />
                }
                <span class="nft-card__seal" aria-hidden="true">NFT</span>
              </a>
              <div class="nft-card__body">
                <span
                  class="tag"
                  [class.tag--warn]="status === 'pending' || status === 'minting'"
                  [class.tag--fail]="status === 'failed'"
                >
                  @if (status === 'minting') {
                    <span class="spinner" aria-hidden="true"></span>
                  }
                  {{ 'visits.nft.' + status | t }}
                </span>
                <h3 class="card__title">
                  <a [routerLink]="['/events', visit.event.id]">{{ visit.event.title }}</a>
                </h3>
                <p class="card__venue">
                  {{ visit.event.venue.name }} · {{ visit.checked_in_at | eventDate: 'day' }}
                </p>

                <div class="nft-card__foot">
                  @switch (status) {
                    @case ('minted') {
                      <strong>{{ 'visits.token' | t: { id: visit.nft_reward?.token_id ?? '' } }}</strong>
                      @if (visit.nft_reward?.explorer_url; as url) {
                        <a class="link" [href]="url" target="_blank" rel="noopener">{{ 'visits.explorer' | t }} ↗</a>
                      }
                    }
                    @case ('minting') {
                      <small class="muted">{{ 'visits.mintingHint' | t }}</small>
                    }
                    @default {
                      <button type="button" class="btn" [disabled]="busyId() === visit.id" (click)="claim(visit)">
                        {{ (status === 'failed' ? 'visits.retry' : 'visits.claim') | t }}
                      </button>
                    }
                  }
                </div>
              </div>
            </article>
          }
        </div>
      }

      <h2 class="results__title results__title--spaced">{{ 'loyalty.codes' | t }}</h2>
      @if (!discounts().length) {
        <p class="muted">{{ 'loyalty.codesEmpty' | t }}</p>
      } @else {
        <div class="rows">
          @for (item of discounts(); track item.id) {
            <a class="row" [routerLink]="['/events', item.event.id]">
              <span class="row__main">
                <strong class="mono">{{ item.code }}</strong>
                <small>{{ item.event.title }} · {{ item.event.start_at | eventDate: 'day' }}</small>
              </span>
              <span class="tag" [class.tag--fail]="item.status === 'used'">
                −{{ item.discount_percent }}% · {{ (item.status === 'used' ? 'discount.used' : 'discount.active') | t }}
              </span>
            </a>
          }
        </div>
      }
    </div>
  `,
})
export class Visits implements OnDestroy {
  private api = inject(EventsApi);
  private i18n = inject(I18n);
  private auth = inject(Auth);

  protected readonly visits = signal<Visit[]>([]);
  protected readonly loading = signal(true);
  protected readonly error = signal(false);
  protected readonly notice = signal('');
  protected readonly busyId = signal<number | null>(null);
  protected readonly loyalty = signal<LoyaltyInfo | null>(null);
  protected readonly discounts = signal<DiscountCode[]>([]);
  protected readonly mintedCount = computed(
    () => this.visits().filter((visit) => visit.nft_reward?.status === 'minted').length,
  );

  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor() {
    effect(() => {
      this.i18n.lang();
      this.load();
    });
  }

  private load(): void {
    this.api.loyalty().subscribe({ next: (data) => this.loyalty.set(data), error: () => {} });
    this.api.myDiscounts().subscribe({ next: (res) => this.discounts.set(res.results), error: () => {} });
    this.api.visits().subscribe({
      next: (res) => {
        this.visits.set(res.results);
        this.loading.set(false);
        this.error.set(false);
        this.scheduleRefresh();
      },
      error: () => {
        this.error.set(true);
        this.loading.set(false);
      },
    });
  }

  /** Пока хотя бы один NFT выдаётся, список сам обновляется каждые 4 секунды. */
  private scheduleRefresh(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = this.visits().some((visit) => visit.nft_reward?.status === 'minting')
      ? setTimeout(() => this.load(), 4000)
      : null;
  }

  protected claim(visit: Visit): void {
    this.notice.set('');
    if (!this.auth.user()?.wallet_address) {
      this.notice.set('visits.needWallet');
      return;
    }
    this.busyId.set(visit.id);
    this.api.claimNft(visit.id).subscribe({
      next: (updated) => {
        this.busyId.set(null);
        this.visits.update((items) => items.map((item) => (item.id === updated.id ? updated : item)));
        this.scheduleRefresh();
      },
      error: (error: HttpErrorResponse) => {
        this.busyId.set(null);
        const code = error.error?.code;
        this.notice.set(
          code === 'no_wallet' ? 'visits.needWallet' : code === 'not_configured' ? 'visits.notConfigured' : 'common.error',
        );
      },
    });
  }

  protected hide(event: Event): void {
    (event.target as HTMLElement).hidden = true;
  }

  ngOnDestroy(): void {
    if (this.timer) clearTimeout(this.timer);
  }
}
