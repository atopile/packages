/**
 * Toolbar - View controls and mode toggles
 */

import { usePcbViewer } from '../context/PcbViewerContext';

interface ToolbarProps {
  /** Title to show in toolbar */
  title?: string;
  /** Show diff-specific controls */
  showDiffControls?: boolean;
  /** Whether diff data is available (to show mode toggle) */
  hasDiffData?: boolean;
  /** Callback when mode changes */
  onModeChange?: (mode: 'single' | 'diff') => void;
}

export function Toolbar({ title, showDiffControls, hasDiffData, onModeChange }: ToolbarProps) {
  const { state, dispatch, setView } = usePcbViewer();

  // Calculate zoom percentage
  const zoomPercent = Math.round(state.view.zoom * 2); // Rough percentage based on default zoom

  const resetView = () => {
    setView({ zoom: 50, panX: 0, panY: 0 });
  };

  const zoomIn = () => {
    dispatch({ type: 'ZOOM', payload: { delta: 100, centerX: 0, centerY: 0 } });
  };

  const zoomOut = () => {
    dispatch({ type: 'ZOOM', payload: { delta: -100, centerX: 0, centerY: 0 } });
  };

  return (
    <div className="pcb-toolbar">
      {title && (
        <>
          <span style={{ fontWeight: 600 }}>{title}</span>
          <div className="pcb-toolbar__separator" />
        </>
      )}

      {/* Zoom controls */}
      <div className="pcb-toolbar__group">
        <span className="pcb-toolbar__label">Zoom</span>
        <button className="pcb-btn pcb-btn--icon" onClick={zoomOut} title="Zoom out">
          −
        </button>
        <span style={{
          minWidth: '50px',
          textAlign: 'center',
          fontSize: '12px',
          fontFamily: 'var(--pcb-font-mono)',
        }}>
          {zoomPercent}%
        </span>
        <button className="pcb-btn pcb-btn--icon" onClick={zoomIn} title="Zoom in">
          +
        </button>
        <button className="pcb-btn" onClick={resetView} title="Reset view">
          Fit
        </button>
      </div>

      {/* Mode toggle - only show if diff data is available */}
      {hasDiffData && (
        <>
          <div className="pcb-toolbar__separator" />
          <div className="pcb-toolbar__group">
            <span className="pcb-toolbar__label">View</span>
            <button
              className={`pcb-btn ${state.mode === 'single' ? 'pcb-btn--active' : ''}`}
              onClick={() => {
                dispatch({ type: 'SET_MODE', payload: 'single' });
                onModeChange?.('single');
              }}
              title="View PCB normally"
            >
              PCB
            </button>
            <button
              className={`pcb-btn ${state.mode === 'diff' ? 'pcb-btn--active' : ''}`}
              onClick={() => {
                dispatch({ type: 'SET_MODE', payload: 'diff' });
                onModeChange?.('diff');
              }}
              title="View differences between versions"
              style={state.mode === 'diff' ? {
                backgroundColor: 'var(--pcb-diff-modified-after)',
                borderColor: 'var(--pcb-diff-modified-after)',
                color: '#1e1e2e',
              } : {}}
            >
              Diff
            </button>
          </div>
        </>
      )}

      {/* Diff controls */}
      {showDiffControls && state.mode === 'diff' && (
        <>
          <div className="pcb-toolbar__group">
            <span className="pcb-toolbar__label">Show</span>
            <button
              className={`pcb-btn ${state.showBeforeState ? 'pcb-btn--active' : ''}`}
              onClick={() => dispatch({ type: 'TOGGLE_BEFORE_STATE' })}
              title="Toggle before state (removed/modified-before)"
              style={state.showBeforeState ? {
                backgroundColor: 'var(--pcb-diff-modified-before)',
                borderColor: 'var(--pcb-diff-modified-before)',
                color: '#1e1e2e',
              } : {}}
            >
              Before
            </button>
            <button
              className={`pcb-btn ${state.showAfterState ? 'pcb-btn--active' : ''}`}
              onClick={() => dispatch({ type: 'TOGGLE_AFTER_STATE' })}
              title="Toggle after state (added/modified-after)"
              style={state.showAfterState ? {
                backgroundColor: 'var(--pcb-diff-modified-after)',
                borderColor: 'var(--pcb-diff-modified-after)',
                color: '#1e1e2e',
              } : {}}
            >
              After
            </button>
          </div>

          <div className="pcb-toolbar__separator" />
        </>
      )}

      {/* Stats */}
      <div style={{ marginLeft: 'auto', display: 'flex', gap: '16px', fontSize: '12px' }}>
        {state.pcbData && (
          <>
            <span style={{ color: 'var(--pcb-text-muted)' }}>
              <strong>{state.pcbData.elements.footprints.length}</strong> footprints
            </span>
            <span style={{ color: 'var(--pcb-text-muted)' }}>
              <strong>{state.pcbData.elements.segments.length}</strong> traces
            </span>
            <span style={{ color: 'var(--pcb-text-muted)' }}>
              <strong>{state.pcbData.elements.vias.length}</strong> vias
            </span>
          </>
        )}

        {state.diffData && state.mode === 'diff' && (
          <>
            <span style={{ color: 'var(--pcb-diff-added)' }}>
              <strong>
                {state.diffData.diff.footprints.filter(d => d.status === 'added').length +
                 state.diffData.diff.segments.filter(d => d.status === 'added').length +
                 state.diffData.diff.vias.filter(d => d.status === 'added').length}
              </strong> added
            </span>
            <span style={{ color: 'var(--pcb-diff-removed)' }}>
              <strong>
                {state.diffData.diff.footprints.filter(d => d.status === 'removed').length +
                 state.diffData.diff.segments.filter(d => d.status === 'removed').length +
                 state.diffData.diff.vias.filter(d => d.status === 'removed').length}
              </strong> removed
            </span>
            <span style={{ color: 'var(--pcb-diff-modified-after)' }}>
              <strong>
                {state.diffData.diff.footprints.filter(d => d.status === 'modified').length +
                 state.diffData.diff.segments.filter(d => d.status === 'modified').length +
                 state.diffData.diff.vias.filter(d => d.status === 'modified').length}
              </strong> modified
            </span>
          </>
        )}
      </div>
    </div>
  );
}
