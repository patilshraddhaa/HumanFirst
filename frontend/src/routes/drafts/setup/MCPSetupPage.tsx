import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../../../context/AuthContext";
import { ActionButton, ErrorState, PageShell } from "../../../components/shared";
import { useDraft } from "../../../api/drafts";

export function MCPSetupPage() {
  const { draftId = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const draft = useDraft(draftId);
  const [copied, setCopied] = useState(false);

  const snippet = user
    ? JSON.stringify(
        {
          mcpServers: {
            humanfirst: {
              url: `${window.location.origin}/mcp`,
              headers: { Authorization: `Bearer ${user.mcp_token}` },
            },
          },
        },
        null,
        2,
      )
    : "";

  async function handleCopy() {
    if (!snippet) return;
    await navigator.clipboard.writeText(snippet);
    setCopied(true);
  }

  if (!user) {
    return (
      <ErrorState
        title="Not authenticated"
        body="Sign in to access MCP setup."
      />
    );
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(165deg,_#f5efe3_0%,_#eef3f8_44%,_#dbe9e4_100%)]">
      <PageShell
        eyebrow="Draft locked / Connect Claude"
        title="Connect HumanFirst to Claude"
        subtitle="Add the MCP server once, then run /humanfirst in your Claude Code terminal."
      >
        <div className="grid gap-6 lg:grid-cols-[1.35fr_0.75fr]">
          <section className="rounded-[2rem] border border-white/70 bg-white/90 p-8 shadow-[0_24px_80px_rgba(52,58,64,0.1)]">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">Step 1</p>
            <h2 className="mt-3 font-['Fraunces'] text-4xl leading-tight text-stone-900">
              {copied ? "Config copied — restart Claude" : "Paste this config into Claude"}
            </h2>
            <p className="mt-3 max-w-3xl text-lg leading-8 text-stone-600">
              Open Claude Desktop config, add the HumanFirst MCP server, then restart Claude.
            </p>

            <pre className="mt-6 overflow-x-auto rounded-[1.5rem] bg-stone-900 px-6 py-5 text-xs leading-6 text-stone-100">
              {snippet}
            </pre>

            <div className="mt-4 flex gap-3">
              <ActionButton onClick={() => void handleCopy()}>
                {copied ? "Copied ✓" : "Copy config"}
              </ActionButton>
            </div>

            <div className="mt-5 rounded-[1.25rem] border border-stone-200 bg-stone-50 px-5 py-4 text-sm text-stone-600">
              <p className="font-semibold text-stone-700">Your MCP token</p>
              <p className="mt-2 break-all font-mono text-xs">{user.mcp_token}</p>
            </div>
          </section>

          <aside className="grid content-start gap-5">
            <div className="rounded-[2rem] border border-white/70 bg-white/90 p-6 shadow-[0_18px_60px_rgba(15,23,42,0.06)]">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-stone-500">
                Locked draft
              </p>
              <h3 className="mt-3 font-['Fraunces'] text-2xl text-stone-900">
                {draft.data?.title ?? "Loading…"}
              </h3>
              {draft.data ? (
                <p className="mt-2 text-sm text-stone-500">
                  {draft.data.word_count} words · {draft.data.paste_attempts} paste attempts
                </p>
              ) : null}
            </div>

            <div className="flex flex-col gap-3">
              <ActionButton variant="secondary" onClick={() => navigate(`/drafts/${draftId}/preview`)}>
                Skip for now
              </ActionButton>
              <ActionButton onClick={() => navigate(`/drafts/${draftId}/preview`)}>
                Go to preview
              </ActionButton>
            </div>
          </aside>
        </div>
      </PageShell>
    </div>
  );
}
