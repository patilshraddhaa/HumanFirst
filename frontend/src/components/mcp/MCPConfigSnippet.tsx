import { ActionButton } from "../shared";

type MCPConfigSnippetProps = {
  configPath: string;
  copied: boolean;
  loading: boolean;
  onCopy: () => void;
  snippet: string;
};

export function MCPConfigSnippet({
  configPath,
  copied,
  loading,
  onCopy,
  snippet,
}: MCPConfigSnippetProps) {
  return (
    <div className="grid gap-5">
      <div>
        <p className="text-sm font-semibold text-ink-base">Config path</p>
        <div className="mt-2 rounded-panel border border-line-subtle bg-surface-base px-4 py-4 font-mono text-sm text-ink-muted">
          {loading ? <div className="h-4 w-2/3 animate-pulse rounded bg-canvas-accent" /> : configPath}
        </div>
      </div>

      <div>
        <p className="text-sm font-semibold text-ink-base">MCP server snippet</p>
        <pre className="mt-2 min-h-72 overflow-x-auto rounded-panel border border-line-subtle bg-surface-base px-5 py-5 text-sm leading-7 text-ink-base">
          {loading ? (
            <div className="grid gap-3">
              <div className="h-4 w-2/3 animate-pulse rounded bg-canvas-accent" />
              <div className="h-4 w-5/6 animate-pulse rounded bg-canvas-accent" />
              <div className="h-4 w-4/5 animate-pulse rounded bg-canvas-accent" />
              <div className="h-4 w-3/4 animate-pulse rounded bg-canvas-accent" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-canvas-accent" />
            </div>
          ) : (
            snippet
          )}
        </pre>
      </div>

      <ActionButton disabled={loading} onClick={onCopy}>
        {copied ? "Copied" : "Copy config snippet"}
      </ActionButton>
    </div>
  );
}
