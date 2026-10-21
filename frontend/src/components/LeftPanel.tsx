export function LeftPanel() {
  return (
    <aside className="relative hidden min-h-screen flex-1 overflow-hidden bg-[#163d35] px-16 py-14 text-white lg:flex">
      <div className="relative z-10 flex max-w-xl flex-col">
        <p className="flex items-center gap-2 text-[1.5rem] font-bold tracking-[-0.04em]"><span className="grid h-8 w-8 place-items-center rounded-xl bg-[#ffcc65] text-sm text-[#163d35]">H</span>HumanFirst</p>

        <div className="mt-28">
          <p className="text-sm font-bold uppercase tracking-[0.2em] text-[#9ee2cf]">Make thinking a practice</p>
          <h1 className="mt-5 font-serif text-[4.4rem] font-semibold leading-[0.94] tracking-[-0.06em] text-white">
            Your ideas.<br /><span className="text-[#ffcc65]">Stronger.</span><br />Still yours.
          </h1>
        </div>

        <p className="mt-9 max-w-sm text-lg leading-8 text-white/70">
          Start with your own point of view. Bring in AI only when you are ready for a thoughtful challenge.
        </p>

        <div className="mt-14 grid max-w-sm gap-3">
          {[
            "1 Write",
            "2 Enrich with your AI",
            "3 Publish transparently",
          ].map((label) => (
            <div
              key={label}
              className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/10 px-5 py-4"
            >
              <span className="grid h-6 w-6 place-items-center rounded-full bg-[#ffcc65] text-xs font-bold text-[#163d35]">{label[0]}</span>
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
