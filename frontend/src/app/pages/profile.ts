import { HttpErrorResponse } from '@angular/common/http';
import { Component, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Auth } from '../core/auth';
import { I18n, TPipe } from '../core/i18n';
import { Lang } from '../core/models';

@Component({
  selector: 'app-profile',
  imports: [FormsModule, TPipe],
  template: `
    <div class="container page page--narrow">
      <h1 class="page__title">{{ 'profile.title' | t }}</h1>

      @if (auth.user(); as user) {
        <form class="panel" (ngSubmit)="save()">
          <div class="profile__head">
            <div class="avatar" aria-hidden="true">{{ user.username.charAt(0).toUpperCase() }}</div>
            <div>
              <strong>{{ user.username }}</strong>
              <div class="muted">{{ user.email }}</div>
            </div>
            <span class="tag">{{ 'profile.role.' + user.role | t }}</span>
          </div>

          <div class="form-row">
            <label class="field">
              <span>{{ 'profile.firstName' | t }}</span>
              <input name="firstName" [(ngModel)]="firstName" />
            </label>
            <label class="field">
              <span>{{ 'profile.lastName' | t }}</span>
              <input name="lastName" [(ngModel)]="lastName" />
            </label>
          </div>

          <label class="field">
            <span>{{ 'profile.wallet' | t }}</span>
            <input name="wallet" [(ngModel)]="wallet" placeholder="0x…" spellcheck="false" />
            <small>{{ 'profile.walletHint' | t }}</small>
          </label>

          <label class="field">
            <span>{{ 'profile.language' | t }}</span>
            <select name="language" [(ngModel)]="language">
              <option value="en">English</option>
              <option value="ru">Русский</option>
              <option value="kk">Қазақша</option>
            </select>
          </label>

          @for (message of errors(); track message) {
            <p class="form-error" role="alert">{{ message }}</p>
          }
          @if (saved()) {
            <p class="form-ok" role="status">{{ 'profile.saved' | t }}</p>
          }

          <button class="btn" type="submit" [disabled]="busy()">{{ 'profile.save' | t }}</button>
        </form>
      } @else {
        <p class="state">{{ 'common.loading' | t }}</p>
      }
    </div>
  `,
})
export class Profile {
  protected auth = inject(Auth);
  private i18n = inject(I18n);

  protected firstName = '';
  protected lastName = '';
  protected wallet = '';
  protected language: Lang = 'en';
  protected readonly busy = signal(false);
  protected readonly saved = signal(false);
  protected readonly errors = signal<string[]>([]);

  constructor() {
    // Заполняем форму, когда профиль загрузился
    effect(() => {
      const user = this.auth.user();
      if (!user) return;
      this.firstName = user.first_name;
      this.lastName = user.last_name;
      this.wallet = user.wallet_address;
      this.language = user.language;
    });
  }

  protected save(): void {
    this.busy.set(true);
    this.saved.set(false);
    this.errors.set([]);
    this.auth
      .update({
        first_name: this.firstName.trim(),
        last_name: this.lastName.trim(),
        wallet_address: this.wallet.trim(),
        language: this.language,
      })
      .subscribe({
        next: (user) => {
          this.busy.set(false);
          this.saved.set(true);
          this.i18n.set(user.language);
        },
        error: (error: HttpErrorResponse) => {
          this.busy.set(false);
          const body = error.error;
          this.errors.set(
            error.status === 400 && body && typeof body === 'object'
              ? Object.values(body as Record<string, string[]>).flat().map(String)
              : [this.i18n.t('common.error')],
          );
        },
      });
  }
}
