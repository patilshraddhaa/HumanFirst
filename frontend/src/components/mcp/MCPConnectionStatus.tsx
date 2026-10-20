import { ActionButton } from "../shared";
import { cn } from "../shared/utils";

type MCPConnectionStatusProps = {
  connected: boolean;
  copied: boolean;
  isTesting: boolean;
  message: string;
  onTest: () => void;
};

export function MCPConnectionStatus({
  connected,
  copied,
  isTesting,
  message,
  onTest,
}: MCPConnectionStatusProps) {
  return (
    <div className="grid gap-4">
      <div className="space-y-2 text-sm text-ink-muted">
        <p className="font-semibold text-ink-base">Next steps</p>
        <div className="grid gap-3">
          {[
            "Copy the MCP config",
            "Restart Claude",
            connected ? "Connection verified" : "Test the connection",
            "Run /humanfirst",
          ].map((label, index) => (
            <div className="flex gap-3" key={label}>
              <div
                className={cn(
                  "mt-0.5 flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold",
                  connected && index === 2
                    ? "bg-success text-ink-inverse"
                    : "bg-canvas-accent text-ink-muted",
                )}
              >
                {connected && index === 2 ? "✓" : index + 1}
              </div>
              <div>
                <p className={cn("font-semibold", connected && index === 2 ? "text-success" : "text-ink-base")}>
                  {label}
                </p>
                <p>
                  {index === 0 && "Use the generated token for this author account."}
                  {index === 1 && "Claude loads the server from the local config file."}
                  {index === 2 &&
                    (connected
                      ? "HumanFirst can reach Claude through MCP."
                      : "HumanFirst pings /mcp/ping using the bearer token.")}
                  {index === 3 && "Claude suggests enrichments and saves accepted sections."}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-panel bg-ink-base px-5 py-4 font-mono text-sm font-semibold text-ink-inverse">
        $ claude /humanfirst
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <ActionButton onClick={onTest} disabled={isTesting} variant="secondary">
          {connected ? "Test again" : "Test connection"}
        </ActionButton>
        <p className={cn("text-sm", connected || copied ? "text-success" : "text-ink-muted")}>
          {message}
        </p>
      </div>
    </div>
  );
}
