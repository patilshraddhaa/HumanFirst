import { useMemo, useState } from "react";

import type { AuthUser } from "../../client";
import { cn } from "../shared/utils";

type McpPingResult = { ok: boolean; token?: string } | undefined;

type McpConnectionChipProps = {
  isTesting: boolean;
  onTestConnection: () => void;
  status: McpPingResult;
  user: AuthUser;
};

export function McpConnectionChip({
  isTesting,
  onTestConnection,
  status,
  user,
}: McpConnectionChipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const connected = status?.ok ?? Boolean(user.mcp_token);
  const statusLabel = connected ? "Connected" : "Not connected";
  const snippet = useMemo(
    () =>
      JSON.stringify(
        {
          mcpServers: {
            humanfirst: {
              url: "https://humanfirst.app/mcp",
              headers: {
                Authorization: `Bearer ${user.mcp_token}`,
              },
            },
          },
        },
        null,
        2,
      ),
    [user.mcp_token],
  );

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setIsOpen((current) => !current)}
        className={cn(
          "inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ml-blue focus-visible:ring-offset-2",
          connected
            ? "border-emerald-200 bg-emerald-50 text-emerald-700"
            : "border-ml-grey-lightest bg-white text-ml-grey-dark",
        )}
      >
        <span
          aria-hidden="true"
          className={cn(
            "h-2.5 w-2.5 rounded-full",
            connected ? "bg-emerald-500" : "border border-ml-grey-dark bg-white",
          )}
        />
        <span>{statusLabel}</span>
      </button>

      {isOpen ? (
        <div className="absolute right-0 top-[calc(100%+12px)] z-30 w-[min(26rem,calc(100vw-2rem))] rounded-[20px] border border-ml-grey-lightest bg-white p-5 shadow-[0_24px_80px_rgba(15,23,42,0.12)]">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            MCP connection
          </p>
          <h3 className="mt-3 font-display text-[1.7rem] font-semibold tracking-[-0.04em] text-foreground">
            {connected ? "Claude is connected" : "Connect HumanFirst to Claude"}
          </h3>
          <p className="mt-2 text-sm leading-6 text-ml-grey-dark">
            Add the HumanFirst MCP server once, then retry the connection check
            whenever Claude Desktop is ready.
          </p>

          <div className="mt-5 rounded-[16px] border border-ml-grey-lightest bg-white-200 px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Author token
            </p>
            <p className="mt-2 break-all font-mono text-sm text-foreground">
              {user.mcp_token}
            </p>
          </div>

          <div className="mt-4 rounded-[16px] border border-ml-grey-lightest bg-white px-4 py-3">
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Claude config
            </p>
            <pre className="mt-3 overflow-x-auto rounded-[14px] bg-hf-panel px-4 py-4 text-xs leading-6 text-white">
              {snippet}
            </pre>
          </div>

          <div className="mt-5 flex items-center gap-3">
            <button
              type="button"
              onClick={onTestConnection}
              className="inline-flex items-center justify-center rounded-[14px] border border-ml-grey-lightest px-4 py-2 text-sm font-semibold text-foreground transition hover:bg-white-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ml-blue focus-visible:ring-offset-2"
            >
              {isTesting ? "Testing..." : connected ? "Test again" : "Test connection"}
            </button>
            <p
              className={cn(
                "text-sm",
                connected ? "text-emerald-700" : "text-muted-foreground",
              )}
            >
              {connected
                ? "Connection verified. You can continue into enrichment."
                : "Paste the config, restart Claude, then test the connection."}
            </p>
          </div>
        </div>
      ) : null}
    </div>
  );
}
