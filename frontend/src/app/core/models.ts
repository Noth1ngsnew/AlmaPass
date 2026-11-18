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
  loyalty: { nft_count: number; level: string; discount_percent: number };
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
  title_en: string;
  title_ru: string;
  title_kk: string;
  description_en: string;
  description_ru: string;
  description_kk: string;
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
  is_visited: boolean;
  visits_count: number | null;
  nft_discount: boolean;
  my_discount: { code: string; status: 'active' | 'used'; discount_percent: number } | null;
}

export interface LoyaltyLevel {
  id: number;
  name: string;
  min_nfts: number;
  discount_percent: number;
}

/** Уровни и прогресс; поля прогресса пустые, если пользователь не вошёл */
export interface LoyaltyInfo {
  levels: LoyaltyLevel[];
  nft_count: number | null;
  current_level: LoyaltyLevel | null;
  next_level: LoyaltyLevel | null;
  nfts_to_next: number | null;
}

export interface DiscountCode {
  id: number;
  code: string;
  status: 'active' | 'used';
  discount_percent: number;
  level: string;
  event: { id: number; title: string; start_at: string; price: string };
  username: string;
  final_price: string;
  created_at: string;
  used_at: string | null;
}

/** Поля формы события, которые уходят на сервер */
export interface EventPayload {
  title_en: string;
  title_ru: string;
  title_kk: string;
  description_en: string;
  description_ru: string;
  description_kk: string;
  category_id: number;
  venue_id: number;
  start_at: string;
  end_at: string;
  price: string;
  image_url: string;
  source_url: string;
  nft_image_url: string;
  nft_discount: boolean;
}

export interface NftReward {
  id: number;
  status: 'pending' | 'minting' | 'minted' | 'failed';
  wallet_address: string;
  contract_address: string;
  token_id: number | null;
  tx_hash: string;
  explorer_url: string;
  metadata_uri: string;
  minted_at: string | null;
}

export interface Visit {
  id: number;
  event: EventItem;
  checked_in_at: string;
  nft_reward: NftReward | null;
  already_checked_in?: boolean;
}

export interface CheckinCode {
  event_id: number;
  token: string;
  visits_count: number;
  is_published: boolean;
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface VenueHit extends Venue {
  events_count: number;
}

export interface OrganizerHit extends Organizer {
  events_count: number;
}

export interface SearchResult {
  query: string;
  total: number;
  events: EventItem[];
  venues: VenueHit[];
  organizers: OrganizerHit[];
}

export interface EventFilters {
  venue?: string;
  organizer?: string;
  category?: string;
  date_from?: string;
  date_to?: string;
  free?: boolean;
  page?: number;
}
