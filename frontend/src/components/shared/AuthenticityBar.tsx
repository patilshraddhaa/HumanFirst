import { formatPercent } from "./utils";

type AuthenticityBarProps = {
  aiWords: number;
  humanWords: number;
  label?: string;
};

export function AuthenticityBar({
  aiWords,
  humanWords,
  label = "Authenticity mix",
}: AuthenticityBarProps) {
  const totalWords = Math.max(aiWords + humanWords, 0);
  const humanPercent = totalWords === 0 ? 50 : (humanWords / totalWords) * 100;
  const aiPercent = totalWords === 0 ? 50 : 100 - humanPercent;

  return (
    <div className="panel-surface p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-ink-muted">
            {label}
          </p>
          <p className="mt-2 font-serif text-xl text-ink-base">
            {humanWords + aiWords} words tracked
          </p>
        </div>
        <div className="text-right text-sm text-ink-muted">
          <p>{formatPercent(humanPercent)} human</p>
          <p>{formatPercent(aiPercent)} AI</p>
        </div>
      </div>

      <div
        className="mt-4 grid h-3 overflow-hidden rounded-pill bg-canvas-accent"
        style={{ gridTemplateColumns: `${humanPercent}fr ${aiPercent}fr` }}
      >
        <div className="bg-human" title={`${formatPercent(humanPercent)} human`} />
        <div className="bg-ai" title={`${formatPercent(aiPercent)} AI`} />
      </div>

      <div className="mt-3 flex items-center gap-4 text-sm text-ink-muted">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-human" />
          <span>Human authored</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-ai" />
          <span>AI assisted</span>
        </div>
      </div>
    </div>
  );
}
