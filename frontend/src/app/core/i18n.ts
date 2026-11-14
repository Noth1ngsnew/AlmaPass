import { Injectable, Pipe, PipeTransform, inject, signal } from '@angular/core';
import { Lang } from './models';
import { TRANSLATIONS } from './translations';

const STORAGE_KEY = 'almapass.lang';

@Injectable({ providedIn: 'root' })
export class I18n {
  readonly languages: { code: Lang; label: string }[] = [
    { code: 'en', label: 'EN' },
    { code: 'ru', label: 'RU' },
    { code: 'kk', label: 'KZ' },
  ];
  readonly lang = signal<Lang>(this.initial());

  set(lang: Lang): void {
    this.lang.set(lang);
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch {
      /* хранилище может быть недоступно */
    }
    document.documentElement.lang = lang;
  }

  /** Перевод по ключу; если перевода нет, показывается английский текст. */
  t(key: string, params?: Record<string, string | number>): string {
    let text = TRANSLATIONS[this.lang()][key] ?? TRANSLATIONS.en[key] ?? key;
    for (const [name, value] of Object.entries(params ?? {})) {
      text = text.replace(`{${name}}`, String(value));
    }
    return text;
  }

  /** Локаль для дат и чисел. */
  locale(): string {
    return { en: 'en-GB', ru: 'ru-RU', kk: 'kk-KZ' }[this.lang()];
  }

  private initial(): Lang {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'en' || saved === 'ru' || saved === 'kk') return saved;
    } catch {
      /* ignore */
    }
    return 'en';
  }
}

@Pipe({ name: 't', pure: false })
export class TPipe implements PipeTransform {
  private i18n = inject(I18n);

  transform(key: string, params?: Record<string, string | number>): string {
    return this.i18n.t(key, params);
  }
}

/** Дата в формате текущего языка: «14 ноября, 19:00». */
@Pipe({ name: 'eventDate', pure: false })
export class EventDatePipe implements PipeTransform {
  private i18n = inject(I18n);

  transform(value: string, mode: 'full' | 'day' | 'time' = 'full'): string {
    const date = new Date(value);
    const options: Intl.DateTimeFormatOptions =
      mode === 'day'
        ? { day: 'numeric', month: 'short' }
        : mode === 'time'
          ? { hour: '2-digit', minute: '2-digit' }
          : { weekday: 'short', day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' };
    return new Intl.DateTimeFormat(this.i18n.locale(), options).format(date);
  }
}
