import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { Sparkles, Film, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import MovieCard from "@/components/MovieCard";
import MovieModal from "@/components/MovieModal";
import MoreLikeThisModal from "@/components/MoreLikeThisModal";
import { recommendationsAPI } from "@/lib/api";
import { toast } from "sonner";
import type { MovieDB } from "@/types";
import { useStatsStore } from "@/stores/statsStore";
import { cn } from "@/lib/utils";
import { GENRES, LANGUAGE_OPTIONS } from "@/lib/constants";
import { MultiSelect } from "@/components/ui/multi-select";

const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500";

export default function DiscoverContent() {
    const [searchParams] = useSearchParams();
    const { fetchStats } = useStatsStore();

    // View Mode
    const [viewMode, setViewMode] = useState<"filter" | "similar">("filter");

    // Filters
    const [similarTo, setSimilarTo] = useState("");
    const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
    const [yearRange, setYearRange] = useState<[number, number]>([1950, new Date().getFullYear()]);
    const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);

    // Data
    const [movies, setMovies] = useState<MovieDB[]>([]);
    const [loading, setLoading] = useState(false);

    // Modals
    const [selectedTmdbId, setSelectedTmdbId] = useState<number | null>(null);
    const [moreLikeThisOpen, setMoreLikeThisOpen] = useState(false);
    const [moreLikeThisMovie, setMoreLikeThisMovie] = useState<{ id: number; title: string } | null>(null);

    const [hasSearched, setHasSearched] = useState(false);

    // Fetch Recommendations
    const fetchRecommendations = async () => {
        setLoading(true);
        setHasSearched(true);
        try {
            const params = new URLSearchParams();
            params.append("limit", "20");

            if (viewMode === "similar") {
                if (similarTo.trim()) {
                    params.append("query_movies", similarTo);
                } else {
                    toast.error("Please enter a movie title");
                    setLoading(false);
                    return;
                }
            } else {
                // Filter Mode
                if (selectedGenres.length > 0) {
                    selectedGenres.forEach(g => params.append("genres", g));
                }
                if (selectedLanguages.length > 0) {
                    selectedLanguages.forEach(l => params.append("languages", l));
                }
                params.append("year_min", yearRange[0].toString());
                params.append("year_max", yearRange[1].toString());
            }

            const res = await recommendationsAPI.recommend(params);

            if (res.data?.status === "success") {
                const results = res.data.data.map((m: any) => ({
                    id: m.id,
                    tmdbId: m.tmdb_id,
                    title: m.title,
                    overview: m.overview,
                    genres: Array.isArray(m.genres) ? m.genres.join(", ") : m.genres,
                    poster_url: m.poster_path
                        ? `${TMDB_IMAGE_BASE}${m.poster_path}`
                        : "/poster-not-found.png",
                    release_year: m.release_year,
                    popularity: m.popularity,
                    original_language: m.original_language
                }));

                setMovies(results);
            }
        } catch (err) {
            toast.error("Failed to load recommendations");
        } finally {
            setLoading(false);
        }
    };

    const handleMoreLikeThis = (movie: MovieDB) => {
        setMoreLikeThisMovie({ id: movie.id, title: movie.title });
        setMoreLikeThisOpen(true);
    };

    const toggleGenre = (genre: string) => {
        setSelectedGenres(prev =>
            prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
        );
    };

    const languageOptions = LANGUAGE_OPTIONS.map(l => ({ label: l.label, value: l.value }));

    return (
        <div className="animate-fade-in space-y-8">

            {/* Header */}
            <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-heading font-bold mb-2 gradient-text">
                        Discover Your Next Favorite
                    </h1>
                    <p className="text-gray-400">Get recommendations for your next favorite movie using our AI engine.</p>
                </div>

                {/* View Mode Toggle */}
                <div className="flex bg-zinc-900/50 p-1 rounded-lg border border-zinc-800">
                    <button
                        onClick={() => setViewMode("filter")}
                        className={cn(
                            "px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                            viewMode === "filter"
                                ? "bg-primary text-primary-foreground shadow-lg"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                        )}
                    >
                        <Filter className="w-4 h-4" />
                        By Filters
                    </button>
                    <button
                        onClick={() => setViewMode("similar")}
                        className={cn(
                            "px-4 py-2 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                            viewMode === "similar"
                                ? "bg-primary text-primary-foreground shadow-lg"
                                : "text-gray-400 hover:text-white hover:bg-white/5"
                        )}
                    >
                        <Film className="w-4 h-4" />
                        By Similar Movies
                    </button>
                </div>
            </div>

            {/* Filters Section */}
            <Card className="bg-zinc-900/50 border-zinc-800">
                <CardContent className="p-6 space-y-6">

                    {viewMode === "similar" ? (
                        /* Similar Movies Mode */
                        <div className="max-w-2xl mx-auto space-y-4 text-center py-8">
                            <div className="space-y-2">
                                <Label className="text-lg font-medium">What have you watched recently?</Label>
                                <p className="text-sm text-gray-500">Enter a movie title, and we'll find similar gems.</p>
                            </div>
                            <div className="relative max-w-md mx-auto">
                                <Film className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                                <Input
                                    placeholder="e.g. Inception, The Dark Knight..."
                                    value={similarTo}
                                    onChange={(e) => setSimilarTo(e.target.value)}
                                    className="pl-10 h-12 text-lg bg-zinc-950 border-zinc-800 focus:border-primary/50 transition-colors"
                                    onKeyDown={(e) => e.key === "Enter" && fetchRecommendations()}
                                />
                            </div>
                            <Button
                                onClick={fetchRecommendations}
                                className="gradient-cinematic glow-primary px-8"
                                disabled={loading}
                            >
                                {loading ? <Sparkles className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                                Find Similar Movies
                            </Button>
                        </div>
                    ) : (
                        /* Filter Mode */
                        <div className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

                                {/* Language & Year */}
                                <div className="space-y-6">
                                    <div className="space-y-2">
                                        <Label className="text-xs font-medium uppercase tracking-wider text-gray-500">Language</Label>
                                        <MultiSelect
                                            options={languageOptions}
                                            selected={selectedLanguages}
                                            onChange={setSelectedLanguages}
                                            placeholder="Select languages..."
                                        />
                                    </div>

                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <Label className="text-xs font-medium uppercase tracking-wider text-gray-500">Release Year</Label>
                                            <span className="text-xs text-primary font-mono">{yearRange[0]} - {yearRange[1]}</span>
                                        </div>
                                        <Slider
                                            defaultValue={[1950, new Date().getFullYear()]}
                                            min={1950}
                                            max={new Date().getFullYear()}
                                            step={1}
                                            value={yearRange}
                                            onValueChange={(val) => setYearRange(val as [number, number])}
                                            className="py-2"
                                        />
                                    </div>
                                </div>

                                {/* Genres */}
                                <div className="space-y-3">
                                    <Label className="text-xs font-medium uppercase tracking-wider text-gray-500">Genres</Label>
                                    <div className="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto pr-2 scrollbar-hide">
                                        {GENRES.map((genre) => (
                                            <Badge
                                                key={genre}
                                                variant={selectedGenres.includes(genre) ? "default" : "outline"}
                                                className={cn(
                                                    "cursor-pointer transition-all hover:opacity-80 px-3 py-1",
                                                    selectedGenres.includes(genre)
                                                        ? "bg-primary text-primary-foreground border-primary"
                                                        : "bg-transparent text-gray-400 border-zinc-800 hover:border-zinc-700"
                                                )}
                                                onClick={() => toggleGenre(genre)}
                                            >
                                                {genre}
                                            </Badge>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-center pt-4 border-t border-zinc-800">
                                <Button
                                    onClick={fetchRecommendations}
                                    className="gradient-cinematic glow-primary w-full md:w-auto px-8"
                                    disabled={loading}
                                >
                                    {loading ? <Sparkles className="w-4 h-4 animate-spin mr-2" /> : <Sparkles className="w-4 h-4 mr-2" />}
                                    Suggest Movies
                                </Button>
                            </div>
                        </div>
                    )}

                </CardContent>
            </Card>

            {/* Results Grid */}
            {movies.length > 0 ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
                    {movies.map((movie) => (
                        <div key={movie.id} onClick={() => setSelectedTmdbId(movie.tmdbId)}>
                            <MovieCard movie={movie} />
                        </div>
                    ))}
                </div>
            ) : (
                !loading && (
                    <div className="text-center py-20 text-gray-500">
                        {hasSearched ? (
                            <p>No movies found. Try adjusting your filters.</p>
                        ) : (
                            <p>Select filters or search for a movie to get recommendations.</p>
                        )}
                    </div>
                )
            )}

            {/* Modals */}
            {selectedTmdbId && (
                <MovieModal
                    tmdbId={selectedTmdbId}
                    onClose={() => setSelectedTmdbId(null)}
                />
            )}

            {moreLikeThisOpen && moreLikeThisMovie && (
                <MoreLikeThisModal
                    open={moreLikeThisOpen}
                    onOpenChange={setMoreLikeThisOpen}
                    movieTitle={moreLikeThisMovie.title}
                    id={moreLikeThisMovie.id}
                />
            )}
        </div>
    );
}
