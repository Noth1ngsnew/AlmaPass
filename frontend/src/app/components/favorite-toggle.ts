import { Component, booleanAttribute, inject, input, linkedSignal, output } from '@angular/core';
import { Router } from '@angular/router';
import { Auth } from '../core/auth';
import { EventsApi } from '../core/events-api';
import { TPipe } from '../core/i18n';
import { EventItem } from '../core/models';

@Component({
  selector: 'app-favorite-toggle',
  imports: [TPipe],
  template: `
    @let label = (active() ? 'event.removeFavorite' : 'event.addFavorite') | t;
    <button
      type="button"
      class="fav"
      [class.fav--compact]="compact()"
      [class.is-active]="active()"
      [attr.aria-pressed]="active()"
      [attr.aria-label]="label"
      [title]="label"
      (click)="toggle()"
    >
      <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
        <path d="M12 20.5s-7.5-4.6-7.5-10.2A4.3 4.3 0 0 1 12 7.6a4.3 4.3 0 0 1 7.5 2.7c0 5.6-7.5 10.2-7.5 10.2z" />
      </svg>
      @if (!compact()) {
        <span>{{ label }}</span>
      }
    </button>
  `,
})
export class FavoriteToggle {
  private api = inject(EventsApi);
  private auth = inject(Auth);
  private router = inject(Router);

  readonly event = input.required<EventItem>();
  readonly compact = input(false, { transform: booleanAttribute });
  readonly changed = output<boolean>();

  protected readonly active = linkedSignal(() => this.event().is_favorite);

  protected toggle(): void {
    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/login'], { queryParams: { next: this.router.url } });
      return;
    }
    const next = !this.active();
    this.active.set(next); // сразу меняем вид, при ошибке откатываем
    this.api.setFavorite(this.event().id, next).subscribe({
      next: () => this.changed.emit(next),
      error: () => this.active.set(!next),
    });
  }
}
