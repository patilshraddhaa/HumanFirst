import type { ReactNode } from "react";
import { ActionButton } from "./ActionButton";

type BaseStateProps = {
  actionLabel?: string;
  body: string;
  onAction?: () => void;
  title: string;
};

function StateCard({
  accentClassName,
  actionLabel,
  body,
  onAction,
  title,
}: BaseStateProps & { accentClassName: string }) {
  return (
    <div className={`state-card ${accentClassName}`}>
      <h2 className="font-serif text-2xl text-ink-base">{title}</h2>
      <p className="mt-2 max-w-xl text-sm leading-6 text-ink-muted">{body}</p>
      {actionLabel && onAction ? (
        <div className="mt-5">
          <ActionButton variant="secondary" onClick={onAction}>
            {actionLabel}
          </ActionButton>
        </div>
      ) : null}
    </div>
  );
}

export function LoadingState({ title = "Loading workspace...", body = "Pulling the current lap, linked resources, and delivery context." }: Partial<BaseStateProps>) {
  return (
    <div className="state-card border-brand/30 bg-brand-soft/40">
      <div className="flex items-center gap-3">
        <span className="h-3 w-3 animate-pulse rounded-full bg-brand" />
        <h2 className="font-serif text-2xl text-ink-base">{title}</h2>
      </div>
      <p className="mt-2 max-w-xl text-sm leading-6 text-ink-muted">{body}</p>
    </div>
  );
}

export function EmptyState(props: BaseStateProps) {
  return <StateCard {...props} accentClassName="border-warning/35 bg-warning-soft/55" />;
}

export function ErrorState(props: BaseStateProps) {
  return <StateCard {...props} accentClassName="border-danger/35 bg-danger-soft/55" />;
}

export function SectionStack({ children }: { children: ReactNode }) {
  return <div className="grid gap-5">{children}</div>;
}
