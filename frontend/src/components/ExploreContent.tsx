import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectItem,
  SelectContent,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search } from "lucide-react";
import MovieCard from "@/components/MovieCard";
import MovieModal from "@/components/MovieModal";
import { moviesAPI } from "@/lib/api";
import { toast } from "sonner";
import type { MovieDB } from "@/types";
import { GENRES, LANGUAGE_OPTIONS } from "@/lib/constants";
import { MultiSelect } from "@/components/ui/multi-select";

const ExploreContent = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState("all");
  const [sortOption, setSortOption] = useState("popularity:desc");

  const [movies, setMovies] = useState<MovieDB[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [selectedTmdbId, setSelectedTmdbId] = useState<number | null>(null);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: currentYear - 1949 }, (_, i) => currentYear - i);

  // Sorting Map
  const getSortParams = () => {
    const [field, direction] = sortOption.split(":");
    return {
      sort_by:
        field === "release"
          ? "release_year"
          : field === "popularity"
            ? "popularity"
            : "title",
      order: direction,
    };
  };

  // Fetch Movies
  const fetchMovies = async (pageNum: number) => {
    setLoading(true);
    try {
      const { sort_by, order } = getSortParams();

      const res = await moviesAPI.search({
        title: searchQuery || undefined,
        genre: selectedGenres,
        language: selectedLanguages.length > 0 ? selectedLanguages : undefined,
        release_year:
          selectedYear !== "all" ? parseInt(selectedYear) : undefined,
        sort_by,
        order,
        page: pageNum,
        limit: 50,
      });

      const data = res.data;

      const formatted: MovieDB[] = data.movies.map((m: any) => ({
        id: m.id,
        tmdbId: m.tmdb_id,
        title: m.title,
        overview: m.overview,
        genres: m.genres,
        popularity: m.popularity,
        release_year: m.release_year,
        poster_url: m.poster_path
          ? `https://image.tmdb.org/t/p/w300${m.poster_path}`
          : "/poster-not-found.png",
      }));

      setMovies(formatted);
      setPage(data.page);
      setTotalPages(data.total_pages);
    } catch {
      toast.error("Failed to load movies.");
    }
    setLoading(false);
  };

  const handleSearch = () => fetchMovies(1);

  useEffect(() => {
    fetchMovies(1);
  }, []);

  const previousPage = () => page > 1 && fetchMovies(page - 1);
  const nextPage = () => page < totalPages && fetchMovies(page + 1);

  const genreOptions = GENRES.map(g => ({ label: g, value: g }));

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div className="text-center mb-8 animate-fade-up">
        <h1 className="text-4xl sm:text-5xl font-heading font-bold mb-4">
          <span className="gradient-text">Explore The Movie Vault</span>
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Dive into our extensive collection of cinematic masterpieces.
        </p>
      </div>

      {/* Filters Panel */}
      <div className="max-w-6xl mx-auto mb-8 bg-card border border-border rounded-2xl p-6 card-elevated">

        {/* Search */}
        <div className="mb-6">
          <Label className="text-sm font-medium mb-2 block">Search Movies</Label>
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                placeholder="Enter movie name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10 bg-background border-border"
              />
            </div>
            <Button onClick={handleSearch} disabled={loading}>
              {loading ? "Searching..." : "Search"}
            </Button>
          </div>
        </div>

        {/* Filters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">

          {/* Genre Dropdown */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Genres</Label>
            <MultiSelect
              options={genreOptions}
              selected={selectedGenres}
              onChange={setSelectedGenres}
              placeholder="Select Genres"
            />
          </div>

          {/* Language */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Language</Label>
            <MultiSelect
              options={LANGUAGE_OPTIONS}
              selected={selectedLanguages}
              onChange={setSelectedLanguages}
              placeholder="Select Languages"
            />
          </div>

          {/* Year */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Year</Label>
            <Select value={selectedYear} onValueChange={setSelectedYear}>
              <SelectTrigger className="bg-background border-border">
                <SelectValue placeholder="All Years" />
              </SelectTrigger>

              <SelectContent className="max-h-[300px]">
                <SelectItem value="all">All Years</SelectItem>
                {years.map((year) => (
                  <SelectItem key={year} value={year.toString()}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {/* Sorting */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Sort By</Label>
            <Select value={sortOption} onValueChange={setSortOption}>
              <SelectTrigger className="bg-background border-border">
                <SelectValue placeholder="Sort By" />
              </SelectTrigger>

              <SelectContent>
                <SelectItem value="popularity:desc">Popularity (High→Low)</SelectItem>
                <SelectItem value="popularity:asc">Popularity (Low→High)</SelectItem>
                <SelectItem value="release:desc">Release Year (New→Old)</SelectItem>
                <SelectItem value="release:asc">Release Year (Old→New)</SelectItem>
                <SelectItem value="title:asc">Title (A→Z)</SelectItem>
                <SelectItem value="title:desc">Title (Z→A)</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>


      </div>

      {/* Results */}
      <div className="max-w-7xl mx-auto">

        {loading && movies.length === 0 ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading movies...</p>
          </div>
        ) : movies.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground text-lg mb-4">No movies found</p>
            <p className="text-muted-foreground text-sm">Try adjusting your filters</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-5 mb-8">
              {movies.map((movie) => (
                <div
                  key={movie.id}
                  className="cursor-pointer animate-fade-in"
                  onClick={() => {
                    setSelectedTmdbId(movie.tmdbId);
                    setSelectedId(movie.id);
                  }}
                >
                  <MovieCard movie={movie} />
                </div>
              ))}
            </div>

            <div className="flex justify-center items-center gap-4 mt-8">
              <Button onClick={previousPage} disabled={page === 1}>
                Previous
              </Button>

              <span className="text-lg font-medium">
                Page {page} / {totalPages}
              </span>

              <Button onClick={nextPage} disabled={page === totalPages}>
                Next
              </Button>
            </div>
          </>
        )}
      </div>

      {selectedTmdbId && (
        <MovieModal
          id={selectedId}
          tmdbId={selectedTmdbId}
          onClose={() => setSelectedTmdbId(null)}
        />
      )}
    </div>
  );
};

export default ExploreContent;