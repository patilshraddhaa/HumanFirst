import { ActionButton, SectionRenderer } from "../shared";

type SectionCardProps = {
  body: string;
  createdAtLabel: string;
  onDelete?: () => void;
  title: string;
  tone: "human" | "ai";
};

export function SectionCard({
  body,
  createdAtLabel,
  onDelete,
  title,
  tone,
}: SectionCardProps) {
  return (
    <SectionRenderer
      tone={tone}
      title={title}
      meta={
        <div className="flex items-center gap-3">
          <span>{createdAtLabel}</span>
          {tone === "ai" && onDelete ? (
            <ActionButton variant="ghost" className="px-3 py-1.5 text-xs" onClick={onDelete}>
              Delete section
            </ActionButton>
          ) : null}
        </div>
      }
      body={<p>{body}</p>}
    />
  );
}
