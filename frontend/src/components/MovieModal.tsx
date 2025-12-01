import { useEffect, useState } from "react";
import { Loader2, Check, Plus, Pencil } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import type { MovieDB } from "@/types";
import { moviesAPI } from "@/lib/api";
import { useAuthStore } from "@/stores/authStore";
import { useStatsStore } from "@/stores/statsStore";
import api from "@/lib/api";
import { Link } from "react-router-dom";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";

const TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500";

type StatusType = "watchlist" | "watched" | "none";

interface MovieModalProps {
  id?: number;
  tmdbId: number;
  onClose: () => void;
  onWatchlistUpdate?: () => void;
}

/** StarRating Component */
const StarRating = ({
  value,
  setValue,
  small = false,
  readOnly = false,
}: {
  value: number;
  setValue?: (v: number) => void;
  small?: boolean;
  readOnly?: boolean;
}) => {
  const [hover, setHover] = useState<number | null>(null);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);

  const active = hover !== null ? hover : value;
  const sizeClass = small ? "w-4 h-4" : "w-8 h-8";
  const gapClass = small ? "gap-1" : "gap-2";

  const getFill = (index: number) => {
    const pct = Math.max(0, Math.min(100, (active - (index - 1)) * 100));
    return `${pct}%`;
  };

  const handleClick = (v: number) => {
    if (!setValue) return;
    setActiveIndex(Math.ceil(v));
    setValue(v);
    setTimeout(() => setActiveIndex(null), 180);
  };

  return (
    <div className={`flex items-center ${gapClass}`}>
      {Array.from({ length: 5 }).map((_, i) => {
        const idx = i + 1;
        const isPopped = activeIndex === idx;
        return (
          <div key={idx} className={`relative ${sizeClass}`}>
            <svg
              viewBox="0 0 24 24"
              className={`${sizeClass} text-gray-600 transform transition-transform duration-150 ${!readOnly ? "hover:scale-110" : ""
                } ${isPopped ? "scale-125" : ""}`}
            >
              <path
                fill="currentColor"
                d="M12 .587l3.668 7.431 8.2 1.193-5.934 5.787 1.401 8.167L12 18.896 4.665 23.165l1.401-8.167L.132 9.211l8.2-1.193z"
              />
            </svg>

            <div
              className="absolute inset-0 overflow-hidden pointer-events-none"
              style={{ width: getFill(idx) }}
            >
              <svg viewBox="0 0 24 24" className={`${sizeClass} text-yellow-400`}>
                <path
                  fill="currentColor"
                  d="M12 .587l3.668 7.431 8.2 1.193-5.934 5.787 1.401 8.167L12 18.896 4.665 23.165l1.401-8.167L.132 9.211l8.2-1.193z"
                />
              </svg>
            </div>

            {!readOnly && setValue && (
              <>
                <button
                  className="absolute left-0 top-0 w-1/2 h-full opacity-0"
                  onMouseEnter={() => setHover(idx - 0.5)}
                  onMouseLeave={() => setHover(null)}
                  onMouseDown={() => handleClick(idx - 0.5)}
                />
                <button
                  className="absolute right-0 top-0 w-1/2 h-full opacity-0"
                  onMouseEnter={() => setHover(idx)}
                  onMouseLeave={() => setHover(null)}
                  onMouseDown={() => handleClick(idx)}
                />
              </>
            )}
          </div>
        );
      })}
    </div>
  );
};

