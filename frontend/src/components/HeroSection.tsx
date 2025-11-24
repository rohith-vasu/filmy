import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Play } from "lucide-react";
import { useEffect, useState } from "react";

const TMDB_API_KEY = import.meta.env.VITE_TMDB_API_KEY;

const HeroSection = () => {
  const [posters, setPosters] = useState<string[]>([]);
  const [currentPosterIndex, setCurrentPosterIndex] = useState(0);
  const [countryCode, setCountryCode] = useState<string>("US");

  // 🌍 Detect user's country
  useEffect(() => {
    const fetchLocation = async () => {
      try {
        const res = await fetch("https://ipapi.co/json/");
        const data = await res.json();
        setCountryCode(data.country_code || "US");
      } catch (err) {
        console.error("Error fetching location:", err);
        setCountryCode("US");
      }
    };
    fetchLocation();
  }, []);

  // 🎬 Fetch Now Playing Movies from TMDB (region-aware)
  useEffect(() => {
    if (!countryCode) return;
    const fetchNowPlaying = async () => {
      try {
        const res = await fetch(
          `https://api.themoviedb.org/3/movie/now_playing?language=en-US&page=1&region=${countryCode}`,
          {
            headers: {
              Authorization: `Bearer ${TMDB_API_KEY}`,
              accept: "application/json",
            },
          }
        );
        const data = await res.json();

        const moviePosters = (data.results || [])
          .filter((m: any) => m.poster_path)
          .slice(0, 10)
          .map(
            (m: any) => `https://image.tmdb.org/t/p/w500${m.poster_path}`
          );

        setPosters(moviePosters);
      } catch (err) {
        console.error("Error fetching now playing movies:", err);
      }
    };
    fetchNowPlaying();
  }, [countryCode]);

  // 🔁 Smooth auto-rotation
  useEffect(() => {
    if (posters.length === 0) return;
    const interval = setInterval(() => {
      setCurrentPosterIndex((prev) => (prev + 1) % posters.length);
    }, 4000);
    return () => clearInterval(interval);
  }, [posters]);

  // 🎯 Scroll to movies section
  const scrollToMovies = () => {
    const moviesSection = document.getElementById("top-movies");
    moviesSection?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
      {/* Background Glow removed - moved to Index.tsx */}

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center">
          {/* LEFT SIDE: Text + Buttons */}
          <div className="text-center lg:text-left space-y-6 animate-fade-up">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl xl:text-7xl font-heading font-bold leading-tight">
              Discover movies that{" "}
              <span className="gradient-text">match your mood</span>
            </h1>

            <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto lg:mx-0">
              Filmy learns your taste and finds the perfect film — from hidden gems to top hits.
            </p>

            <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start pt-4">
              <Button
                size="lg"
                onClick={scrollToMovies}
                className="gradient-cinematic hover:opacity-90 transition-all duration-300 glow-primary text-base sm:text-lg px-8 py-6"
              >
                <Play className="w-5 h-5 mr-2" />
                Get Started
              </Button>
            </div>
          </div>

          {/* RIGHT SIDE: Auto-Rotating Posters */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="relative h-[500px] hidden lg:flex items-center justify-center"
          >
            <div className="relative w-80 h-[480px]">
              {posters.length > 0 ? (
                posters.map((poster, index) => (
                  <motion.div
                    key={poster}
                    initial={{ opacity: 0, scale: 0.8, rotateY: -20 }}
                    animate={{
                      opacity: currentPosterIndex === index ? 1 : 0,
                      scale: currentPosterIndex === index ? 1 : 0.8,
                      rotateY: currentPosterIndex === index ? 0 : -20,
                    }}
                    transition={{ duration: 0.8 }}
                    className="absolute inset-0"
                  >
                    <img
                      src={poster}
                      alt="Movie Poster"
                      className="w-full h-full object-cover rounded-2xl shadow-2xl"
                    />
                  </motion.div>
                ))
              ) : (
                <div className="flex items-center justify-center text-muted-foreground h-full">
                  Loading posters...
                </div>
              )}

              <div className="absolute -z-10 inset-0 bg-gradient-to-br from-primary/40 to-accent/40 rounded-2xl blur-3xl" />
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;