import axios from "axios";

const API_BASE_URL =
  import.meta.env.VITE_BASE_API_URL || "http://localhost:8000/filmy-api/v1";

export function setTokens({ access_token, refresh_token }: { access_token?: string; refresh_token?: string; }) {
  if (access_token) localStorage.setItem("access_token", access_token);
  if (refresh_token) localStorage.setItem("refresh_token", refresh_token);
}

export function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

export function getAccessToken() {
  return localStorage.getItem("access_token");
}
export function getRefreshToken() {
  return localStorage.getItem("refresh_token");
}

/**
 * Attempts to refresh the access token using refresh token.
 * Returns the new access_token (string) or throws.
 * Used by AuthInitializer and axios interceptor.
 */
export async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) throw new Error("No refresh token");

  const params = new URLSearchParams();
  params.append("refresh_token", refreshToken);

  const res = await axios.post(`${API_BASE_URL}/auth/refresh`, params, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  const data = res.data?.data || res.data;
  const newAccess = data?.access_token || data;
  const newRefresh = data?.refresh_token;

  if (!newAccess) throw new Error("Invalid refresh response");

  setTokens({ access_token: newAccess, refresh_token: newRefresh });
  return newAccess;
}