/** MovieModal */
const MovieModal = ({ id: propId, tmdbId, onClose, onWatchlistUpdate }: MovieModalProps) => {
  const { isAuthenticated } = useAuthStore();
  const { fetchStats } = useStatsStore();

  const [movie, setMovie] = useState<MovieDB | null>(null);
  const [loading, setLoading] = useState(true);

  // Feedback states
  const [status, setStatus] = useState<StatusType>("none");
  const [ratingValue, setRatingValue] = useState<number>(0);
  const [reviewText, setReviewText] = useState<string>("");

  const [originalFeedback, setOriginalFeedback] = useState<{
    status: StatusType;
    rating: number;
    review: string;
  } | null>(null);

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingFeedback, setIsLoadingFeedback] = useState(false);

  // UI
  const [isEditing, setIsEditing] = useState(false);
  const [showConfirmWatchlist, setShowConfirmWatchlist] = useState(false);
  const [pendingWatchlistNext, setPendingWatchlistNext] = useState<StatusType | null>(null);

  const bodyTextClass = "text-sm leading-relaxed tracking-wide text-gray-200";

  /* Fetch Movie */
  useEffect(() => {
    let mounted = true;
    const fetchMovie = async () => {
      try {
        const res = await api.get(`/movies/tmdb/${tmdbId}`);
        const d = res.data?.data;

        if (!d) {
          toast.error("Movie not found");
          onClose();
          return;
        }

        if (!mounted) return;

        setMovie({
          id: d.id,
          tmdbId: d.tmdb_id,
          title: d.title,
          overview: d.overview,
          genres:
            typeof d.genres === "string"
              ? d.genres.replace(/[{}\[\]"]/g, "")
              : Array.isArray(d.genres)
                ? d.genres.join(", ")
                : "N/A",
          language: d.original_language
            ? d.original_language.charAt(0).toUpperCase() + d.original_language.slice(1)
            : "N/A",
          runtime: d.runtime || 0,
          popularity: d.popularity || 0,
          poster_url: d.poster_path
            ? `${TMDB_IMAGE_BASE}${d.poster_path}`
            : "/poster-not-found.png",
          release_year: d.release_year ? String(d.release_year) : "N/A",
        });
      } catch (err) {
        toast.error("Failed to load movie details.");
      } finally {
        mounted && setLoading(false);
      }
    };

    fetchMovie();
    return () => {
      mounted = false;
    };
  }, [tmdbId, onClose]);

  /* Fetch Feedback */
  useEffect(() => {
    if (!isAuthenticated) return;
    const movieId = propId ?? movie?.id;
    if (!movieId) return;

    setIsLoadingFeedback(true);
    moviesAPI
      .getUserRating(movieId)
      .then((res) => {
        if (!res) return;

        const s = (res.status as StatusType) ?? "none";
        const r = res.rating ?? 0;
        const rv = res.review ?? "";

        setStatus(s);
        setRatingValue(r);
        setReviewText(rv);

        setOriginalFeedback({ status: s, rating: r, review: rv });
      })
      .catch(() => {
        setOriginalFeedback({ status: "none", rating: 0, review: "" });
      })
      .finally(() => setIsLoadingFeedback(false));
  }, [isAuthenticated, movie, propId]);

  const hasFeedback =
    originalFeedback &&
    (originalFeedback.rating > 0 ||
      originalFeedback.review.trim().length > 0 ||
      originalFeedback.status !== "none");

  /* Watchlist Button */
  const handleToggleWatchlistClick = () => {
    if (!isAuthenticated) return;
    const next: StatusType = status === "watchlist" ? "none" : "watchlist";

    if (next === "watchlist" && (originalFeedback?.rating || originalFeedback?.review)) {
      setPendingWatchlistNext(next);
      setShowConfirmWatchlist(true);
      return;
    }

    proceedWatchlist(next);
  };

  const proceedWatchlist = async (next: StatusType) => {
    const movieId = propId ?? movie?.id;
    if (!movieId) return;

    const ratingToSend = null;
    const reviewToSend = null;

    setStatus(next);

    try {
      await moviesAPI.rateMovie(movieId, ratingToSend, reviewToSend, next !== "none" ? next : null);

      setOriginalFeedback({
        status: next,
        rating: 0,
        review: "",
      });

      setRatingValue(0);
      setReviewText("");
      setIsEditing(false);

      toast.success(
        next === "watchlist"
          ? "Added to Watchlist"
          : "Removed from Watchlist"
      );

      fetchStats();
      onWatchlistUpdate?.();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to update watchlist");
      setStatus((prev) => (prev === "watchlist" ? "none" : "watchlist"));
    } finally {
      setShowConfirmWatchlist(false);
      setPendingWatchlistNext(null);
    }
  };

  /* Watched Toggle */
  const handleToggleWatched = () => {
    if (!isAuthenticated) return;
    const next = status === "watched" ? "none" : "watched";
    setStatus(next);
    setIsEditing(true);

    if (next === "watched" && ratingValue <= 0) {
      setRatingValue(0);
      setReviewText("");
    }
  };

  /* Save Feedback */
  const handleSave = async () => {
    if (!isAuthenticated) return;
    const movieId = propId ?? movie?.id;
    if (!movieId) return;

    if (status === "watched" && ratingValue <= 0) {
      return toast.error("Please provide a rating to mark this movie as watched.");
    }

    setIsSubmitting(true);
    try {
      const ratingToSend = status === "watched" ? ratingValue : null;
      const reviewToSend =
        status === "watched" && reviewText.trim() ? reviewText.trim() : null;
      const statusToSend = status !== "none" ? status : null;

      await moviesAPI.rateMovie(movieId, ratingToSend, reviewToSend, statusToSend);

      setOriginalFeedback({
        status: statusToSend ?? "none",
        rating: ratingToSend ?? 0,
        review: reviewToSend ?? "",
      });

      setIsEditing(false);
      toast.success("Saved");

      fetchStats();
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || "Failed to save changes");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (!originalFeedback) return;
    setStatus(originalFeedback.status);
    setRatingValue(originalFeedback.rating);
    setReviewText(originalFeedback.review);
    setIsEditing(false);
  };

  return (
    <Dialog open={true} onOpenChange={(open) => !open && onClose()}>
      <DialogContent
        className="text-white border-zinc-800 max-w-[95%] sm:max-w-[780px] max-h-[85vh] overflow-y-auto scrollbar-hide p-6"
        style={{ background: "var(--gradient-hero)" }}
        onOpenAutoFocus={(e) => e.preventDefault()}
      >
        <DialogTitle className="sr-only">{movie?.title || "Movie Details"}</DialogTitle>
        <DialogDescription className="sr-only">Details for {movie?.title}</DialogDescription>

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-10 h-10 animate-spin text-white" />
          </div>
        ) : movie ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {/* Poster */}
            <div className="flex justify-center">
              <img src={movie.poster_url} alt={movie.title} className="rounded-lg w-full sm:w-[300px] object-cover" />
            </div>

            {/* Info */}
            <div className="flex flex-col">
              <h3 className="text-2xl font-semibold mb-1 tracking-wide">{movie.title}</h3>

              <p className="text-sm text-gray-300 mb-1">
                {movie.release_year}{movie.genres ? ` • ${movie.genres}` : ""}
              </p>

              <p className="text-sm text-gray-400 mb-1">Language: {movie.language}</p>
              {movie.runtime > 0 && (
                <p className="text-sm text-gray-400 mb-4">Runtime: {movie.runtime} min</p>
              )}

              <p className={`${bodyTextClass} mb-6`}>{movie.overview || "No description available."}</p>

              {/* Action Pills */}
              <div className="flex gap-3 mb-4">
                <button
                  type="button"
                  disabled={!isAuthenticated}
                  onClick={handleToggleWatched}
                  className={`px-4 py-2 rounded-full flex items-center gap-2 border ${!isAuthenticated
                    ? "opacity-40 cursor-not-allowed border-gray-700 text-gray-400"
                    : status === "watched"
                      ? "bg-green-500 text-black border-green-600"
                      : "border-gray-700 text-gray-300"
                    }`}
                >
                  <Check className="w-4 h-4" /> Watched
                </button>

                <button
                  type="button"
                  disabled={!isAuthenticated}
                  onClick={handleToggleWatchlistClick}
                  className={`px-4 py-2 rounded-full flex items-center gap-2 border ${!isAuthenticated
                    ? "opacity-40 cursor-not-allowed border-gray-700 text-gray-400"
                    : status === "watchlist"
                      ? "bg-white text-black border-white"
                      : "border-gray-700 text-gray-300"
                    }`}
                >
                  <Plus className="w-4 h-4" /> Watchlist
                </button>
              </div>

              {/* Feedback Section */}
              <div className="mt-auto pt-4 border-t border-gray-700 relative">
                {/* Pencil Icon — only if logged in + hasFeedback + !editing */}
                {isAuthenticated && hasFeedback && !isEditing && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="absolute top-2 right-2 text-gray-400 hover:text-white"
                  >
                    <Pencil className="w-4 h-4" />
                  </button>
                )}

                {/* If user is NOT logged in */}
                {!isAuthenticated ? (
                  <p className="text-xs text-gray-400 text-center">
                    <Link to="/login" className="text-primary hover:underline font-medium">
                      Log in
                    </Link>{" "}
                    to rate or review this movie.
                  </p>
                ) : (
                  <>
                    {isLoadingFeedback ? (
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <Loader2 className="w-4 h-4 animate-spin" /> Loading feedback...
                      </div>
                    ) : (
                      <>
                        {/* VIEW MODE */}
                        <div
                          className={`transition-opacity duration-300 ${isEditing ? "opacity-0 pointer-events-none h-0" : "opacity-100"
                            }`}
                        >
                          {hasFeedback ? (
                            <>
                              {/* Rating */}
                              {originalFeedback?.rating > 0 && (
                                <div className="mb-4">
                                  <Label className="text-sm font-medium">Your Rating</Label>
                                  <div className="mt-2">
                                    <StarRating value={originalFeedback.rating} readOnly small />
                                  </div>
                                </div>
                              )}

                              {/* Review */}
                              {originalFeedback?.review ? (
                                <div className="mb-2">
                                  <Label className="text-sm font-medium">Your Review</Label>
                                  <div className="mt-3 bg-zinc-800 rounded-md p-3 text-sm text-gray-300 whitespace-pre-wrap">
                                    {originalFeedback.review}
                                  </div>
                                </div>
                              ) : null}

                              {/* Only watchlist */}
                              {originalFeedback?.rating === 0 &&
                                !originalFeedback?.review &&
                                originalFeedback.status === "watchlist" && (
                                  <p className="text-sm text-gray-400">
                                    This movie is in your watchlist.
                                  </p>
                                )}
                            </>
                          ) : (
                            <p className="text-sm text-gray-400">Mark as watched to leave a rating & review.</p>
                          )}
                        </div>

                        {/* EDIT MODE */}
                        <div
                          className={`transition-opacity duration-300 ${isEditing ? "opacity-100" : "opacity-0 pointer-events-none h-0"
                            }`}
                        >
                          <Label className="text-sm font-medium mb-2 block">Rate this movie</Label>
                          <StarRating value={ratingValue} setValue={setRatingValue} />

                          <div className="mt-4">
                            <Label className="text-sm font-medium mb-2 block">Your Review (optional)</Label>
                            <textarea
                              rows={3}
                              value={reviewText}
                              onChange={(e) => setReviewText(e.target.value)}
                              className="w-full bg-zinc-800 border border-gray-700 rounded-lg p-3 text-sm text-gray-200 outline-none resize-none"
                              placeholder="Write your thoughts..."
                            />
                          </div>

                          <div className="flex justify-end gap-3 mt-4">
                            <Button variant="secondary" onClick={handleCancel} disabled={isSubmitting}>
                              Cancel
                            </Button>
                            <Button onClick={handleSave} disabled={isSubmitting} className="gradient-cinematic glow-primary">
                              {isSubmitting ? (
                                <>
                                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                  Saving...
                                </>
                              ) : (
                                "Save"
                              )}
                            </Button>
                          </div>
                        </div>
                      </>
                    )}
                  </>
                )}
              </div>
            </div>
          </div>
        ) : null}

        {/* Confirm watchlist modal */}
        {showConfirmWatchlist && pendingWatchlistNext === "watchlist" && (
          <div className="absolute inset-0 z-[100] flex items-center justify-center bg-black/80 rounded-lg">
            <div className="bg-zinc-900 text-white rounded-xl p-5 w-[90%] sm:w-[420px] shadow-xl border border-zinc-700">
              <h4 className="text-lg font-semibold mb-2">Remove rating & move to Watchlist?</h4>
              <p className="text-sm text-gray-300 mb-4">
                Moving this movie to your Watchlist will remove your existing rating and review.
              </p>

              <div className="flex justify-end gap-3">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setShowConfirmWatchlist(false);
                    setPendingWatchlistNext(null);
                  }}
                >
                  Cancel
                </Button>
                <Button onClick={() => proceedWatchlist("watchlist")} className="gradient-cinematic glow-primary">
                  Remove & Move
                </Button>
              </div>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default MovieModal;
