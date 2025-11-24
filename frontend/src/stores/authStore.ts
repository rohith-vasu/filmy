import { create } from "zustand";
import { persist } from "zustand/middleware";
import { User } from "@/types";
import api, { authAPI } from "@/lib/api";
import { getAccessToken, clearTokens } from "@/lib/tokenManager";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  authLoaded: boolean;
  // modal flags
  showRegisterPrompt: boolean;
  showSessionExpired: boolean;
  // auth actions
  setUser: (user: User | null) => void;
  logout: () => void;
  fetchUser: () => Promise<void>;
  // for modals
  openRegisterPrompt: () => void;
  closeRegisterPrompt: () => void;
  showSessionExpiredModal: () => void;
  hideSessionExpiredModal: () => void;
  setAuthLoaded: (v: boolean) => void;
  // helper invoked from api when refresh fails
  handleSessionExpired: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      authLoaded: false,
      showRegisterPrompt: false,
      showSessionExpired: false,

      setUser: (user) =>
        set({
          user: user ? { ...user } : null,
          isAuthenticated: !!user,
          authLoaded: true,
        }),

      logout: () => {
        try {
          clearTokens();
        } catch { }
        set({
          user: null,
          isAuthenticated: false,
          authLoaded: true,
        });
      },

      fetchUser: async () => {
        try {
          const token = getAccessToken();
          if (!token) {
            set({ authLoaded: true });
            return;
          }

          const res = await api.get("/auth/me");
          const data = res.data?.data || res.data;

          const user: User = {
            id: data.id,
            email: data.email,
            first_name: data.firstname,
            last_name: data.lastname,
            genre_preferences: data.genre_preferences,
          };

          set({
            user,
            isAuthenticated: true,
            authLoaded: true,
          });
        } catch (err) {
          // token invalid → clean state
          clearTokens();
          set({
            user: null,
            isAuthenticated: false,
            authLoaded: true,
          });
        }
      },

      openRegisterPrompt: () => set({ showRegisterPrompt: true }),
      closeRegisterPrompt: () => set({ showRegisterPrompt: false }),

      showSessionExpiredModal: () => set({ showSessionExpired: true }),
      hideSessionExpiredModal: () => set({ showSessionExpired: false }),

      setAuthLoaded: (v: boolean) => set({ authLoaded: v }),

      handleSessionExpired: () => {
        // called when refresh token expired / refresh request failed
        clearTokens();
        set({
          user: null,
          isAuthenticated: false,
          authLoaded: true,
          showSessionExpired: true,
        });
      },
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
