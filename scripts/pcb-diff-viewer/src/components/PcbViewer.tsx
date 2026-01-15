/**
 * PcbViewer - Main reusable PCB viewer component
 *
 * Can be embedded in:
 * - Package review station
 * - VS Code extension webview
 * - atopile website
 * - Any React application
 *
 * Features:
 * - Single PCB viewing
 * - Diff overlay mode
 * - Dynamic layers from KiCad data
 * - Net highlighting
 * - Element inspection
 * - Pan/zoom navigation
 * - Collapsible panels
 */

import { useEffect, useState } from 'react';
import { PcbViewerProvider, usePcbViewer } from '../context/PcbViewerContext';
import { Canvas } from './Canvas';
import { LayerPanel } from './LayerPanel';
import { NetPanel } from './NetPanel';
import { Inspector } from './Inspector';
import { Toolbar } from './Toolbar';
import { DiffSummary } from './DiffSummary';
import { OpacityPanel } from './OpacityPanel';
import type { PcbViewerProps, PcbData, PcbDiffData, BusData, ViewerMode } from '../types/pcb';

import '../styles/theme.css';
import '../styles/components.css';

// Collapsible sidebar panel component
interface CollapsibleSidebarPanelProps {
  title: string;
  children: React.ReactNode;
  defaultCollapsed?: boolean;
}

function CollapsibleSidebarPanel({ title, children, defaultCollapsed = false }: CollapsibleSidebarPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(defaultCollapsed);

  return (
    <div className={`pcb-sidebar-panel ${isCollapsed ? 'pcb-sidebar-panel--collapsed' : ''}`}>
      <div
        className="pcb-sidebar-panel__header"
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <span className="pcb-sidebar-panel__chevron">
          {isCollapsed ? '▶' : '▼'}
        </span>
        <span className="pcb-sidebar-panel__title">{title}</span>
      </div>
      {!isCollapsed && (
        <div className="pcb-sidebar-panel__content">
          {children}
        </div>
      )}
    </div>
  );
}

// Sidebar container
interface SidebarProps {
  children: React.ReactNode;
  position: 'left' | 'right';
}

function SidebarWithCollapsiblePanels({ children, position }: SidebarProps) {
  return (
    <div className={`pcb-viewer__sidebar pcb-viewer__sidebar--${position}`}>
      {children}
    </div>
  );
}

// Internal component that uses the context
function PcbViewerInner({
  data,
  diffData,
  busData,
  mode = 'single',
  showLayerPanel = true,
  showNetPanel = true,
  showInspector = true,
  showToolbar = true,
  onElementSelect,
  onElementHover,
  onNetHighlight,
  onViewChange,
  className,
  style,
  width = '100%',
  height = '100%',
}: PcbViewerProps) {
  const { state, dispatch, setBusData } = usePcbViewer();

  // Load PCB data when props change
  useEffect(() => {
    if (diffData) {
      dispatch({
        type: 'SET_DATA',
        payload: { mode: 'diff', diffData }
      });
    } else if (data) {
      dispatch({
        type: 'SET_DATA',
        payload: { mode: 'single', pcbData: data }
      });
    }
  }, [data, diffData, dispatch]);

  // Load bus data when props change
  useEffect(() => {
    if (busData) {
      setBusData(busData);
    }
  }, [busData, setBusData]);

  // Callbacks for external integration
  useEffect(() => {
    if (onElementSelect && state.selectedElement) {
      onElementSelect(state.selectedElement);
    }
  }, [state.selectedElement, onElementSelect]);

  useEffect(() => {
    if (onElementHover) {
      onElementHover(state.hoveredElement);
    }
  }, [state.hoveredElement, onElementHover]);

  useEffect(() => {
    if (onNetHighlight) {
      onNetHighlight(state.highlightedNet);
    }
  }, [state.highlightedNet, onNetHighlight]);

  useEffect(() => {
    if (onViewChange) {
      onViewChange(state.view);
    }
  }, [state.view, onViewChange]);

  const containerStyle: React.CSSProperties = {
    width,
    height,
    ...style,
  };

  const hasData = state.pcbData || state.diffData;
  const hasDiffData = !!state.diffData;

  return (
    <div className={`pcb-viewer ${className || ''}`} style={containerStyle}>
      {showToolbar && (
        <Toolbar
          title={state.pcbData?.filename || state.diffData?.after?.filename}
          showDiffControls={state.mode === 'diff'}
          hasDiffData={hasDiffData}
        />
      )}

      <div className="pcb-viewer__layout">
        {/* Left sidebar: Layers and Nets */}
        {(showLayerPanel || showNetPanel) && hasData && (
          <SidebarWithCollapsiblePanels position="left">
            {showLayerPanel && (
              <CollapsibleSidebarPanel title="Layers" defaultCollapsed={false}>
                <LayerPanel />
              </CollapsibleSidebarPanel>
            )}
            {showNetPanel && (
              <CollapsibleSidebarPanel title="Nets" defaultCollapsed={false}>
                <NetPanel />
              </CollapsibleSidebarPanel>
            )}
            <CollapsibleSidebarPanel title="Opacity" defaultCollapsed={true}>
              <OpacityPanel />
            </CollapsibleSidebarPanel>
          </SidebarWithCollapsiblePanels>
        )}

        {/* Main canvas */}
        <div className="pcb-viewer__main">
          {hasData ? (
            <Canvas />
          ) : (
            <div style={{
              flex: 1,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--pcb-text-muted)',
              flexDirection: 'column',
              gap: '8px',
            }}>
              <div style={{ fontSize: '48px' }}>📋</div>
              <div>No PCB data loaded</div>
            </div>
          )}
        </div>

        {/* Right sidebar: Inspector and Diff Summary */}
        {(showInspector || state.mode === 'diff') && hasData && (
          <SidebarWithCollapsiblePanels position="right">
            {state.mode === 'diff' && (
              <CollapsibleSidebarPanel title="Diff Summary" defaultCollapsed={false}>
                <DiffSummary />
              </CollapsibleSidebarPanel>
            )}
            {showInspector && (
              <CollapsibleSidebarPanel title="Inspector" defaultCollapsed={false}>
                <Inspector />
              </CollapsibleSidebarPanel>
            )}
          </SidebarWithCollapsiblePanels>
        )}
      </div>
    </div>
  );
}

// Export the main component wrapped in provider
export function PcbViewer(props: PcbViewerProps) {
  return (
    <PcbViewerProvider>
      <PcbViewerInner {...props} />
    </PcbViewerProvider>
  );
}

// Also export types for consumers
export type { PcbViewerProps, PcbData, PcbDiffData, BusData, ViewerMode };
