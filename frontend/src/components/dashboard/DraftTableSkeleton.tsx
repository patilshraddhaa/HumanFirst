type DraftTableSkeletonProps = {
  rows?: number;
};

export function DraftTableSkeleton({
  rows = 3,
}: DraftTableSkeletonProps) {
  return (
    <div className="overflow-hidden rounded-[20px] border border-ml-grey-lightest bg-white shadow-[0_20px_70px_rgba(15,23,42,0.05)]">
      <div className="grid grid-cols-[minmax(0,2.6fr)_1fr_0.7fr_1fr_1fr] gap-4 border-b border-ml-grey-lightest px-6 py-4 text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">
        <span>Title</span>
        <span>Status</span>
        <span>Words</span>
        <span>Last edited</span>
        <span>Actions</span>
      </div>
      <div className="divide-y divide-ml-grey-lightest">
        {Array.from({ length: rows }).map((_, index) => (
          <div
            key={index}
            className="grid animate-pulse grid-cols-[minmax(0,2.6fr)_1fr_0.7fr_1fr_1fr] gap-4 px-6 py-5"
          >
            <span className="h-4 w-4/5 rounded-full bg-white-300" />
            <span className="h-4 w-16 rounded-full bg-white-300" />
            <span className="h-4 w-10 rounded-full bg-white-300" />
            <span className="h-4 w-24 rounded-full bg-white-300" />
            <span className="h-4 w-20 rounded-full bg-white-300" />
          </div>
        ))}
      </div>
    </div>
  );
}
