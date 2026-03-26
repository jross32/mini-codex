import type { ReactNode } from "react";

type EmptyStateProps = {
  title: string;
  message: string;
  action?: ReactNode;
  icon?: ReactNode;
};

export function EmptyState({ title, message, action, icon }: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-icon" aria-hidden="true">
        {icon ?? "i"}
      </div>
      <div className="empty-copy">
        <p className="pill soft">{title}</p>
        <p className="muted">{message}</p>
      </div>
      {action ? <div className="empty-action">{action}</div> : null}
    </div>
  );
}
