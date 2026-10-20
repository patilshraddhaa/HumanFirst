import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createDraft,
  getDraft,
  listDrafts,
  lockDraft,
  meApiAuthMeGet,
  updateDraft,
} from "../client/sdk.gen";
import type { DraftResponse, DraftUpdateRequest } from "../client/types.gen";

export type { DraftResponse, DraftUpdateRequest };

// ── Draft list ────────────────────────────────────────────────────────────────

export function useGetDrafts(enabled = true) {
  return useQuery({
    queryKey: ["drafts"],
    queryFn: async () => {
      const res = await listDrafts();
      return res.data.items;
    },
    enabled,
  });
}

// ── Create draft ──────────────────────────────────────────────────────────────

export function useCreateDraft() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (title: string) => {
      const res = await createDraft({ body: { title: title || undefined } });
      return res.data;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["drafts"] });
    },
  });
}

// ── Single draft ──────────────────────────────────────────────────────────────

export function useDraft(draftId: string | undefined) {
  return useQuery({
    queryKey: ["draft", draftId],
    queryFn: async () => {
      const res = await getDraft({ path: { draft_id: draftId! } });
      return res.data;
    },
    enabled: Boolean(draftId),
  });
}

export function useUpdateDraft(draftId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: DraftUpdateRequest) => {
      const res = await updateDraft({ path: { draft_id: draftId! }, body: payload });
      return res.data;
    },
    onSuccess: (draft) => {
      queryClient.setQueryData(["draft", draftId], draft);
      void queryClient.invalidateQueries({ queryKey: ["drafts"] });
    },
  });
}

// ── Finalize (patch + lock) ───────────────────────────────────────────────────

export function useFinalizeDraftLock(draftId: string | undefined) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: DraftUpdateRequest) => {
      let latest: DraftResponse | null = null;

      if (draftId && Object.keys(payload).length > 0) {
        const saved = await updateDraft({ path: { draft_id: draftId }, body: payload });
        latest = saved.data;
      }

      const locked = await lockDraft({ path: { draft_id: draftId! } });
      return locked.data ?? latest;
    },
    onSuccess: (draft) => {
      queryClient.setQueryData(["draft", draftId], draft);
      void queryClient.invalidateQueries({ queryKey: ["drafts"] });
    },
  });
}

// ── MCP status (checks /api/auth/me — token presence implies MCP configured) ──

export function useMcpPing(enabled = true) {
  return useQuery({
    queryKey: ["mcp-ping"],
    queryFn: async () => {
      const res = await meApiAuthMeGet();
      // MCP is "connected" when the user has an mcp_token (always present after register)
      return { ok: Boolean(res.data?.user?.mcp_token), token: res.data?.user?.mcp_token };
    },
    enabled,
    staleTime: 30_000,
  });
}
