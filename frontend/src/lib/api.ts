import axios, { AxiosError, AxiosHeaders, AxiosRequestConfig } from "axios";
import { getAccessToken, getRefreshToken, refreshAccessToken, clearTokens, setTokens } from "@/lib/tokenManager";
import { useAuthStore } from "@/stores/authStore";
import { toast } from "sonner";

const API_BASE_URL =
  import.meta.env.VITE_BASE_API_URL || "http://localhost:8000/filmy-api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Attach access token to outgoing requests
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    if (config.headers instanceof AxiosHeaders) {
      config.headers.set("Authorization", `Bearer ${token}`);
    } else {
      config.headers = {
        ...(config.headers as any || {}),
        Authorization: `Bearer ${token}`,
      } as any;
    }
  }
  return config;
});

// Single-refresh queue implementation
let isRefreshing = false;
let refreshPromise: Promise<string | null> | null = null;
let failedQueue: {
  resolve: (value?: any) => void;
  reject: (error?: any) => void;
  config: AxiosRequestConfig;
}[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((p) => {
    if (error) p.reject(error);
    else {
      if (p.config.headers instanceof AxiosHeaders) {
        p.config.headers.set("Authorization", `Bearer ${token}`);
      } else {
        p.config.headers = {
          ...(p.config.headers || {}),
          Authorization: `Bearer ${token}`,
        } as any;
      }
      p.resolve(api(p.config));
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (res) => res,
  async (
    error: AxiosError & {
      config?: AxiosRequestConfig & { _retry?: boolean };
    }
  ) => {
    const originalRequest = error.config;

    if (
      originalRequest?.url?.includes("/auth/login") ||
      originalRequest?.url?.includes("/auth/register")
    ) {
      return Promise.reject(error); // pass to Login.tsx
    }

    // Normal refresh logic for all other API calls
    if (
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = (async () => {
          try {
            const newAccess = await refreshAccessToken();
            return newAccess;
          } catch (err) {
            clearTokens();
            useAuthStore.getState().handleSessionExpired(); // show modal
            throw err;
          } finally {
            isRefreshing = false;
            refreshPromise = null;
          }
        })();
      }

      try {
        const newToken = await refreshPromise;

        // Retry queued requests
        if (originalRequest.headers instanceof AxiosHeaders) {
          originalRequest.headers.set("Authorization", `Bearer ${newToken}`);
        } else {
          originalRequest.headers = {
            ...(originalRequest.headers as any || {}),
            Authorization: `Bearer ${newToken}`,
          };
        }

        return api(originalRequest);
      } catch (err) {
        return Promise.reject(err);
      }
    }

    return Promise.reject(error);
  }
);


/* ---------------------------
   High-level auth helpers
   (authAPI)
   --------------------------- */
export const authAPI = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const response = await api.post("/auth/login", formData, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });

    // Return full response.data so caller can inspect status/message
    const data = response.data;
    // store tokens if present
    const payload = data?.data || data;
    const access_token = payload?.access_token;
    const refresh_token = payload?.refresh_token;
    if (access_token) setTokens({ access_token, refresh_token });
    return data;
  },

  signup: async (
    firstname: string,
    lastname: string,
    email: string,
    hashed_password: string
  ) => {
    const response = await api.post("/auth/register", {
      firstname,
      lastname,
      email,
      hashed_password,
    });
    return response.data;
  },

  logout: () => {
    clearTokens();
    useAuthStore.getState().logout();
  },

  getCurrentUser: async () => {
    const res = await api.get("/auth/me");
    return res.data;
  },

  updateProfile: async (id: number, data: any) => {
    const response = await api.patch(`/users/${id}`, data);
    return response.data.data;
  },

  changePassword: async (current_password: string, new_password: string) => {
    const response = await api.post("/users/change-password", {
      current_password,
      new_password,
    });
    return response.data;
  },

  deleteAccount: async (id: number) => {
    // API returns 204 No Content in your spec; axios will set response.status
    const response = await api.delete(`/users/${id}`);
    return response;
  },

};

/* -----------------------------------------------------------
    MOVIES API
----------------------------------------------------------- */
export const moviesAPI = {
  search: async (params: {
    title?: string;
    genre?: string[];
    language?: string[];
    release_year?: number;
    sort_by?: string;
    order?: string;
    page?: number;
    limit?: number;
    search_bar?: boolean;
  }) => {
    const sp = new URLSearchParams();

    if (params.title) sp.append("title", params.title);
    if (params.release_year) sp.append("release_year", params.release_year.toString());
    if (params.sort_by) sp.append("sort_by", params.sort_by);
    if (params.order) sp.append("order", params.order);
    if (params.search_bar !== undefined) sp.append("search_bar", params.search_bar.toString());

    // Genre → comma-separated list
    if (params.genre?.length) {
      sp.append("genre", params.genre.join(","));
    }

    // Language → comma-separated list
    if (params.language?.length) {
      sp.append("language", params.language.join(","));
    }

    sp.append("page", params.page?.toString() || "1");
    sp.append("limit", params.limit?.toString() || "50");

    const response = await api.get(`/movies/explore?${sp.toString()}`);
    return response.data;
  },


  getById: async (tmdbId: number) => {
    const response = await api.get(`/movies/tmdb/${tmdbId}`);
    return response.data;
  },

  rateMovie: async (
    id: number,
    rating?: number | null,
    review?: string | null,
    status?: "watchlist" | "watched" | null
  ) => {
    const payload: any = {
      movie_id: id,
    };

    // only include fields if they are valid
    if (typeof rating === "number" && rating > 0) {
      payload.rating = rating;
    }

    if (typeof review === "string" && review.trim().length > 0) {
      payload.review = review.trim();
    }

    if (status === "watchlist" || status === "watched") {
      payload.status = status;
      payload.rating = rating;
      payload.review = review;
    }

    const response = await api.post("/feedbacks/", payload);
    return response.data;
  },

  getUserRating: async (id: number) => {
    const response = await api.get(`/feedbacks/${id}`);
    // return the raw data object expected by MovieModal
    return response.data.data;
  },

  getPersonalizedRecommendations: async (params?: { limit?: number }) => {
    const searchParams = new URLSearchParams();
    if (params?.limit)
      searchParams.append("limit", params.limit.toString());
    const response = await api.get(
      `/recommendations/personalized?${searchParams.toString()}`
    );
    return response.data;
  },

  getBecauseYouWatchedRecommendations: async () => {
    const response = await api.get("/recommendations/because-you-watched");
    return response.data;
  },
};

export const recommendationsAPI = {
  guest: (params: any) => api.get("/recommendations/guest", { params }),
  personalized: (limit = 10) => api.get("/recommendations/personalized", { params: { limit } }),
  recent: (limit = 12) => api.get("/recommendations/recent", { params: { limit } }),
  recommend: (params: any) => api.get("/recommendations/recommend", { params }),
  similarMovies: (id: number, limit = 10) => api.get("/recommendations/similar-movies", { params: { id, limit } }),
};

export const userAPI = {
  stats: () => api.get("/feedbacks/stats"),
};

export default api;
