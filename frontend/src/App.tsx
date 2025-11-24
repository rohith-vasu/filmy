import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { AuthInitializer } from "@/components/auth/AuthInitializer";

import Index from "./pages/Index";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Explore from "./pages/Explore";
import Recommendations from "./pages/Recommendations";
import Dashboard from "./pages/Dashboard";
import NotFound from "./pages/NotFound";

import RegisterPromptModal from "@/components/auth/RegisterPromptModal";
import SessionExpiredModal from "@/components/auth/SessionExpiredModal";
import GenreSelectionModal from "@/components/auth/GenreSelectionModal";

const queryClient = new QueryClient();

const RootRoute = () => {
  const { isAuthenticated, authLoaded } = useAuthStore();

  if (!authLoaded)
    return <div className="min-h-screen flex items-center justify-center">Loading…</div>;

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <Index />;
};

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, authLoaded } = useAuthStore();

  if (!authLoaded)
    return <div className="min-h-screen flex items-center justify-center">Loading…</div>;

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

const PublicOnlyRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, authLoaded } = useAuthStore();

  if (!authLoaded)
    return <div className="min-h-screen flex items-center justify-center">Loading…</div>;

  return isAuthenticated ? <Navigate to="/dashboard" replace /> : <>{children}</>;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        {/* Runs ONCE, restores authentication */}
        <AuthInitializer />

        {/* Global modals */}
        <RegisterPromptModal />
        <SessionExpiredModal />
        <GenreSelectionModal />

        <Routes>
          <Route path="/" element={<RootRoute />} />

          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />

          <Route
            path="/register"
            element={
              <PublicOnlyRoute>
                <Register />
              </PublicOnlyRoute>
            }
          />

          <Route path="/explore" element={<Explore />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <Recommendations />
              </ProtectedRoute>
            }
          />

          {/* ✳ Keep custom routes above this */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
