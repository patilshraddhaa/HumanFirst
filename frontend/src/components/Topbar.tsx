import type { ReactNode } from "react";
import { Link } from "react-router-dom";

type TopbarProps = {
  backHref?: string;
  backLabel?: string;
  center?: ReactNode;
  children?: ReactNode;
  connected?: boolean;
};

export function Topbar({
  backHref,
  backLabel,
  center,
  children,
  connected,
}: TopbarProps) {
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-[#ebeae4]/90 backdrop-blur">
      <div className="mx-auto flex h-[4.5rem] max-w-[1160px] items-center justify-between gap-4 px-6 lg:px-12">
        <div className="flex items-center gap-5">
          <Link
            to="/dashboard"
            className="flex items-center gap-2 text-[1.1rem] font-semibold tracking-[-0.04em] text-foreground"
          >
            <span className="grid h-7 w-7 place-items-center border border-foreground font-mono text-xs">H</span>HumanFirst
          </Link>
          {backHref && backLabel ? (
            <Link className="text-sm font-semibold text-ml-blue" to={backHref}>
              ← {backLabel}
            </Link>
          ) : null}
        </div>
        <div className="hidden flex-1 items-center justify-center md:flex">
          {center ??
            (connected !== undefined ? (
              <span className="inline-flex items-center gap-2 rounded-full border border-ml-grey-lightest bg-white px-4 py-2 text-sm font-medium text-ml-grey-dark">
                <span
                  aria-hidden="true"
                  className={
                    connected
                      ? "h-2.5 w-2.5 rounded-full bg-emerald-500"
                      : "h-2.5 w-2.5 rounded-full border border-ml-grey-dark"
                  }
                />
                {connected ? "Connected" : "Not connected"}
              </span>
            ) : null)}
        </div>
        <div className="flex items-center gap-3">
          {children ?? (
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-[#5C6070] text-sm font-semibold text-white">
              SP
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
