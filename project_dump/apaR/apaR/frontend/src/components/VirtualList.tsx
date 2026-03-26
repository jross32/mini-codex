import { useMemo, useRef } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";

type VirtualListProps<T> = {
  items: T[];
  itemHeight: number;
  renderRow: (item: T, index: number) => React.ReactNode;
  overscan?: number;
  height?: number;
  className?: string;
};

export function VirtualList<T>({
  items,
  itemHeight,
  renderRow,
  overscan = 8,
  height = 420,
  className = "",
}: VirtualListProps<T>) {
  const parentRef = useRef<HTMLDivElement | null>(null);
  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => itemHeight,
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();
  const totalHeight = useMemo(() => virtualizer.getTotalSize(), [virtualizer]);

  return (
    <div ref={parentRef} className={`virtual-list ${className}`} style={{ height, overflow: "auto" }}>
      <div style={{ height: totalHeight, position: "relative" }}>
        {virtualItems.map((virtualRow) => (
          <div
            key={virtualRow.key}
            style={{
              position: "absolute",
              top: 0,
              left: 0,
              right: 0,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            {renderRow(items[virtualRow.index], virtualRow.index)}
          </div>
        ))}
      </div>
    </div>
  );
}
