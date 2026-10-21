export function LeftPanel() {
  return (
    <aside className="relative hidden min-h-screen flex-1 overflow-hidden border-r border-black bg-[#151515] px-16 py-14 text-white lg:flex">
      <div className="relative z-10 flex max-w-xl flex-col">
        <p className="flex items-center gap-2 text-[1.3rem] font-semibold tracking-[-0.04em]"><span className="grid h-7 w-7 place-items-center border border-white font-mono text-xs">H</span>HumanFirst</p>

        <div className="mt-28">
          <p className="font-mono text-xs uppercase tracking-[0.15em] text-white/50">A writing workspace</p>
          <h1 className="mt-5 font-serif text-[4.4rem] font-medium leading-[0.94] tracking-[-0.06em] text-white">
            Think first.<br /><span className="text-[#8facff]">Then ask.</span>
          </h1>
        </div>

        <p className="mt-9 max-w-sm text-base leading-7 text-white/65">
          Start with your own point of view. Bring in AI only when you are ready for a thoughtful challenge.
        </p>

        <div className="mt-14 grid max-w-sm gap-0 border-y border-white/30">
          {[
            "Write",
            "Enrich with your AI",
            "Publish transparently",
          ].map((label) => (
            <div
              key={label}
              className="flex items-center gap-3 border-b border-white/10 px-1 py-4 last:border-0"
            >
              <span className="font-mono text-xs text-[#a9c3f5]">{label.slice(0, 1)}</span>
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
