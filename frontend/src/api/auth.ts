import { apiClient } from "./client";
import type { TokenResponse, UserPublic } from "../types";

export function register(payload: { email: string; password: string; full_name: string }) {
  return apiClient.post<UserPublic>("/v1/auth/register", payload).then((r) => r.data);
}

export function login(payload: { email: string; password: string }) {
  return apiClient.post<TokenResponse>("/v1/auth/login", payload).then((r) => r.data);
}

export function getMyProfile() {
  return apiClient.get<UserPublic>("/v1/users/me").then((r) => r.data);
}
