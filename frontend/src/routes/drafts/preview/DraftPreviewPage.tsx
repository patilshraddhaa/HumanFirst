import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router-dom";
import { useDraft } from "../../../api/drafts";
import { publishDraft } from "../../../client/sdk.gen";
import { ActionButton, AuthenticityBar, ErrorState, LoadingState, PageShell, SectionStack } from "../../../components/shared";

export function DraftPreviewPage() {
  const { draftId = "" } = useParams();
  const queryClient = useQueryClient();
  const draft = useDraft(draftId);

  const publish = useMutation({
    mutationFn: () => publishDraft({ path: { draft_id: draftId } }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["draft", draftId] });
    },
  });

  const data = draft.data;

  return (
    <div className="min-h-screen bg-[linear-gradient(165deg,_#f5efe3_0%,_#eef3f8_44%,_#dbe9e4_100%)]">
      <PageShell
        eyebrow="Draft preview"
        title={data?.title ?? "Preview"}
        subtitle="Review your locked draft and publish it when ready."
        actions={
          <ActionButton
            onClick={() => void publish.mutateAsync()}
            disabled={!data || publish.isPending || Boolean(data.locked_at === null)}
          >
            {publish.isPending ? "Publishing..." : "Publish"}
          </ActionButton>
        }
      >
        {draft.isLoading ? (
          <LoadingState title="Loading preview..." body="Fetching draft state." />
        ) : draft.isError || !data ? (
          <ErrorState
            title="Preview unavailable"
            body="The draft could not be loaded."
            actionLabel="Retry"
            onAction={() => void draft.refetch()}
          />
        ) : (
          <SectionStack>
            <div className="rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(52,58,64,0.1)]">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Locked draft</p>
              <h2 className="mt-3 font-['Fraunces'] text-3xl text-stone-900">{data.title ?? "Untitled"}</h2>
              <div className="mt-4">
                <AuthenticityBar humanWords={data.word_count} aiWords={0} />
              </div>
              <div className="mt-6 grid grid-cols-3 gap-4 text-center text-sm">
                <div className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-3 py-4">
                  <p className="text-lg font-semibold text-stone-900">{data.word_count}</p>
                  <p className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">Words</p>
                </div>
                <div className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-3 py-4">
                  <p className="text-lg font-semibold text-stone-900">{data.keystroke_count}</p>
                  <p className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">Keystrokes</p>
                </div>
                <div className="rounded-[1.25rem] border border-stone-200 bg-stone-50 px-3 py-4">
                  <p className="text-lg font-semibold text-stone-900">{data.paste_attempts}</p>
                  <p className="mt-1 text-xs font-medium uppercase tracking-[0.18em] text-stone-500">Paste attempts</p>
                </div>
              </div>
            </div>

            <div className="rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(52,58,64,0.08)]">
              <p className="whitespace-pre-wrap text-base leading-7 text-stone-700">{data.body}</p>
            </div>

            {publish.isSuccess ? (
              <div className="rounded-[2rem] border border-emerald-200 bg-emerald-50 px-7 py-6">
                <p className="text-sm font-semibold text-emerald-700">Published successfully.</p>
              </div>
            ) : null}
            {publish.isError ? (
              <div className="rounded-[2rem] border border-rose-200 bg-rose-50 px-7 py-6">
                <p className="text-sm font-semibold text-rose-700">Publish failed. Try again.</p>
              </div>
            ) : null}
          </SectionStack>
        )}
      </PageShell>
    </div>
  );
}
