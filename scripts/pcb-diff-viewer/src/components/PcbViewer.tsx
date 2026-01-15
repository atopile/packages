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
 */

import { useEffect } from 'react';
import { PcbViewerProvider, usePcbViewer } from '../context/PcbViewerContext';
import { Canvas } from './Canvas';
import { LayerPanel } from './LayerPanel';
import { NetPanel } from './NetPanel';
import { Inspector } from './Inspector';
import { Toolbar } from './Toolbar';
import { DiffSummary } from './DiffSummary';
import type { PcbViewerProps, PcbData, PcbDiffData, ViewerMode } from '../types/pcb';

import '../styles/theme.css';
import '../styles/components.css';

// Internal component that uses the context
function PcbViewerInner({
  data,
  diffData,
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
  const { state, dispatch } = usePcbViewer();

  // Load data when props change
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
          <div className="pcb-viewer__sidebar pcb-viewer__sidebar--left">
            {showLayerPanel && <LayerPanel />}
            {showNetPanel && <NetPanel />}
          </div>
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
          <div className="pcb-viewer__sidebar">
            {state.mode === 'diff' && <DiffSummary />}
            {showInspector && <Inspector />}
          </div>
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
export type { PcbViewerProps, PcbData, PcbDiffData, ViewerMode };
