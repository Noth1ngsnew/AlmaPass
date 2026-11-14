import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, inject, input, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Auth } from '../core/auth';
import { I18n, TPipe } from '../core/i18n';

@Component({
  selector: 'app-auth-page',
  imports: [FormsModule, RouterLink, TPipe],
  template: `
    <div class="container auth">
      <form class="panel auth__form" (ngSubmit)="submit()" #form="ngForm">
        <h1>{{ (isRegister() ? 'auth.registerTitle' : 'auth.loginTitle') | t }}</h1>

        <label class="field">
          <span>{{ 'auth.username' | t }}</span>
          <input name="username" [(ngModel)]="username" required autocomplete="username" />
        </label>

        @if (isRegister()) {
          <label class="field">
            <span>{{ 'auth.email' | t }}</span>
            <input name="email" type="email" [(ngModel)]="email" required email autocomplete="email" />
          </label>
        }

        <label class="field">
          <span>{{ 'auth.password' | t }}</span>
          <input
            name="password"
            type="password"
            [(ngModel)]="password"
            required
            [attr.minlength]="isRegister() ? 8 : null"
            [autocomplete]="isRegister() ? 'new-password' : 'current-password'"
          />
          @if (isRegister()) {
            <small>{{ 'auth.passwordHint' | t }}</small>
          }
        </label>

        @for (message of errors(); track message) {
          <p class="form-error" role="alert">{{ message }}</p>
        }

        <button class="btn btn--block" type="submit" [disabled]="form.invalid || busy()">
          {{ (isRegister() ? 'auth.registerButton' : 'auth.loginButton') | t }}
        </button>

        <p class="auth__switch">
          @if (isRegister()) {
            {{ 'auth.haveAccount' | t }} <a routerLink="/login" queryParamsHandling="preserve">{{ 'nav.login' | t }}</a>
          } @else {
            {{ 'auth.noAccount' | t }} <a routerLink="/register" queryParamsHandling="preserve">{{ 'nav.register' | t }}</a>
          }
        </p>
      </form>
    </div>
  `,
})
export class AuthPage {
  private auth = inject(Auth);
  private i18n = inject(I18n);
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  /** Берётся из data маршрута: 'login' или 'register' */
  readonly mode = input<'login' | 'register'>('login');
  protected readonly isRegister = computed(() => this.mode() === 'register');

  protected username = '';
  protected email = '';
  protected password = '';
  protected readonly busy = signal(false);
  protected readonly errors = signal<string[]>([]);

  protected submit(): void {
    this.busy.set(true);
    this.errors.set([]);
    const request = this.isRegister()
      ? this.auth.register(this.username.trim(), this.email.trim(), this.password)
      : this.auth.login(this.username.trim(), this.password);

    request.subscribe({
      next: () => this.router.navigateByUrl(this.route.snapshot.queryParamMap.get('next') || '/'),
      error: (error: HttpErrorResponse) => {
        this.busy.set(false);
        this.errors.set(this.describe(error));
      },
    });
  }

  /** Превращает ответ Django вида {"field": ["message"]} в список строк. */
  private describe(error: HttpErrorResponse): string[] {
    if (error.status === 401) return [this.i18n.t('auth.badCredentials')];
    if (error.status === 400 && error.error && typeof error.error === 'object') {
      return Object.values(error.error as Record<string, string[] | string>).flat().map(String);
    }
    return [this.i18n.t('common.error')];
  }
}
