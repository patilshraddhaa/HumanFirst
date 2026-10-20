import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { DraftResponse, DraftUpdateRequest } from "../client/types.gen";

export type { DraftResponse, DraftUpdateRequest };

const KEY = "humanfirst-drafts";
const now = () => new Date().toISOString();
const read = (): DraftResponse[] => JSON.parse(localStorage.getItem(KEY) ?? "[]");
const write = (drafts: DraftResponse[]) => localStorage.setItem(KEY, JSON.stringify(drafts));
const words = (body: string) => body.trim() ? body.trim().split(/\s+/).length : 0;

type LocalDraftPatch = DraftUpdateRequest & Partial<Pick<DraftResponse, "status" | "locked_at">>;
function update(id: string, patch: LocalDraftPatch) {
  const drafts = read();
  const index = drafts.findIndex((draft) => draft.id === id);
  if (index < 0) throw new Error("Draft not found");
  const current = drafts[index];
  const next = { ...current, ...patch, word_count: patch.word_count ?? words(patch.body ?? current.body), updated_at: now() } as DraftResponse;
  drafts[index] = next; write(drafts); return next;
}

export function useGetDrafts(enabled = true) { return useQuery({ queryKey: ["drafts"], queryFn: () => read(), enabled }); }
export function useCreateDraft() { const qc = useQueryClient(); return useMutation({ mutationFn: async (title: string) => { const timestamp = now(); const draft: DraftResponse = { id: crypto.randomUUID(), author_id: "local-author", title: title || "", body: "", status: "draft", word_count: 0, keystroke_count: 0, session_duration_seconds: 0, pause_events: 0, paste_attempts: 0, reading_time_minutes: 0, locked_at: null, created_at: timestamp, updated_at: timestamp }; write([draft, ...read()]); return draft; }, onSuccess: () => void qc.invalidateQueries({ queryKey: ["drafts"] }) }); }
export function useDraft(id: string | undefined) { return useQuery({ queryKey: ["draft", id], queryFn: () => { const draft = read().find((item) => item.id === id); if (!draft) throw new Error("Draft not found"); return draft; }, enabled: Boolean(id) }); }
export function useUpdateDraft(id: string | undefined) { const qc = useQueryClient(); return useMutation({ mutationFn: async (patch: LocalDraftPatch) => update(id!, patch), onSuccess: (draft) => { qc.setQueryData(["draft", id], draft); void qc.invalidateQueries({ queryKey: ["drafts"] }); } }); }
export function useFinalizeDraftLock(id: string | undefined) { const qc = useQueryClient(); return useMutation({ mutationFn: async (patch: DraftUpdateRequest) => update(id!, { ...patch, status: "locked", locked_at: now() }), onSuccess: (draft) => { qc.setQueryData(["draft", id], draft); void qc.invalidateQueries({ queryKey: ["drafts"] }); } }); }
export function useMcpPing(enabled = true) { return useQuery({ queryKey: ["mcp-ping"], queryFn: async () => ({ ok: true, token: "local-demo" }), enabled, staleTime: Infinity }); }
