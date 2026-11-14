import { Routes } from '@angular/router';
import { authGuard } from './core/auth';
import { AuthPage } from './pages/auth-page';
import { Catalog } from './pages/catalog';
import { Checkin } from './pages/checkin';
import { EventDetail } from './pages/event-detail';
import { EventQr } from './pages/event-qr';
import { Favorites } from './pages/favorites';
import { EventForm } from './pages/event-form';
import { OrganizerCabinet } from './pages/organizer-cabinet';
import { Profile } from './pages/profile';
import { Scan } from './pages/scan';
import { Search } from './pages/search';
import { Visits } from './pages/visits';

export const routes: Routes = [
  { path: '', component: Catalog },
  { path: 'events/:id', component: EventDetail },
  { path: 'events/:id/qr', component: EventQr, canActivate: [authGuard] },
  { path: 'organizer', component: OrganizerCabinet, canActivate: [authGuard] },
  { path: 'organizer/events/new', component: EventForm, canActivate: [authGuard] },
  { path: 'organizer/events/:id/edit', component: EventForm, canActivate: [authGuard] },
  { path: 'search', component: Search },
  { path: 'scan', component: Scan, canActivate: [authGuard] },
  { path: 'checkin/:token', component: Checkin, canActivate: [authGuard] },
  { path: 'visits', component: Visits, canActivate: [authGuard] },
  { path: 'login', component: AuthPage, data: { mode: 'login' } },
  { path: 'register', component: AuthPage, data: { mode: 'register' } },
  { path: 'favorites', component: Favorites, canActivate: [authGuard] },
  { path: 'profile', component: Profile, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
