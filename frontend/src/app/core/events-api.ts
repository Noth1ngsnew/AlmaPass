import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './config';
import {
  Category,
  CheckinCode,
  EventFilters,
  EventItem,
  EventPayload,
  Organizer,
  Page,
  SearchResult,
  Venue,
  Visit,
} from './models';

@Injectable({ providedIn: 'root' })
export class EventsApi {
  private http = inject(HttpClient);

  categories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${API_URL}/categories/`);
  }

  list(filters: EventFilters = {}): Observable<Page<EventItem>> {
    let params = new HttpParams();
    if (filters.category) params = params.set('category', filters.category);
    if (filters.venue) params = params.set('venue', filters.venue);
    if (filters.organizer) params = params.set('organizer', filters.organizer);
    if (filters.date_from) params = params.set('date_from', filters.date_from);
    if (filters.date_to) params = params.set('date_to', filters.date_to);
    if (filters.free) params = params.set('free', '1');
    if (filters.page && filters.page > 1) params = params.set('page', filters.page);
    return this.http.get<Page<EventItem>>(`${API_URL}/events/`, { params });
  }

  get(id: number): Observable<EventItem> {
    return this.http.get<EventItem>(`${API_URL}/events/${id}/`);
  }

  search(query: string): Observable<SearchResult> {
    return this.http.get<SearchResult>(`${API_URL}/search/`, { params: { q: query } });
  }

  venue(id: string): Observable<Venue> {
    return this.http.get<Venue>(`${API_URL}/venues/${id}/`);
  }

  organizer(id: string): Observable<Organizer> {
    return this.http.get<Organizer>(`${API_URL}/organizers/${id}/`);
  }

  checkin(token: string): Observable<Visit> {
    return this.http.post<Visit>(`${API_URL}/checkin/`, { token });
  }

  visits(): Observable<Page<Visit>> {
    return this.http.get<Page<Visit>>(`${API_URL}/visits/`, { params: { page_size: '100' } });
  }

  claimNft(visitId: number): Observable<Visit> {
    return this.http.post<Visit>(`${API_URL}/visits/${visitId}/claim/`, {});
  }

  checkinCode(eventId: number): Observable<CheckinCode> {
    return this.http.get<CheckinCode>(`${API_URL}/events/${eventId}/checkin-code/`);
  }

  venues(): Observable<Venue[]> {
    return this.http.get<Venue[]>(`${API_URL}/venues/`);
  }

  createVenue(data: { name: string; address: string }): Observable<Venue> {
    return this.http.post<Venue>(`${API_URL}/venues/`, data);
  }

  myOrganizer(): Observable<Organizer> {
    return this.http.get<Organizer>(`${API_URL}/organizers/me/`);
  }

  applyOrganizer(data: { name: string; description: string; website: string }): Observable<Organizer> {
    return this.http.post<Organizer>(`${API_URL}/organizers/apply/`, data);
  }

  myEvents(): Observable<Page<EventItem>> {
    return this.http.get<Page<EventItem>>(`${API_URL}/events/`, { params: { mine: '1', page_size: '100' } });
  }

  createEvent(data: EventPayload): Observable<EventItem> {
    return this.http.post<EventItem>(`${API_URL}/events/`, data);
  }

  updateEvent(id: number, data: EventPayload): Observable<EventItem> {
    return this.http.patch<EventItem>(`${API_URL}/events/${id}/`, data);
  }

  deleteEvent(id: number): Observable<void> {
    return this.http.delete<void>(`${API_URL}/events/${id}/`);
  }

  favorites(): Observable<Page<EventItem>> {
    return this.http.get<Page<EventItem>>(`${API_URL}/favorites/`, { params: { page_size: '100' } });
  }

  setFavorite(id: number, value: boolean): Observable<{ is_favorite: boolean }> {
    const url = `${API_URL}/events/${id}/favorite/`;
    return value
      ? this.http.post<{ is_favorite: boolean }>(url, {})
      : this.http.delete<{ is_favorite: boolean }>(url);
  }
}
