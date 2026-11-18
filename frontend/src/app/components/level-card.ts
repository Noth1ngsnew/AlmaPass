import { Component, computed, input } from '@angular/core';
import { TPipe } from '../core/i18n';
import { LoyaltyInfo } from '../core/models';

/** Текущий уровень, полоса прогресса до следующего и список всех уровней. */
@Component({
  selector: 'app-level-card',
  imports: [TPipe],
  template: `
    @let data = info();
    <section class="level">
      <div class="level__head">
        <div class="level__medal" [class]="'level__medal level__medal--' + medal()" aria-hidden="true">
          {{ data.nft_count ?? 0 }}
        </div>
        <div class="level__text">
          <span class="level__label">{{ 'loyalty.title' | t }}</span>
          <strong class="level__name">{{ data.current_level?.name || ('loyalty.noLevel' | t) }}</strong>
          <span class="muted">
            @if (data.current_level?.discount_percent) {
              {{ 'loyalty.discount' | t: { percent: data.current_level!.discount_percent } }}
            } @else {
              {{ 'loyalty.noDiscount' | t }}
            }
          </span>
        </div>
      </div>

      <div class="level__progress">
        <div
          class="level__bar"
          role="progressbar"
          [attr.aria-valuenow]="data.nft_count"
          [attr.aria-valuemax]="data.next_level?.min_nfts ?? data.nft_count"
        >
          <span [style.width.%]="percent()"></span>
        </div>
        <span class="muted">
          @if (data.next_level) {
            {{ 'loyalty.toNext' | t: { count: data.nfts_to_next ?? 0, level: data.next_level.name, percent: data.next_level.discount_percent } }}
          } @else {
            {{ 'loyalty.max' | t }}
          }
        </span>
      </div>

      <ol class="level__steps" [attr.aria-label]="'loyalty.levels' | t">
        @for (level of data.levels; track level.id) {
          <li [class.is-reached]="(data.nft_count ?? 0) >= level.min_nfts" [class.is-current]="data.current_level?.id === level.id">
            <strong>{{ level.name }}</strong>
            <span>{{ 'loyalty.from' | t: { count: level.min_nfts } }}</span>
            <span class="level__off">{{ level.discount_percent ? '−' + level.discount_percent + '%' : '—' }}</span>
          </li>
        }
      </ol>
    </section>
  `,
})
export class LevelCard {
  readonly info = input.required<LoyaltyInfo>();

  /** Заполнение полосы: сколько NFT собрано из нужных для следующего уровня */
  protected readonly percent = computed(() => {
    const data = this.info();
    const count = data.nft_count ?? 0;
    if (!data.next_level) return 100;
    return Math.max(4, Math.round((count / data.next_level.min_nfts) * 100));
  });

  /** Цвет медали: по порядковому номеру уровня */
  protected readonly medal = computed(() => {
    const data = this.info();
    const index = data.levels.findIndex((level) => level.id === data.current_level?.id);
    return ['bronze', 'silver', 'gold', 'platinum'][index] ?? 'none';
  });
}
