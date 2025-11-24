import { Movie } from "@/types/index";
import { MovieDB } from "@/types/index";

interface MovieCardProps {
  movie: Movie | MovieDB;
  onClick?: () => void;
}

const MovieCard = ({ movie, onClick }: MovieCardProps) => {
  return (
    <div
      className="relative group cursor-pointer rounded-xl overflow-hidden transition-all duration-300 transform hover:scale-105 hover:-translate-y-2 shadow-md hover:shadow-xl"
      onClick={onClick}
    >
      {/* Poster */}
      <div className="relative aspect-[2/3] overflow-hidden bg-secondary">
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

        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Title on Hover */}
        <div className="absolute bottom-0 left-0 right-0 p-3 opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-20">
          <h3 className="text-white text-sm font-semibold drop-shadow-md line-clamp-2">
            {movie.title}
          </h3>
        </div>
      </div>
    </div>
  );
};

export default MovieCard;
