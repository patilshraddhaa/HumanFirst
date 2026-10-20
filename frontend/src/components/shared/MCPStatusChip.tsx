import { cn } from "./utils";

type MCPStatusChipProps = {
  connected: boolean;
  onClick?: () => void;
};

export function MCPStatusChip({ connected, onClick }: MCPStatusChipProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "inline-flex items-center gap-2 rounded-pill border px-3 py-2 text-sm font-medium transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand",
        connected
          ? "border-success/30 bg-success-soft text-success"
          : "border-danger/30 bg-danger-soft text-danger",
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "h-2.5 w-2.5 rounded-full",
          connected ? "bg-success" : "bg-danger",
        )}
      />
      <span>MCP {connected ? "connected" : "disconnected"}</span>
    </button>
  );
}
