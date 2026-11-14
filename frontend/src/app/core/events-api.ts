import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './config';
import { Category, EventFilters, EventItem, Page } from './models';

@Injectable({ providedIn: 'root' })
export class EventsApi {
  private http = inject(HttpClient);

  categories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${API_URL}/categories/`);
  }

  list(filters: EventFilters = {}): Observable<Page<EventItem>> {
    let params = new HttpParams();
    if (filters.category) params = params.set('category', filters.category);
    if (filters.date_from) params = params.set('date_from', filters.date_from);
    if (filters.date_to) params = params.set('date_to', filters.date_to);
    if (filters.free) params = params.set('free', '1');
    if (filters.page && filters.page > 1) params = params.set('page', filters.page);
    return this.http.get<Page<EventItem>>(`${API_URL}/events/`, { params });
  }

  get(id: number): Observable<EventItem> {
    return this.http.get<EventItem>(`${API_URL}/events/${id}/`);
  }

  favorites(): Observable<Page<EventItem>> {
    return this.http.get<Page<EventItem>>(`${API_URL}/favorites/`);
  }

  setFavorite(id: number, value: boolean): Observable<{ is_favorite: boolean }> {
    const url = `${API_URL}/events/${id}/favorite/`;
    return value
      ? this.http.post<{ is_favorite: boolean }>(url, {})
      : this.http.delete<{ is_favorite: boolean }>(url);
  }
}
