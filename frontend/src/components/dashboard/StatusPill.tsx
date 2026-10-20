import type { DraftStatus } from "../../client";
import { cn } from "../shared/utils";

type StatusPillProps = {
  status: DraftStatus;
};

const statusClassNames: Record<DraftStatus, string> = {
  draft: "bg-white-200 text-ml-grey-dark border border-ml-grey-lightest",
  locked: "bg-ml-grey-lightest text-foreground border border-transparent",
  published: "bg-foreground text-white border border-transparent",
};

export function StatusPill({ status }: StatusPillProps) {
  return (
    <span
      className={cn(
        "inline-flex min-w-[84px] justify-center rounded-full px-3 py-1 text-xs font-semibold capitalize",
        statusClassNames[status],
      )}
    >
      {status}
    </span>
  );
}
