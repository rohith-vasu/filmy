import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { useEffect, useState } from "react";
import { moviesAPI } from "@/lib/api";
import { MovieDB } from "@/types";
import MovieCard from "@/components/MovieCard";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import MovieModal from "@/components/MovieModal";

const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500";

interface SearchResultsModalProps {
    query: string;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export default function SearchResultsModal({
    query,
    open,
    onOpenChange,
}: SearchResultsModalProps) {
    const [movies, setMovies] = useState<MovieDB[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedMovieId, setSelectedMovieId] = useState<number | null>(null);

    useEffect(() => {
        if (open && query) {
            const fetchResults = async () => {
                setLoading(true);
                try {
                    const res = await moviesAPI.search({
                        title: query,
                        search_bar: true,
                        limit: 10,
                        page: 1,
                    });
                    if (res.status === "success") {
                        setMovies(
                            (res.data.movies || []).map((mv: any) => ({
                                id: mv.id,
                                tmdbId: mv.tmdb_id,
                                title: mv.title,
                                overview: mv.overview ?? "",
                                genres: mv.genres || "",
                                poster_url: mv.poster_path ? `${TMDB_IMAGE_BASE}${mv.poster_path}` : "/poster-not-found.png",
                                release_year: mv.release_year,
                                popularity: mv.popularity,
                            }))
                        );
                    }
                } catch (error) {
                    toast.error("Failed to load search results");
                } finally {
                    setLoading(false);
                }
            };
            fetchResults();
        } else {
            setMovies([]);
        }
    }, [open, query]);

    return (
        <>
            <Dialog open={open} onOpenChange={onOpenChange}>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto scrollbar-hide">
                    <DialogHeader>
                        <DialogTitle>Results for "{query}"</DialogTitle>
                    </DialogHeader>

                    {loading ? (
                        <div className="flex justify-center py-12">
                            <Loader2 className="w-8 h-8 animate-spin text-primary" />
                        </div>
                    ) : (
                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4 mt-4">
                            {movies.map((movie) => (
                                <MovieCard
                                    key={movie.id}
                                    movie={movie}
                                    onClick={() => setSelectedMovieId(movie.tmdbId)}
                                />
                            ))}
                            {movies.length === 0 && (
                                <p className="col-span-full text-center text-muted-foreground py-8">
                                    No movies found matching your search.
                                </p>
                            )}
                        </div>
                    )}
                </DialogContent>
            </Dialog>

            {selectedMovieId && (
                <MovieModal
                    tmdbId={selectedMovieId}
                    onClose={() => setSelectedMovieId(null)}
                />
            )}
        </>
    );
}
