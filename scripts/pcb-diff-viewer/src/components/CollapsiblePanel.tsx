/**
 * CollapsiblePanel - A panel that can be collapsed/expanded
 *
 * Similar to VS Code's sidebar panels.
 */

import { useState, type ReactNode } from 'react';

interface CollapsiblePanelProps {
  title: string;
  children: ReactNode;
  defaultCollapsed?: boolean;
  badge?: string | number;
  className?: string;
}

export function CollapsiblePanel({
  title,
  children,
  defaultCollapsed = false,
  badge,
  className = '',
}: CollapsiblePanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <div className={`pcb-collapsible-panel ${isCollapsed ? 'pcb-collapsible-panel--collapsed' : ''} ${className}`}>
      <div
        className="pcb-collapsible-panel__header"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className="pcb-collapsible-panel__chevron">
          {isCollapsed ? '▶' : '▼'}
        </span>
        <span className="pcb-collapsible-panel__title">{title}</span>
        {badge !== undefined && (
          <span className="pcb-collapsible-panel__badge">{badge}</span>
        )}
      </div>
      {!isCollapsed && (
        <div className="pcb-collapsible-panel__content">
          {children}
        </div>
      )}
    </div>
  );
}
