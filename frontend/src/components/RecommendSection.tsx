import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  CarouselNext,
  CarouselPrevious,
} from "@/components/ui/carousel";
import { Sparkles, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import MovieCard from "./MovieCard";
import MovieModal from "@/components/MovieModal";
import Autoplay from "embla-carousel-autoplay";
import type { MovieDB } from "@/types";

const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500";

import { GENRES } from "@/lib/constants";

const RecommendSection = () => {
  const [mode, setMode] = useState<"genre" | "similar">("genre");
  const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
  const [movieNames, setMovieNames] = useState<string>("");
  const [recommendations, setRecommendations] = useState<MovieDB[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedTmdbId, setSelectedTmdbId] = useState<number | null>(null);

  const toggleGenre = (genre: string) => {
    setSelectedGenres((prev) =>
      prev.includes(genre) ? prev.filter((g) => g !== genre) : [...prev, genre]
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      getRecommendations();
    }
  };

  const getRecommendations = async () => {
    if (mode === "genre" && selectedGenres.length === 0) {
      toast.error("Please select at least one genre.");
      return;
    }

    if (mode === "similar" && movieNames.trim().length === 0) {
      toast.error("Please enter at least one movie name.");
      return;
    }

    setIsLoading(true);

    try {
      const params = new URLSearchParams();
      if (mode === "genre") {
        selectedGenres.forEach((g) => params.append("genres", g));
      } else if (mode === "similar") {
        movieNames
          .split(",")
          .map((name) => name.trim())
          .filter(Boolean)
          .forEach((ex) => params.append("examples", ex));
      }

      params.append("limit", "10");

      const res = await fetch(`http://localhost:8000/recommendations/guest?${params.toString()}`);
      const data = await res.json();

      if (data.status === "success" && Array.isArray(data.data)) {
        const formatted: MovieDB[] = data.data.map((m: any) => ({
          id: m.id,
          tmdbId: m.tmdb_id || m.id,
          title: m.title,
          overview: m.overview || "",
          genres: m.genres || "",
          popularity: m.popularity,
          release_year: m.release_year ? `${m.release_year}` : "",
          poster_url: m.poster_path
            ? `${TMDB_IMAGE_BASE}${m.poster_path}`
            : "/poster-not-found.png",
        }));

        setRecommendations(formatted);
        toast.success("Found some great recommendations!");
      } else {
        toast.info("No recommendations found. Try changing filters.");
        setRecommendations([]);
      }
    } catch (err) {
      console.error("Error fetching recommendations:", err);
      toast.error("Failed to fetch recommendations. Please try again.");
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        document.getElementById("recommendations-carousel")?.scrollIntoView({ behavior: "smooth" });
      }, 300);
    }
  };

  return (
    <section className="py-20 relative overflow-hidden">
      {/* Background Glow removed - moved to Index.tsx */}

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Header */}
        <div className="text-center mb-12 animate-fade-up">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-heading font-bold mb-4">
            🎬 <span className="gradient-text">Not Sure What to Watch?</span>
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Choose whether you want recommendations by <strong>Genres</strong> or by <strong>Similar Movies</strong>.
          </p>
        </div>

        {/* Mode Selection */}
        <div className="flex justify-center gap-4 mb-10">
          <Button
            variant={mode === "genre" ? "default" : "outline"}
            onClick={() => {
              setMode("genre");
              setMovieNames("");
            }}
            className={`rounded-full px-6 text-base transition-all duration-300 ${mode === "genre" ? "bg-primary text-primary-foreground scale-105 shadow-lg" : ""
              }`}
          >
            🎭 By Genre
          </Button>

          <Button
            variant={mode === "similar" ? "default" : "outline"}
            onClick={() => {
              setMode("similar");
              setSelectedGenres([]);
            }}
            className={`rounded-full px-6 text-base ${mode === "similar" ? "bg-primary text-primary-foreground" : ""}`}
          >
            🎥 By Similar Movies
          </Button>
        </div>

        {/* Filters */}
        <div className="max-w-4xl mx-auto mb-16 bg-card border border-border rounded-2xl p-6 sm:p-8 card-elevated">
          {/* Conditional Inputs */}
          {mode === "genre" && (
            <div>
              <Label className="text-sm font-medium mb-2 block">Select Genres</Label>
              <div className="flex flex-wrap gap-2">
                {GENRES.map((genre) => (
                  <Button
                    key={genre}
                    type="button"
                    variant={selectedGenres.includes(genre) ? "default" : "outline"}
                    className={`rounded-full text-sm ${selectedGenres.includes(genre)
                      ? "bg-primary text-primary-foreground"
                      : "text-muted-foreground"
                      }`}
                    onClick={() => toggleGenre(genre)}
                  >
                    {genre}
                  </Button>
                ))}
              </div>
            </div>
          )}

          {mode === "similar" && (
            <div>
              <Label htmlFor="movieNames" className="text-sm font-medium mb-2 block">
                Enter Movie Names (comma-separated, up to 3)
              </Label>
              <Input
                id="movieNames"
                placeholder="e.g., Interstellar, Inception"
                value={movieNames}
                onChange={(e) => setMovieNames(e.target.value)}
                onKeyDown={handleKeyDown}
                className="bg-background border-border"
              />
            </div>
          )}

          {mode && (
            <Button
              onClick={getRecommendations}
              disabled={isLoading}
              className="mt-8 w-full gradient-cinematic glow-primary text-lg py-6"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                  Finding the best movies...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  ✨ Get Recommendations
                </>
              )}
            </Button>
          )}
        </div>

        {/* Recommendations Carousel */}
        {recommendations.length > 0 && (
          <div id="recommendations-carousel" className="animate-fade-up">
            <h3 className="text-2xl sm:text-3xl font-heading font-bold text-center mb-8">
              🎯 <span className="gradient-text">Recommended For You</span>
            </h3>

            <Carousel
              opts={{ align: "start", loop: true }}
              plugins={[
                Autoplay({
                  delay: 3500,
                  stopOnInteraction: false,
                }),
              ]}
              className="w-full"
            >
              <CarouselContent>
                {recommendations.map((movie) => (
                  <CarouselItem
                    key={movie.id}
                    className="pl-4 basis-1/2 sm:basis-1/3 md:basis-1/4 lg:basis-1/5"
                  >
                    <div
                      className="pointer-events-auto animate-fade-in hover:scale-105 transition-transform duration-300 cursor-pointer"
                      onClick={() => setSelectedTmdbId(movie.tmdbId)}
                    >
                      <MovieCard movie={movie} />
                    </div>
                  </CarouselItem>
                ))}
              </CarouselContent>
              <CarouselPrevious className="hidden sm:flex -left-4" />
              <CarouselNext className="hidden sm:flex -right-4" />
            </Carousel>

            {/* Explore + Login CTA */}
            <div className="mt-12 flex flex-col items-center gap-8">
              <Link to="/explore">
                <Button variant="outline" size="lg" className="rounded-full px-6 text-base">
                  🎥 Explore More Movies
                </Button>
              </Link>

              <div className="max-w-xl text-center bg-card border border-border rounded-2xl p-8 card-elevated">
                <h4 className="text-xl font-heading font-bold mb-2">
                  Want More Personalized Recommendations?
                </h4>
                <p className="text-muted-foreground mb-6">
                  Create an account to save your preferences and get smarter suggestions tailored just for you.
                </p>
                <Link to="/login">
                  <Button className="gradient-cinematic glow-primary">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Login / Sign Up
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ✅ Movie Modal */}
      {selectedTmdbId && (
        <MovieModal tmdbId={selectedTmdbId} onClose={() => setSelectedTmdbId(null)} />
      )}
    </section>
  );
};

export default RecommendSection;
