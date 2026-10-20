import {
  loginApiAuthLoginPost,
  meApiAuthMeGet,
  registerApiAuthRegisterPost,
} from "../client/sdk.gen";
import type { AuthLoginRequest, AuthRegisterRequest, AuthUser } from "../client/types.gen";
import { clearStoredToken, getStoredToken, persistToken } from "./auth-token";

export { getStoredToken, persistToken, clearStoredToken };

export function buildAuthHeaders(token = getStoredToken()) {
  return token ? { authorization: `Bearer ${token}` } : {};
}

export async function registerAuthor(payload: AuthRegisterRequest) {
  const response = await registerApiAuthRegisterPost({ body: payload });
  if (!response.data) throw new Error("Registration did not return a session.");
  return response.data;
}

export async function loginAuthor(payload: AuthLoginRequest) {
  const response = await loginApiAuthLoginPost({ body: payload });
  if (!response.data) throw new Error("Login did not return a session.");
  return response.data;
}

export async function fetchCurrentAuthor(): Promise<AuthUser> {
  const response = await meApiAuthMeGet();
  if (!response.data) throw new Error("Session lookup failed.");
  return response.data.user;
}
