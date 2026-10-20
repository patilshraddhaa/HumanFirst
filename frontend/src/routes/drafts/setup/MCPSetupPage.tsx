import { useState } from "react";
import { ArrowRight, Check, Copy, Sparkles } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { useDraft } from "../../../api/drafts";
import { useAuth } from "../../../context/AuthContext";
import { Badge } from "../../../components/ui/badge";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../../components/ui/card";

const invitations = [
  "Challenge the assumptions in my argument.",
  "Show me viewpoints this draft may be missing.",
  "Identify claims that need evidence or sharper reasoning.",
  "Suggest a stronger structure without rewriting my voice.",
];

export function MCPSetupPage() {
  const { draftId = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const draft = useDraft(draftId);
  const [copied, setCopied] = useState(false);

  const snippet = user ? JSON.stringify({ mcpServers: { humanfirst: { url: `${window.location.origin}/mcp`, headers: { Authorization: `Bearer ${user.mcp_token}` } } } }, null, 2) : "";
  async function copyConfig() { await navigator.clipboard.writeText(snippet); setCopied(true); }

  return <main className="min-h-screen bg-background px-5 py-8 text-foreground md:px-10"><div className="mx-auto max-w-5xl">
    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">Step 2 · Invite AI at the right moment</p>
    <h1 className="mt-2 max-w-3xl font-serif text-4xl tracking-tight md:text-5xl">Use AI as a critical partner.</h1>
    <p className="mt-3 max-w-2xl leading-7 text-muted-foreground">Your original draft is preserved. Now choose the kind of pressure, evidence, or perspective that will help you think more clearly.</p>

    <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_20rem]"><div className="space-y-6">
      <Card><CardHeader><Badge variant="human" className="w-fit">Baseline locked</Badge><CardTitle>{draft.data?.title || "Untitled draft"}</CardTitle><CardDescription>{draft.data ? `${draft.data.word_count} human-written words are preserved and attributable.` : "Loading your baseline…"}</CardDescription></CardHeader></Card>
      <Card><CardHeader><Badge variant="ai" className="w-fit">Invite AI with intent</Badge><CardTitle className="text-xl">Try one of these prompts</CardTitle><CardDescription>These prompts ask AI to improve your thinking without taking it over.</CardDescription></CardHeader><CardContent className="grid gap-3">{invitations.map((prompt) => <div key={prompt} className="rounded-lg border border-border bg-muted/40 px-4 py-3 text-sm leading-6">{prompt}</div>)}</CardContent></Card>
      <Card><CardHeader><CardTitle className="text-xl">Connect your AI tool</CardTitle><CardDescription>Use the HumanFirst MCP server to add AI-assisted sections with their source and placement recorded.</CardDescription></CardHeader><CardContent><pre className="overflow-x-auto rounded-md bg-foreground p-4 text-xs leading-5 text-background">{snippet}</pre><Button variant="outline" className="mt-4" onClick={() => void copyConfig()}><Copy className="mr-2 h-4 w-4" />{copied ? "Config copied" : "Copy MCP config"}</Button></CardContent></Card>
    </div>
    <aside className="space-y-4"><Card className="border-primary/20 bg-secondary/40"><CardHeader><Sparkles className="h-5 w-5 text-primary"/><CardTitle className="text-xl">The rule</CardTitle></CardHeader><CardContent className="leading-6 text-muted-foreground">AI should make your thinking stronger—not arrive early enough to replace it.</CardContent></Card><Button className="w-full" size="lg" onClick={() => navigate(`/drafts/${draftId}/preview`)}>Review and publish <ArrowRight className="ml-2 h-4 w-4" /></Button><p className="flex items-center justify-center gap-2 text-xs text-muted-foreground"><Check className="h-3.5 w-3.5 text-primary" />You can review with or without AI additions.</p></aside>
    </div>
  </div></main>;
}
