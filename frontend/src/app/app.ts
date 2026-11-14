import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { Auth } from './core/auth';
import { I18n, TPipe } from './core/i18n';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive, FormsModule, TPipe],
  template: `
    <header class="topbar">
      <div class="container topbar__inner">
        <a routerLink="/" class="logo" aria-label="AlmaPass">
          <span class="logo__mark" aria-hidden="true"></span>AlmaPass
        </a>

        <nav class="nav">
          <a routerLink="/" routerLinkActive="is-active" [routerLinkActiveOptions]="{ exact: true }">{{ 'nav.events' | t }}</a>
          @if (auth.isLoggedIn()) {
            <a routerLink="/favorites" routerLinkActive="is-active">{{ 'nav.favorites' | t }}</a>
            <a routerLink="/profile" routerLinkActive="is-active">{{ 'nav.profile' | t }}</a>
          }
        </nav>

        <form class="search-box" role="search" (ngSubmit)="search()">
          <svg viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">
            <circle cx="11" cy="11" r="7" /><path d="m20 20-3.8-3.8" />
          </svg>
          <input
            type="search"
            name="q"
            [(ngModel)]="query"
            [placeholder]="'nav.search' | t"
            [attr.aria-label]="'nav.search' | t"
          />
        </form>

        <div class="topbar__right">
          <div class="lang" role="group" aria-label="Language">
            @for (item of i18n.languages; track item.code) {
              <button type="button" [class.is-active]="i18n.lang() === item.code" (click)="i18n.set(item.code)">
                {{ item.label }}
              </button>
            }
          </div>
          @if (auth.user(); as user) {
            <span class="topbar__user">{{ user.username }}</span>
            <button type="button" class="btn btn--ghost" (click)="logout()">{{ 'nav.logout' | t }}</button>
          } @else {
            <a routerLink="/login" class="btn btn--ghost">{{ 'nav.login' | t }}</a>
            <a routerLink="/register" class="btn">{{ 'nav.register' | t }}</a>
          }
        </div>
      </div>
    </header>

    <main><router-outlet /></main>

    <footer class="footer">
      <div class="container">{{ 'footer.text' | t }}</div>
    </footer>
  `,
})
export class App {
  protected auth = inject(Auth);
  protected i18n = inject(I18n);
  private router = inject(Router);

  protected query = '';

  protected search(): void {
    const q = this.query.trim();
    if (q) this.router.navigate(['/search'], { queryParams: { q } });
  }

  protected logout(): void {
    this.auth.logout();
    this.router.navigateByUrl('/');
  }
}
