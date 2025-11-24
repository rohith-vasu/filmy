import { Movie, MovieDB } from "@/types";
import { MoreHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";

interface DashboardMovieCardProps {
  movie: MovieDB;
  onClick: () => void;
  onMoreLikeThis: () => void;
}

export default function DashboardMovieCard({
  movie,
  onClick,
  onMoreLikeThis,
}: DashboardMovieCardProps) {
  return (
    <div
      className="relative group cursor-pointer rounded-xl overflow-hidden transition-all duration-300 hover:shadow-xl hover:scale-[1.02]"
      onClick={onClick}
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] bg-secondary">
        <img
          src={movie.poster_url}
          alt={movie.title}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          loading="lazy"
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = "/poster-not-found.png";
          }}
        />

        {/* Hover Overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-between p-3">
          {/* Buttons */}
          <div className="flex justify-end">
            <Button
              size="sm"
              variant="secondary"
              className="text-xs h-8 px-2 gap-1"
              onClick={(e) => {
                e.stopPropagation();
                onMoreLikeThis();
              }}
            >
              <MoreHorizontal className="w-4 h-4" />
              Similar Movies
            </Button>
          </div>

          <h3 className="text-white text-sm font-semibold line-clamp-2">
            {movie.title}
          </h3>
        </div>
      </div>
    </div>
  );
}
