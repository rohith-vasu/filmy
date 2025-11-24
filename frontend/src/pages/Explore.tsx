import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ExploreContent from "@/components/ExploreContent";

export default function Explore() {
    return (
        <div className="min-h-screen bg-background text-white relative overflow-hidden">
            {/* Background Glow - matching hero section */}
            <div className="absolute inset-0 bg-gradient-to-b from-background via-primary/5 to-background" />
            <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[600px] rounded-full bg-primary/10 blur-3xl animate-glow-pulse" />

            <Navbar />
            <main className="pt-24 pb-12 container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
                <ExploreContent />
            </main>
            <Footer />
        </div>
    );
}
