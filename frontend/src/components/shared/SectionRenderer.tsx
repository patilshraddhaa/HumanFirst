import type { ReactNode } from "react";
import { cn } from "./utils";

type SectionTone = "human" | "ai";

type SectionRendererProps = {
  body: ReactNode;
  className?: string;
  meta?: ReactNode;
  title: string;
  tone: SectionTone;
};

const toneClasses: Record<SectionTone, string> = {
  human: "",
  ai: "section-ai",
};

const badgeClasses: Record<SectionTone, string> = {
  human: "border-human/30 bg-human-soft text-human",
  ai: "border-ai/30 bg-ai-soft text-ai",
};

export function SectionRenderer({
  body,
  className,
  meta,
  title,
  tone,
}: SectionRendererProps) {
  return (
    <section
      className={cn(
        tone === "human" ? "py-1" : "p-6 md:p-7",
        toneClasses[tone],
        className,
      )}
    >
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          {tone === "ai" ? (
            <span className={cn("badge-kicker", badgeClasses[tone])}>{tone}</span>
          ) : null}
          <h2
            className={cn(
              "font-serif text-2xl text-ink-base",
              tone === "ai" ? "mt-3" : "",
            )}
          >
            {title}
          </h2>
        </div>
        {meta ? <div className="text-sm text-ink-muted">{meta}</div> : null}
      </div>
      <div
        className={cn(
          "mt-5 text-base leading-7 text-ink-base",
          tone === "human" ? "font-serif" : "font-sans",
        )}
      >
        {body}
      </div>
    </section>
  );
}
