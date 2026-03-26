type SkeletonProps = {
  lines?: number;
};

export function Skeleton({ lines = 1 }: SkeletonProps) {
  return (
    <div className="skeleton-stack" role="presentation">
      {Array.from({ length: lines }).map((_, idx) => (
        <div key={idx} className="skeleton-line" />
      ))}
    </div>
  );
}
