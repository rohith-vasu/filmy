import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Link, useNavigate, useLocation } from "react-router-dom";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useAuthStore } from "@/stores/authStore";
import { LogOut, User, LayoutDashboard, Pencil, Trash, Search, X, Sparkles } from "lucide-react";
import { EditProfileModal } from "@/components/EditProfileModalWithTabs";
import { DeleteAccountModal } from "@/components/DeleteAccountModal";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import SearchResultsModal from "@/components/SearchResultsModal";

const Navbar = () => {
  const { isAuthenticated, user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const [editOpen, setEditOpen] = useState(false);
  const [deleteOpen, setDeleteOpen] = useState(false);

  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [resultsModalOpen, setResultsModalOpen] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (searchOpen && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [searchOpen]);

  const handleLogoClick = () => {
    if (isAuthenticated) navigate("/dashboard");
    else navigate("/");
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setSubmittedQuery(searchQuery);
      setResultsModalOpen(true);
      setSearchOpen(false);
      setSearchQuery("");
    }
  };

  return (
    <>
      {/* NAVBAR */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-border/50 backdrop-blur-cinematic bg-background/80">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div onClick={handleLogoClick} className="flex items-center gap-2 cursor-pointer">
              <img
                src="/filmy-icon.ico"
                alt="Filmy Logo"
                className="w-9 h-9 object-contain transition-transform duration-300 hover:scale-110"
              />
              <span className="text-xl font-heading font-bold">filmy</span>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <div className={cn("relative flex items-center transition-all duration-300", searchOpen ? "w-64" : "w-auto")}>
                    {searchOpen ? (
                      <form onSubmit={handleSearchSubmit} className="w-full relative">
                        <Input
                          ref={searchInputRef}
                          value={searchQuery}
                          onChange={(e) => setSearchQuery(e.target.value)}
                          placeholder="Search movies..."
                          className="pr-8 h-9"
                          onBlur={() => !searchQuery && setSearchOpen(false)}
                        />
                        <button
                          type="button"
                          onClick={() => { setSearchOpen(false); setSearchQuery(""); }}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </form>
                    ) : (
                      <Button variant="ghost" size="icon" onClick={() => setSearchOpen(true)} className="hover:bg-transparent hover:text-primary">
                        <Search className="w-5 h-5" />
                      </Button>
                    )}
                  </div>

                  <Link to="/explore">
                    <Button
                      variant="ghost"
                      className={cn(
                        "hidden sm:inline-flex transition-all hover:bg-transparent hover:text-primary hover:shadow-[0_0_10px_rgba(217,217,217,0.2)]",
                        location.pathname === "/explore" && "text-primary shadow-[0_0_15px_rgba(217,217,217,0.3)]"
                      )}
                    >
                      Explore
                    </Button>
                  </Link>

                  <Link to="/recommendations">
                    <Button
                      variant="ghost"
                      className={cn(
                        "hidden sm:inline-flex transition-all hover:bg-transparent hover:text-primary hover:shadow-[0_0_10px_rgba(217,217,217,0.2)]",
                        location.pathname === "/recommendations" && "text-primary shadow-[0_0_15px_rgba(217,217,217,0.3)]"
                      )}
                    >
                      Recommendations
                    </Button>
                  </Link>

                  <Link to="/dashboard">
                    <Button
                      variant="ghost"
                      className={cn(
                        "hidden sm:inline-flex transition-all hover:bg-transparent hover:text-primary hover:shadow-[0_0_10px_rgba(217,217,217,0.2)]",
                        location.pathname === "/dashboard" && "text-primary shadow-[0_0_15px_rgba(217,217,217,0.3)]"
                      )}
                    >
                      Dashboard
                    </Button>
                  </Link>

                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" className="flex items-center gap-2 hover:bg-transparent hover:text-primary">
                        <User className="w-4 h-4" />
                        <span className="hidden sm:inline">
                          {user?.first_name} {user?.last_name}
                        </span>
                      </Button>
                    </DropdownMenuTrigger>

                    <DropdownMenuContent align="end">
                      <DropdownMenuItem disabled className="opacity-75">
                        {user?.email}
                      </DropdownMenuItem>

                      <DropdownMenuSeparator />

                      <DropdownMenuItem onClick={() => setEditOpen(true)} className="hover:bg-primary/10 hover:text-primary focus:bg-primary/10 focus:text-primary">
                        <Pencil className="w-4 h-4 mr-2" />
                        Edit Profile
                      </DropdownMenuItem>

                      <DropdownMenuItem onClick={() => setDeleteOpen(true)} className="hover:bg-red-500/10 hover:text-red-400 focus:bg-red-500/10 focus:text-red-400">
                        <Trash className="w-4 h-4 mr-2" />
                        <span>Delete Account</span>
                      </DropdownMenuItem>

                      <DropdownMenuSeparator />

                      <DropdownMenuItem onClick={handleLogout} className="hover:bg-primary/10 hover:text-primary focus:bg-primary/10 focus:text-primary">
                        <LogOut className="w-4 h-4 mr-2" />
                        Logout
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </>
              ) : (
                <>
                  <Link to="/explore">
                    <Button
                      variant="ghost"
                      className={cn(
                        "hidden sm:inline-flex transition-all hover:bg-transparent hover:text-primary hover:shadow-[0_0_10px_rgba(217,217,217,0.2)]",
                        location.pathname === "/explore" && "text-primary shadow-[0_0_15px_rgba(217,217,217,0.3)]"
                      )}
                    >
                      Explore
                    </Button>
                  </Link>
                  <Link to="/login">
                    <Button variant="ghost" className="hidden sm:inline-flex hover:bg-transparent hover:text-primary hover:shadow-[0_0_10px_rgba(217,217,217,0.2)] transition-all">
                      Login
                    </Button>
                  </Link>
                  <Link to="/register">
                    <Button className="gradient-cinematic hover:opacity-90 glow-primary">
                      Sign Up
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav >

      {/* MODALS */}
      < EditProfileModal open={editOpen} onOpenChange={setEditOpen} />
      <DeleteAccountModal open={deleteOpen} onOpenChange={setDeleteOpen} />
      <SearchResultsModal
        query={submittedQuery}
        open={resultsModalOpen}
        onOpenChange={setResultsModalOpen}
      />
    </>
  );
};

export default Navbar;
