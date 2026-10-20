// SDK — all functions call the backend via axios, configured from runtime-config.
// Auth endpoints send no Authorization header (login/register).
// Protected endpoints attach the stored Bearer token automatically.

import axios from "axios";
import { API_BASE_URL } from "../api/runtime-config";
import { getStoredToken } from "../api/auth-token";
import type {
  AuthMeResponse,
  AuthResponse,
  AuthLoginRequest,
  AuthRegisterRequest,
  DraftCreateRequest,
  DraftListResponse,
  DraftResponse,
  DraftUpdateRequest,
  PostCommentCreateEnvelope,
  PostCommentCreateRequest,
  PostCommentListEnvelope,
  PostDetailResponse,
  PostLikeRequest,
  PostLikeResponse,
  PostListResponse,
  PublicPostDetailResponse,
} from "./types.gen";

const api = axios.create({ baseURL: API_BASE_URL });

function authHeaders() {
  const token = getStoredToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// ── Health ───────────────────────────────────────────────────────────────────

export async function getHealthz() {
  const res = await api.get<{ status: string }>("/healthz");
  return { data: res.data };
}

// ── Auth ─────────────────────────────────────────────────────────────────────

export async function registerApiAuthRegisterPost(options: { body: AuthRegisterRequest }) {
  const res = await api.post<AuthResponse>("/api/auth/register", options.body);
  return { data: res.data };
}

export async function loginApiAuthLoginPost(options: { body: AuthLoginRequest }) {
  const res = await api.post<AuthResponse>("/api/auth/login", options.body);
  return { data: res.data };
}

export async function meApiAuthMeGet() {
  const res = await api.get<AuthMeResponse>("/api/auth/me", { headers: authHeaders() });
  return { data: res.data };
}

// ── Drafts ───────────────────────────────────────────────────────────────────

export async function listDrafts() {
  const res = await api.get<DraftListResponse>("/api/drafts", { headers: authHeaders() });
  return { data: res.data };
}

export async function createDraft(options: { body: DraftCreateRequest }) {
  const res = await api.post<DraftResponse>("/api/drafts", options.body, { headers: authHeaders() });
  return { data: res.data };
}

export async function getDraft(options: { path: { draft_id: string } }) {
  const res = await api.get<DraftResponse>(`/api/drafts/${options.path.draft_id}`, { headers: authHeaders() });
  return { data: res.data };
}

export async function updateDraft(options: { path: { draft_id: string }; body: DraftUpdateRequest }) {
  const res = await api.patch<DraftResponse>(`/api/drafts/${options.path.draft_id}`, options.body, { headers: authHeaders() });
  return { data: res.data };
}

export async function lockDraft(options: { path: { draft_id: string } }) {
  const res = await api.post<DraftResponse>(`/api/drafts/${options.path.draft_id}/lock`, undefined, { headers: authHeaders() });
  return { data: res.data };
}

export async function publishDraft(options: { path: { draft_id: string } }) {
  const res = await api.post<PostDetailResponse>(`/api/drafts/${options.path.draft_id}/publish`, undefined, { headers: authHeaders() });
  return { data: res.data };
}

// ── Posts ────────────────────────────────────────────────────────────────────

export async function listPosts() {
  const res = await api.get<PostListResponse>("/api/posts");
  return { data: res.data };
}

export async function getPostBySlug(options: { path: { slug: string } }) {
  const res = await api.get<PublicPostDetailResponse>(`/api/posts/${options.path.slug}`);
  return { data: res.data };
}

export async function likePost(options: { path: { post_id: string }; body: PostLikeRequest }) {
  const res = await api.post<PostLikeResponse>(`/api/posts/${options.path.post_id}/likes`, options.body);
  return { data: res.data };
}

export async function unlikePost(options: { path: { post_id: string }; body: PostLikeRequest }) {
  const res = await api.delete<PostLikeResponse>(`/api/posts/${options.path.post_id}/likes`, { data: options.body });
  return { data: res.data };
}

export async function createPostComment(options: { path: { post_id: string }; body: PostCommentCreateRequest }) {
  const res = await api.post<PostCommentCreateEnvelope>(`/api/posts/${options.path.post_id}/comments`, options.body);
  return { data: res.data };
}

export async function listPostComments(options: { path: { post_id: string } }) {
  const res = await api.get<PostCommentListEnvelope>(`/api/posts/${options.path.post_id}/comments`);
  return { data: res.data };
}
