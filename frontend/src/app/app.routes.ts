import { Routes } from '@angular/router';
import { authGuard } from './core/auth';
import { AuthPage } from './pages/auth-page';
import { Catalog } from './pages/catalog';
import { EventDetail } from './pages/event-detail';
import { Favorites } from './pages/favorites';
import { Profile } from './pages/profile';
import { Search } from './pages/search';

export const routes: Routes = [
  { path: '', component: Catalog },
  { path: 'events/:id', component: EventDetail },
  { path: 'search', component: Search },
  { path: 'login', component: AuthPage, data: { mode: 'login' } },
  { path: 'register', component: AuthPage, data: { mode: 'register' } },
  { path: 'favorites', component: Favorites, canActivate: [authGuard] },
  { path: 'profile', component: Profile, canActivate: [authGuard] },
  { path: '**', redirectTo: '' },
];
