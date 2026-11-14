import { HttpClient, HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { Injectable, computed, inject, signal } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { Observable, catchError, switchMap, tap, throwError } from 'rxjs';
import { API_URL } from './config';
import { I18n } from './i18n';
import { User } from './models';

const ACCESS_KEY = 'almapass.access';
const REFRESH_KEY = 'almapass.refresh';

function read(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function write(key: string, value: string | null): void {
  try {
    if (value === null) localStorage.removeItem(key);
    else localStorage.setItem(key, value);
  } catch {
    /* ignore */
  }
}

@Injectable({ providedIn: 'root' })
export class Auth {
  private http = inject(HttpClient);
  private i18n = inject(I18n);

  readonly user = signal<User | null>(null);
  readonly isLoggedIn = computed(() => this.user() !== null);
  private accessToken = read(ACCESS_KEY);

  get token(): string | null {
    return this.accessToken;
  }

  /** Вызывается при старте приложения: восстанавливает сессию по сохранённому токену. */
  restore(): void {
    if (this.accessToken) {
      this.loadMe().subscribe({ error: () => this.logout() });
    }
  }

  login(username: string, password: string): Observable<User> {
    return this.http
      .post<{ access: string; refresh: string }>(`${API_URL}/auth/login/`, { username, password })
      .pipe(
        tap((tokens) => this.setTokens(tokens.access, tokens.refresh)),
        switchMap(() => this.loadMe()),
      );
  }

  register(username: string, email: string, password: string): Observable<User> {
    return this.http
      .post(`${API_URL}/auth/register/`, { username, email, password, language: this.i18n.lang() })
      .pipe(switchMap(() => this.login(username, password)));
  }

  refresh(): Observable<{ access: string }> {
    return this.http
      .post<{ access: string }>(`${API_URL}/auth/refresh/`, { refresh: read(REFRESH_KEY) })
      .pipe(tap((res) => this.setTokens(res.access, read(REFRESH_KEY))));
  }

  hasRefreshToken(): boolean {
    return read(REFRESH_KEY) !== null;
  }

  update(changes: Partial<User>): Observable<User> {
    return this.http.patch<User>(`${API_URL}/auth/me/`, changes).pipe(tap((user) => this.user.set(user)));
  }

  /** Перечитывает профиль с сервера, например после получения роли организатора. */
  reload(): Observable<User> {
    return this.loadMe();
  }

  logout(): void {
    this.setTokens(null, null);
    this.user.set(null);
  }

  private loadMe(): Observable<User> {
    return this.http.get<User>(`${API_URL}/auth/me/`).pipe(tap((user) => this.user.set(user)));
  }

  private setTokens(access: string | null, refresh: string | null): void {
    this.accessToken = access;
    write(ACCESS_KEY, access);
    write(REFRESH_KEY, refresh);
  }
}

/** Добавляет токен и язык к запросам; при истёкшем токене один раз обновляет его. */
export const apiInterceptor: HttpInterceptorFn = (req, next) => {
  if (!req.url.startsWith(API_URL)) return next(req);

  const auth = inject(Auth);
  const i18n = inject(I18n);
  const isAuthCall = /\/auth\/(login|register|refresh)\/$/.test(req.url);

  const withHeaders = (token: string | null) => {
    const headers: Record<string, string> = { 'Accept-Language': i18n.lang() };
    if (token && !isAuthCall) headers['Authorization'] = `Bearer ${token}`;
    return req.clone({ setHeaders: headers });
  };

  return next(withHeaders(auth.token)).pipe(
    catchError((error: HttpErrorResponse) => {
      if (error.status !== 401 || isAuthCall || !auth.hasRefreshToken()) return throwError(() => error);
      return auth.refresh().pipe(
        switchMap((res) => next(withHeaders(res.access))),
        catchError((refreshError) => {
          auth.logout();
          return throwError(() => refreshError);
        }),
      );
    }),
  );
};

export const authGuard: CanActivateFn = (_route, state) => {
  const auth = inject(Auth);
  return auth.token ? true : inject(Router).createUrlTree(['/login'], { queryParams: { next: state.url } });
};
