import { useMemo, useState } from "react";
import { Flame, Plus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { useCreateDraft, useGetDrafts, useMcpPing } from "../../api/drafts";
import { getErrorMessage } from "../../api/errors";
import { DraftEmptyState } from "../../components/dashboard/DraftEmptyState";
import { DraftTable } from "../../components/dashboard/DraftTable";
import { DraftTableSkeleton } from "../../components/dashboard/DraftTableSkeleton";
import { McpConnectionChip } from "../../components/dashboard/McpConnectionChip";
import { Topbar } from "../../components/Topbar";
import { useAuth } from "../../context/AuthContext";

export function DashboardPage() {
  const navigate = useNavigate();
  const { logout, user } = useAuth();
  const [errorToast, setErrorToast] = useState<string | null>(null);
  const draftsQuery = useGetDrafts(Boolean(user));
  const createDraft = useCreateDraft();
  const mcpQuery = useMcpPing(Boolean(user));

  const publishedCount = useMemo(
    () =>
      (draftsQuery.data ?? []).filter((draft) => draft.status === "published")
        .length,
    [draftsQuery.data],
  );

  if (!user) {
    return null;
  }

  async function handleCreateDraft() {
    setErrorToast(null);

    try {
      const draft = await createDraft.mutateAsync("");
      navigate(`/drafts/${draft.id}/edit`);
    } catch (error) {
      setErrorToast(getErrorMessage(error, "Failed to create a new draft."));
    }
  }

  return (
    <div className="hf-page">
      <Topbar
        center={
          <McpConnectionChip
            isTesting={mcpQuery.isFetching}
            onTestConnection={() => void mcpQuery.refetch()}
            status={mcpQuery.data}
            user={user}
          />
        }
      >
        <button
          type="button"
          onClick={handleCreateDraft}
          disabled={createDraft.isPending}
          className="inline-flex h-11 items-center justify-center rounded-2xl bg-primary px-5 text-sm font-bold text-primary-foreground shadow-[0_4px_0_rgba(19,103,88,0.4)] transition hover:-translate-y-px disabled:cursor-not-allowed"
        >
          <Plus className="mr-1.5 h-4 w-4" />{createDraft.isPending ? "Creating..." : "New thought"}
        </button>
        <div className="flex items-center gap-3 rounded-full border border-ml-grey-lightest bg-white px-2 py-2">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#5C6070] text-sm font-semibold text-white">
            {(user.name ?? user.display_name ?? "?")
              .split(" ")
              .filter(Boolean)
              .slice(0, 2)
              .map((part: string) => part[0]?.toUpperCase())
              .join("") || "?"}
          </div>
          <div className="hidden pr-2 text-left sm:block">
            <p className="text-sm font-medium text-foreground">{user.name}</p>
            <button
              type="button"
              onClick={logout}
              className="text-xs text-ml-blue transition hover:text-[#143b60]"
            >
              Sign out
            </button>
          </div>
        </div>
      </Topbar>

      <main className="mx-auto max-w-[1160px] px-6 py-10 lg:px-12">
        <div className="max-w-4xl">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
            Your thinking space
          </p>
          <h1 className="mt-2 font-serif text-[3.5rem] font-semibold tracking-[-0.06em] text-foreground">
            Welcome back, {user.name?.split(" ")[0] ?? "writer"}.
          </h1>
          <p className="mt-3 text-lg text-ml-grey-dark">
            {draftsQuery.isSuccess ? `${draftsQuery.data.length} ideas in progress · ${publishedCount} shared` : "A calm place to build stronger ideas."}
          </p>
        </div>

        <div className="mt-8 grid gap-5 md:grid-cols-[1fr_18rem]">
          <section className="rounded-3xl border border-[#ecdcb6] bg-[#fff0c7] p-6 shadow-[0_5px_0_rgba(146,103,28,0.12)]">
            <div className="flex items-start gap-4"><span className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-[#ffcc65] text-[#704900]"><Flame className="h-5 w-5" /></span><div><p className="font-bold">One small practice today</p><p className="mt-1 text-sm leading-6 text-[#675735]">Write one honest paragraph before asking AI for a perspective.</p></div></div>
          </section>
          <section className="rounded-3xl border border-[#b9e2d7] bg-[#e3f7f0] p-6 shadow-[0_5px_0_rgba(27,117,97,0.1)]">
            <p className="hf-kicker">Your streak</p><p className="mt-1 font-serif text-3xl font-semibold">Start today</p><p className="mt-1 text-sm text-muted-foreground">One thought is enough.</p>
          </section>
        </div>

        <div className="mt-8">
          {draftsQuery.isLoading ? <DraftTableSkeleton /> : null}

          {draftsQuery.isError ? (
            <div className="rounded-[24px] border border-destructive bg-destructive-bg px-7 py-8 shadow-[0_20px_70px_rgba(15,23,42,0.05)]">
              <h2 className="font-display text-[2rem] font-semibold tracking-[-0.04em] text-foreground">
                Drafts failed to load
              </h2>
              <p className="mt-3 max-w-2xl text-base leading-7 text-ml-grey-dark">
                {getErrorMessage(
                  draftsQuery.error,
                  "The draft list is unavailable right now.",
                )}
              </p>
              <button
                type="button"
                onClick={() => void draftsQuery.refetch()}
                className="mt-6 inline-flex items-center justify-center rounded-[14px] border border-foreground px-5 py-3 text-sm font-semibold text-foreground transition hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ml-blue focus-visible:ring-offset-2"
              >
                Retry →
              </button>
            </div>
          ) : null}

          {draftsQuery.isSuccess && draftsQuery.data.length === 0 ? (
            <DraftEmptyState onCreateDraft={handleCreateDraft} />
          ) : null}

          {draftsQuery.isSuccess && draftsQuery.data.length > 0 ? (
            <DraftTable drafts={draftsQuery.data} />
          ) : null}
        </div>
      </main>

      {errorToast ? (
        <div className="fixed bottom-6 right-6 z-50 flex max-w-sm items-start gap-3 rounded-[16px] border border-ml-grey-lightest bg-white px-4 py-4 shadow-[0_24px_80px_rgba(15,23,42,0.12)]">
          <span className="mt-0.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-destructive text-xs font-bold text-white">
            !
          </span>
          <div className="flex-1 text-sm text-foreground">{errorToast}</div>
          <button
            type="button"
            onClick={() => setErrorToast(null)}
            className="text-muted-foreground transition hover:text-foreground"
          >
            ✕
          </button>
        </div>
      ) : null}
    </div>
  );
}
