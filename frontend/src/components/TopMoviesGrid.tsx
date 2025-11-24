import { useState, useEffect } from "react";
import MovieCard from "./MovieCard";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import Autoplay from "embla-carousel-autoplay";
import { Movie } from "@/types";

const TMDB_API_KEY = import.meta.env.VITE_TMDB_API_KEY;

const TopMoviesGrid = () => {
  const [movies, setMovies] = useState<Movie[]>([]);
  const [country, setCountry] = useState<string>("Your Country");
  const [countryCode, setCountryCode] = useState<string>("US");
  const [genres, setGenres] = useState<Record<number, string>>({});
  const [languages, setLanguages] = useState<Record<string, string>>({});
  const [selectedMovie, setSelectedMovie] = useState<Movie | null>(null);
  const [selectedMovieRuntime, setSelectedMovieRuntime] = useState<number | null>(null);

  // 🌍 Detect user country
  useEffect(() => {
    fetch("https://ipapi.co/json/")
      .then((res) => res.json())
      .then((data) => {
        const code = data.country_code || "US";
        setCountry(data.country_name || "Your Country");
        setCountryCode(code);
      })
      .catch(() => {
        setCountry("Your Country");
        setCountryCode("US");
      });
  }, []);

  // 🎭 Fetch Genres
  const fetchGenres = async () => {
    try {
      const res = await fetch("https://api.themoviedb.org/3/genre/movie/list?language=en", {
        headers: {
          Authorization: `Bearer ${TMDB_API_KEY}`,
          accept: "application/json",
        },
      });
      const data = await res.json();
      const map: Record<number, string> = {};
      data.genres.forEach((g: any) => (map[g.id] = g.name));
      setGenres(map);
    } catch (err) {
      console.error("Error fetching genres:", err);
    }
  };

  // 🗣️ Fetch Languages
  const fetchLanguages = async () => {
    try {
      const res = await fetch("https://api.themoviedb.org/3/configuration/languages", {
        headers: {
          Authorization: `Bearer ${TMDB_API_KEY}`,
          accept: "application/json",
        },
      });
      const data = await res.json();
      const map: Record<string, string> = {};
      data.forEach((lang: any) => (map[lang.iso_639_1] = lang.english_name));
      setLanguages(map);
    } catch (err) {
      console.error("Error fetching languages:", err);
    }
  };

  // 🎬 Fetch Movies
  const fetchMovies = async (region: string) => {
    try {
      const res = await fetch(
        `https://api.themoviedb.org/3/trending/movie/day?region=${region}&language=en-US&page=1`,
        {
          headers: {
            Authorization: `Bearer ${TMDB_API_KEY}`,
            accept: "application/json",
          },
        }
      );
      const data = await res.json();
      const movieResults: Movie[] = (data.results || [])
        .filter((m: any) => m.poster_path)
        .slice(0, 10)
        .map((m: any) => ({
          id: m.id,
          title: m.title,
          poster_url: `https://image.tmdb.org/t/p/w500${m.poster_path}`,
          overview: m.overview,
          genre_ids: m.genre_ids,
          release_date: m.release_date,
          language: m.original_language,
        }));
      setMovies(movieResults);
    } catch (err) {
      console.error("Error fetching TMDB movies:", err);
    }
  };

  useEffect(() => {
    if (!countryCode) return;
    fetchGenres();
    fetchLanguages();
    fetchMovies(countryCode);
  }, [countryCode]);

  const getGenreNames = (ids?: number[]) => {
    if (!ids) return [];
    return ids.map((id) => genres[id]).filter(Boolean);
  };

  const getLanguageName = (code?: string) => {
    if (!code) return "Unknown";
    return languages[code] || code.toUpperCase();
  };

  // ⭐ Fetch runtime for selected movie
  const fetchMovieRuntime = async (movieId: number) => {
    try {
      const res = await fetch(`https://api.themoviedb.org/3/movie/${movieId}?language=en-US`, {
        headers: {
          Authorization: `Bearer ${TMDB_API_KEY}`,
          accept: "application/json",
        },
      });
      const data = await res.json();
      setSelectedMovieRuntime(data.runtime || null);
    } catch (err) {
      console.error("Failed to fetch runtime:", err);
    }
  };

  // Close modal with ESC
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setSelectedMovie(null);
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, []);

  return (
    <section id="top-movies" className="py-20 relative overflow-hidden">
      {/* Background Glow removed - moved to Index.tsx */}

      {selectedMovie && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-md z-40 transition-all duration-300"
          onClick={() => setSelectedMovie(null)}
        />
      )}

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-50">
        <div className="text-center mb-12 animate-fade-up">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-heading font-bold mb-4">
            🎬 <span className="gradient-text">Trending Movies in {country}</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Discover the most popular films in your region right now
          </p>
        </div>

        {/* 🎠 Carousel */}
        <Carousel
          opts={{
            align: "start",
            loop: true,
          }}
          plugins={[
            Autoplay({
              delay: 4000,
              stopOnInteraction: false,
            }),
          ]}
          className="w-full"
        >
          <CarouselContent>
            {movies.map((movie) => (
              <CarouselItem
                key={movie.id}
                className="pl-4 basis-1/2 sm:basis-1/3 md:basis-1/4 lg:basis-1/5 cursor-pointer"
                onClick={() => {
                  setSelectedMovie(movie);
                  fetchMovieRuntime(movie.id); // ⭐ Fetch runtime when opened
                }}
              >
                <div className="animate-fade-in hover:scale-105 transition-transform duration-300">
                  <MovieCard movie={movie} />
                </div>
              </CarouselItem>
            ))}
          </CarouselContent>

          <CarouselPrevious className="hidden sm:flex -left-4" />
          <CarouselNext className="hidden sm:flex -right-4" />
        </Carousel>
      </div>

      {/* 🪟 Movie Modal */}
      {selectedMovie && (
        <div
          className="fixed inset-0 flex items-center justify-center z-50 p-4"
          onClick={() => setSelectedMovie(null)}
        >
          <div
            className="bg-zinc-900 text-white rounded-2xl shadow-2xl w-[95%] sm:w-[750px] max-h-[85vh] overflow-y-auto grid grid-cols-1 sm:grid-cols-2 gap-6 p-6 relative animate-fade-in"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              onClick={() => setSelectedMovie(null)}
              className="absolute top-3 right-3 text-gray-400 hover:text-white text-xl"
            >
              ✕
            </button>

            <div className="flex justify-center items-start">
              <img
                src={selectedMovie.poster_url}
                alt={selectedMovie.title}
                className="rounded-lg w-full sm:w-[300px] h-auto object-cover"
              />
            </div>

            <div className="flex flex-col pr-2">
              <h3 className="text-2xl font-semibold mb-2">
                {selectedMovie.title}
              </h3>

              <p className="text-sm text-gray-300 mb-2">
                {selectedMovie.release_date
                  ? new Date(selectedMovie.release_date).getFullYear()
                  : ""}
                {" • "}
                {getGenreNames(selectedMovie.genre_ids).join(", ")}
              </p>

              <p className="text-sm text-gray-400 mb-2">
                Language: {getLanguageName(selectedMovie.language)}
              </p>

              {/* ⭐ Added Runtime */}
              {selectedMovieRuntime && (
                <p className="text-sm text-gray-400 mb-4">
                  Runtime: {selectedMovieRuntime} min
                </p>
              )}

              <p className="text-gray-300 text-sm leading-relaxed">
                {selectedMovie.overview || "No description available."}
              </p>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default TopMoviesGrid;
