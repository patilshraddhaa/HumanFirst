export function LeftPanel() {
  return (
    <aside className="relative hidden min-h-screen flex-1 overflow-hidden bg-hf-panel px-16 py-14 text-white lg:flex">
      <div className="relative z-10 flex max-w-xl flex-col">
        <p className="font-display text-[1.75rem] font-semibold tracking-[-0.03em]">
          HumanFirst
        </p>

        <div className="mt-28 space-y-2">
          <h1 className="font-display text-[4.3rem] font-semibold leading-[0.95] tracking-[-0.05em] text-white">
            Write first.
          </h1>
          <p className="font-display text-[4.1rem] font-semibold leading-[0.95] tracking-[-0.05em] text-hf-panel-h2">
            Enrich after.
          </p>
          <p className="font-display text-[4.1rem] font-semibold leading-[0.95] tracking-[-0.05em] text-hf-panel-h3">
            Every word traced.
          </p>
        </div>

        <p className="mt-10 max-w-sm text-lg leading-8 text-white/70">
          A publishing workspace for deliberate authorship. Write without AI,
          connect Claude when you need enrichment, and keep the full trail.
        </p>

        <div className="mt-16 grid max-w-sm gap-4">
          {[
            "1 Write",
            "2 Enrich with your AI",
            "3 Publish transparently",
          ].map((label) => (
            <div
              key={label}
              className="flex items-center gap-3 rounded-[14px] border border-hf-panel-pill-border bg-hf-panel-pill px-5 py-4 shadow-[0_18px_60px_rgba(0,0,0,0.18)]"
            >
              <span className="h-3 w-3 rounded-full bg-ml-red" />
              <span className="text-sm font-medium text-hf-panel-step">
                {label}
              </span>
            </div>
          ))}
        </div>

        <p className="mt-auto pt-16 text-sm text-white/30">humanfirst.app</p>
      </div>
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(255,255,255,0.05),transparent_28%),radial-gradient(circle_at_80%_25%,rgba(28,83,134,0.18),transparent_26%)]" />
    </aside>
  );
}
