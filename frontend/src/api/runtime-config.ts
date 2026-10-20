import type { AxiosRequestConfig } from "axios";

// Production: frontend is served from the same origin as the backend — empty
// baseURL makes axios use relative URLs. Dev: hit the standalone backend on :8000.
export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ??
  (import.meta.env.VITE_API_BASE as string | undefined) ??
  (import.meta.env.PROD ? "" : "http://localhost:8000");

export function createClientConfig(config: AxiosRequestConfig = {}): AxiosRequestConfig {
  return { ...config, baseURL: API_BASE_URL };
}
