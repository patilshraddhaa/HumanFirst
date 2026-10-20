type DraftEmptyStateProps = {
  onCreateDraft: () => void;
};

export function DraftEmptyState({ onCreateDraft }: DraftEmptyStateProps) {
  return (
    <div className="rounded-[24px] border border-dashed border-ml-grey-lightest bg-white px-8 py-12 text-center shadow-[0_20px_70px_rgba(15,23,42,0.05)]">
      <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-white-200 text-2xl text-ml-blue">
        +
      </div>
      <h3 className="mt-5 font-display text-[2rem] font-semibold tracking-[-0.04em] text-foreground">
        No drafts yet
      </h3>
      <p className="mx-auto mt-3 max-w-xl text-base leading-7 text-ml-grey-dark">
        Start with a blank draft, keep the article human-first, and bring your
        MCP assistant in after the core argument is on the page.
      </p>
      <button
        type="button"
        onClick={onCreateDraft}
        className="mt-8 inline-flex items-center justify-center rounded-[14px] bg-ml-red px-6 py-3 text-sm font-semibold text-white transition hover:bg-[#8f0909] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ml-red focus-visible:ring-offset-2"
      >
        + New draft
      </button>
    </div>
  );
}
