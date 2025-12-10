import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import { authAPI } from "@/lib/api";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { GENRES } from "@/lib/constants";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const GenreSelectionModal = () => {
    const { user, isAuthenticated, authLoaded, setUser } = useAuthStore();
    const [open, setOpen] = useState(false);
    const [selectedGenres, setSelectedGenres] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Show modal only after auth is fully loaded and if user has no genre preferences
        if (authLoaded && isAuthenticated && user) {
            // Only check if genre_preferences is defined (backend has responded)
            // undefined = still loading from backend, don't show modal yet
            // null or empty string = backend confirmed no preferences, show modal
            if (user.genre_preferences !== undefined) {
                const hasPreferences = user.genre_preferences && user.genre_preferences.trim().length > 0;
                setOpen(!hasPreferences);
            } else {
                setOpen(false);
            }
        } else {
            setOpen(false);
        }
    }, [authLoaded, isAuthenticated, user]);

    const toggleGenre = (genre: string) => {
        setSelectedGenres((prev) =>
            prev.includes(genre)
                ? prev.filter((g) => g !== genre)
                : [...prev, genre]
        );
    };

    const handleSubmit = async () => {
        if (selectedGenres.length < 3) {
            toast.error("Please select at least 3 genres to continue.");
            return;
        }

        if (!user) return;

        setLoading(true);
        try {
            const genreString = selectedGenres.join(",");
            const updatedUser = await authAPI.updateProfile(user.id, {
                genre_preferences: genreString,
            });

            // Update local store
            setUser({ ...user, genre_preferences: genreString });
            toast.success("Preferences saved! Enjoy your recommendations.");
            setOpen(false);
        } catch (error) {
            console.error("Failed to update genres:", error);
            toast.error("Failed to save preferences. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={() => { }}>
            <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()} onEscapeKeyDown={(e) => e.preventDefault()}>
                <DialogHeader>
                    <DialogTitle>Welcome to Filmy!</DialogTitle>
                    <DialogDescription>
                        Select at least 3 genres you love to help us personalize your experience.
                    </DialogDescription>
                </DialogHeader>

                <div className="flex flex-wrap gap-2 py-4 max-h-[60vh] overflow-y-auto">
                    {GENRES.map((genre) => (
                        <Button
                            key={genre}
                            variant={selectedGenres.includes(genre) ? "default" : "outline"}
                            onClick={() => toggleGenre(genre)}
                            className="rounded-full"
                            size="sm"
                        >
                            {genre}
                        </Button>
                    ))}
                </div>

                <div className="flex justify-end">
                    <Button onClick={handleSubmit} disabled={loading || selectedGenres.length < 3}>
                        {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                        Start Exploring
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default GenreSelectionModal;
