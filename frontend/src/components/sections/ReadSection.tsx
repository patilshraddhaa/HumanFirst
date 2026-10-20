import { SectionRenderer } from "../shared";

type ReadSectionProps = {
  body: string;
  index: number;
  title: string;
  tone: "human" | "ai";
};

export function ReadSection({ body, index, title, tone }: ReadSectionProps) {
  return (
    <div className="rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(52,58,64,0.08)]">
      <SectionRenderer
        tone={tone}
        title={title}
        meta={
          <span className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
            Section {index}
          </span>
        }
        body={
          <div className="space-y-4">
            {body.split(/\n{2,}/).map((paragraph) => (
              <p key={`${title}-${paragraph.slice(0, 24)}`}>{paragraph}</p>
            ))}
          </div>
        }
      />
    </div>
  );
}
