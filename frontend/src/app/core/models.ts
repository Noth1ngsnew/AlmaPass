export type Lang = 'en' | 'ru' | 'kk';
export type Role = 'user' | 'organizer' | 'admin';

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
  wallet_address: string;
  language: Lang;
  avatar_url: string;
  organizer_id: number | null;
}

export interface Category {
  id: number;
  slug: string;
  name: string;
}

export interface Venue {
  id: number;
  name: string;
  address: string;
  latitude: string | null;
  longitude: string | null;
  website: string;
}

export interface Organizer {
  id: number;
  name: string;
  description: string;
  website: string;
  is_verified: boolean;
}

export interface EventItem {
  id: number;
  title: string;
  description: string;
  category: Category;
  venue: Venue;
  organizer: Organizer;
  start_at: string;
  end_at: string;
  price: string;
  image_url: string;
  source_url: string;
  nft_image_url: string;
  status: 'draft' | 'pending' | 'published' | 'rejected';
  is_favorite: boolean;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface EventFilters {
  category?: string;
  date_from?: string;
  date_to?: string;
  free?: boolean;
  page?: number;
}
