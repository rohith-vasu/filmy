import Navbar from "@/components/Navbar";
import HeroSection from "@/components/HeroSection";
import TopMoviesGrid from "@/components/TopMoviesGrid";
import RecommendSection from "@/components/RecommendSection";
import Footer from "@/components/Footer";

const Index = () => {
  return (
    <div className="min-h-screen bg-background relative overflow-hidden">
      {/* Shared Background Glow */}
      <div className="fixed inset-0 bg-gradient-to-b from-background via-primary/5 to-background pointer-events-none" />
      <div className="fixed top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/10 blur-3xl animate-glow-pulse pointer-events-none" />
      
      <Navbar />
      <main className="relative z-10">
        <HeroSection />
        <TopMoviesGrid />
        <RecommendSection />
      </main>
      <Footer />
    </div>
  );
};

export default Index;
