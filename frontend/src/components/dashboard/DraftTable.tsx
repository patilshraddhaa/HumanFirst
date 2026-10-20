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
    <div className="overflow-hidden rounded-[20px] border border-ml-grey-lightest bg-white shadow-[0_20px_70px_rgba(15,23,42,0.05)]">
      <div className="grid grid-cols-[minmax(0,2.6fr)_1fr_0.7fr_1fr_1fr] gap-4 border-b border-ml-grey-lightest px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        <span>Title</span>
        <span>Status</span>
        <span>Words</span>
        <span>Last edited</span>
        <span>Actions</span>
      </div>
      <div className="divide-y divide-ml-grey-lightest">
        {drafts.map((draft) => {
          const title = (draft.title ?? "").trim() || "Untitled";
          const continuePath = `/drafts/${draft.id}/edit`;
          const publicPath = continuePath;

          return (
            <div
              key={draft.id}
              className={cn(
                "grid grid-cols-[minmax(0,2.6fr)_1fr_0.7fr_1fr_1fr] gap-4 px-6 py-5 transition",
                "hover:bg-white-200/70",
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
                  className="text-ml-blue transition hover:text-[#143b60]"
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
