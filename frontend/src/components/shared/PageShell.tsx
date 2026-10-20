import type { ReactNode } from "react";
import { cn } from "./utils";

type PageShellProps = {
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
  eyebrow?: string;
  subtitle?: string;
  title: string;
};

export function PageShell({
  actions,
  children,
  className,
  eyebrow,
  subtitle,
  title,
}: PageShellProps) {
  return (
    <main className={cn("mx-auto flex min-h-screen w-full max-w-6xl flex-col px-6 py-10 md:px-10", className)}>
      <header className="mb-8 flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
        <div className="max-w-3xl">
          {eyebrow ? (
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-ink-muted">
              {eyebrow}
            </p>
          ) : null}
          <h1 className="mt-3 font-serif text-4xl leading-tight text-ink-base md:text-5xl">
            {title}
          </h1>
          {subtitle ? (
            <p className="mt-3 max-w-2xl text-base leading-7 text-ink-muted">
              {subtitle}
            </p>
          ) : null}
        </div>
        {actions ? <div className="flex flex-wrap items-center gap-3">{actions}</div> : null}
      </header>

      <div className="flex-1">{children}</div>
    </main>
  );
}
