export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  genre_preferences?: string;
}

export interface Movie {
  id: number;
  title: string;
  poster_url: string;
  overview?: string;
  genre_ids?: number[];
  language?: string;
  release_date?: string;
}

export interface MovieDB {
  id: number;
  tmdbId: number;
  title: string;
  overview?: string;
  genres?: string;
  language?: string;
  runtime?: number;
  popularity?: number;
  poster_url?: string;
  release_year?: string;
}