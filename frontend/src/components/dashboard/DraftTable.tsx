import { Link } from "react-router-dom";

import type { DraftResponse as DraftRecord } from "../../client";
import { relativeDate } from "../../utils/relativeDate";
import { cn } from "../shared/utils";
import { StatusPill } from "./StatusPill";

type DraftTableProps = {
  drafts: DraftRecord[];
};

export function DraftTable({ drafts }: DraftTableProps) {
  return (
    <div className="overflow-hidden border border-border bg-white">
      <div className="flex items-center justify-between border-b border-border px-6 py-5"><div><p className="hf-kicker">Your library</p><p className="mt-1 font-serif text-2xl font-medium">Drafts and essays</p></div><span className="font-mono text-xs text-muted-foreground">{drafts.length} total</span></div>
      <div className="hidden grid-cols-[minmax(0,2.6fr)_1fr_0.7fr_1fr_1fr] gap-4 border-b border-border px-6 py-3 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground md:grid">
        <span>Title</span>
        <span>Status</span>
        <span>Words</span>
        <span>Last edited</span>
        <span>Actions</span>
      </div>
      <div className="divide-y divide-border">
        {drafts.map((draft) => {
          const title = (draft.title ?? "").trim() || "Untitled";
          const continuePath = draft.locked_at
            ? `/drafts/${draft.id}/setup`
            : `/drafts/${draft.id}/edit`;
          const publicPath = continuePath;

          return (
            <div
              key={draft.id}
              className={cn(
                "grid gap-3 px-6 py-5 transition md:grid-cols-[minmax(0,2.6fr)_1fr_0.7fr_1fr_1fr]",
                "hover:bg-[#f7f6f1]",
              )}
            >
              <div>
                <p className="text-[1rem] font-semibold text-foreground">
                  {title}
                </p>
                <p className="mt-1 text-sm text-muted-foreground">
                  {draft.status === "published"
                    ? "Published story"
                    : "Private working draft"}
                </p>
              </div>
              <div className="flex items-center">
                <StatusPill status={draft.status} />
              </div>
              <div className="flex items-center text-sm text-ml-grey-dark">
                {draft.word_count.toLocaleString()}
              </div>
              <div className="flex items-center text-sm text-ml-grey-dark">
                {relativeDate(draft.updated_at)}
              </div>
              <div className="flex items-center gap-4 text-sm font-medium">
                <Link
                  to={continuePath}
                  className="text-primary transition hover:underline"
                >
                  Continue →
                </Link>
                {draft.status === "published" ? (
                  <Link
                    target="_blank"
                    rel="noreferrer"
                    to={publicPath}
                    className="text-ml-grey-dark transition hover:text-foreground"
                  >
                    View ↗
                  </Link>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
