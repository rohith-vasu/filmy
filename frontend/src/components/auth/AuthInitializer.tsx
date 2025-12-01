// src/components/auth/AuthInitializer.tsx
import { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import { refreshAccessToken } from "@/lib/tokenManager";

export const AuthInitializer = () => {
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const setAuthLoaded = useAuthStore((s) => s.setAuthLoaded);

  useEffect(() => {
    // On app start: if there is a refresh token attempt to refresh -> then fetch user
    (async () => {
      try {
        // If there is a refresh token we try to refresh first so access_token is valid
        await refreshAccessToken();
      } catch (e) {
        // ignore — fetchUser will notice lack of token and mark authLoaded
      } finally {
        // fetchUser will short-circuit if no access token
        await fetchUser();
        setAuthLoaded(true);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return null;
};
