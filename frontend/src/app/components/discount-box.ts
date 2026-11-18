import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, effect, inject, input, linkedSignal, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { I18n, TPipe } from '../core/i18n';
import { EventItem, LoyaltyInfo } from '../core/models';

/** Блок «Скидка для владельцев NFT» на странице платного события. */
@Component({
  selector: 'app-discount-box',
  imports: [RouterLink, TPipe],
  template: `
    @let item = event();
    <div class="discount">
      <strong class="discount__title">{{ 'discount.title' | t }}</strong>

      @if (code(); as current) {
        <span class="discount__label">{{ 'discount.yourCode' | t }}</span>
        <div class="discount__code" [class.is-used]="current.status === 'used'">{{ current.code }}</div>
        <span class="tag" [class.tag--fail]="current.status === 'used'">
          −{{ current.discount_percent }}% · {{ (current.status === 'used' ? 'discount.used' : 'discount.active') | t }}
        </span>
        <p>{{ 'discount.price' | t: { final: money(finalPrice(current.discount_percent)), price: money(item.price) } }}</p>
        <p class="muted">{{ 'discount.show' | t }}</p>
      } @else if (loyalty(); as data) {
        @if (!auth.isLoggedIn()) {
          <p>{{ 'discount.guest' | t: { percent: maxPercent() } }}</p>
          <a class="link" routerLink="/login">{{ 'nav.login' | t }} →</a>
        } @else if (myPercent()) {
          <p>{{ 'discount.eligible' | t: { level: data.current_level!.name, percent: myPercent() } }}</p>
          <p class="discount__price">
            {{ 'discount.price' | t: { final: money(finalPrice(myPercent())), price: money(item.price) } }}
          </p>
          <button type="button" class="btn btn--block" [disabled]="busy()" (click)="getCode()">{{ 'discount.get' | t }}</button>
        } @else if (firstDiscount(); as target) {
          <p>{{ 'discount.locked' | t: { count: target.min_nfts - (data.nft_count ?? 0), percent: target.discount_percent } }}</p>
          <a class="link" routerLink="/visits">{{ 'discount.levelsLink' | t }} →</a>
        }
      }

      @if (errorKey(); as key) {
        <p class="form-error" role="alert">{{ key | t }}</p>
      }
    </div>
  `,
})
export class DiscountBox {
  protected auth = inject(Auth);
  private api = inject(EventsApi);
  private i18n = inject(I18n);

  readonly event = input.required<EventItem>();

  protected readonly code = linkedSignal(() => this.event().my_discount);
  protected readonly loyalty = signal<LoyaltyInfo | null>(null);
  protected readonly busy = signal(false);
  protected readonly errorKey = signal('');

  protected readonly myPercent = computed(() => this.loyalty()?.current_level?.discount_percent ?? 0);
  protected readonly firstDiscount = computed(() => this.loyalty()?.levels.find((level) => level.discount_percent > 0));
  protected readonly maxPercent = computed(() => Math.max(0, ...(this.loyalty()?.levels ?? []).map((l) => l.discount_percent)));

  constructor() {
    effect(() => {
      this.i18n.lang();
      this.auth.isLoggedIn();
      this.api.loyalty().subscribe({ next: (data) => this.loyalty.set(data), error: () => {} });
    });
  }

  protected getCode(): void {
    this.busy.set(true);
    this.errorKey.set('');
    this.api.getDiscount(this.event().id).subscribe({
      next: (item) => {
        this.busy.set(false);
        this.code.set({ code: item.code, status: item.status, discount_percent: item.discount_percent });
      },
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        const code = error.error?.code;
        this.errorKey.set(
          ['level_too_low', 'ended', 'not_offered'].includes(code) ? `discount.error.${code}` : 'common.error',
        );
      },
    });
  }

  protected finalPrice(percent: number): number {
    return Math.round((Number(this.event().price) * (100 - percent)) / 100);
  }

  protected money(value: number | string): string {
    return Number(value).toLocaleString('ru-RU');
  }
}
