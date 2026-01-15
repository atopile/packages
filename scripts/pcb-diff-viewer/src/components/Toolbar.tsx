/**
 * Toolbar - atopile branded floating toolbar
 */

import { usePcbViewer, type ColorMode } from '../context/PcbViewerContext';

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
  const { state, dispatch, setView, setSelectionFilter, setColorMode } = usePcbViewer();

  // Calculate zoom percentage
  const zoomPercent = Math.round(state.view.zoom * 2);

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
      {/* File title with badge */}
      {title && (
        <div className="pcb-file-title">
          {title}
        </div>
      )}

      {/* Zoom controls */}
      <div className="pcb-toolbar__group">
        <span className="pcb-toolbar__label">Zoom</span>
        <button className="pcb-btn pcb-btn--icon" onClick={zoomOut} title="Zoom out">
          −
        </button>
        <span style={{
          minWidth: '48px',
          textAlign: 'center',
          fontSize: '12px',
          fontFamily: 'var(--pcb-font-mono)',
          fontWeight: 600,
          color: 'var(--pcb-text)',
        }}>
          {zoomPercent}%
        </span>
        <button className="pcb-btn pcb-btn--icon" onClick={zoomIn} title="Zoom in">
          +
        </button>
        <button
          className="pcb-btn"
          onClick={resetView}
          title="Fit to view"
        >
          Fit
        </button>
      </div>

      {/* Selection filter */}
      <div className="pcb-toolbar__group">
        <span className="pcb-toolbar__label">Select</span>
        <button
          className={`pcb-btn pcb-btn--sm ${state.selectionFilter.footprints ? 'pcb-btn--active' : ''}`}
          onClick={() => setSelectionFilter({ footprints: !state.selectionFilter.footprints })}
          title="Toggle footprint selection"
        >
          ⬜
        </button>
        <button
          className={`pcb-btn pcb-btn--sm ${state.selectionFilter.segments ? 'pcb-btn--active' : ''}`}
          onClick={() => setSelectionFilter({ segments: !state.selectionFilter.segments })}
          title="Toggle trace selection"
        >
          ╱
        </button>
        <button
          className={`pcb-btn pcb-btn--sm ${state.selectionFilter.vias ? 'pcb-btn--active' : ''}`}
          onClick={() => setSelectionFilter({ vias: !state.selectionFilter.vias })}
          title="Toggle via selection"
        >
          ◉
        </button>
      </div>

      {/* Color mode toggle */}
      <div className="pcb-toolbar__group">
        <span className="pcb-toolbar__label">Color</span>
        <button
          className={`pcb-btn ${state.colorMode === 'layer' ? 'pcb-btn--active' : ''}`}
          onClick={() => setColorMode('layer')}
          title="Color by layer"
        >
          Layer
        </button>
        <button
          className={`pcb-btn ${state.colorMode === 'net' ? 'pcb-btn--active' : ''}`}
          onClick={() => setColorMode('net')}
          title="Color by net"
          style={state.colorMode === 'net' ? {
            background: 'linear-gradient(135deg, #f38ba8, #fab387, #f9e2af, #a6e3a1, #89b4fa, #cba6f7)',
            color: '#1e1e2e',
            border: 'none',
          } : {}}
        >
          Net
        </button>
      </div>

      {/* Mode toggle - only show if diff data is available */}
      {hasDiffData && (
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
            title="View differences"
            style={state.mode === 'diff' ? {
              background: 'var(--pcb-diff-modified-after)',
              borderColor: 'var(--pcb-diff-modified-after)',
            } : {}}
          >
            Diff
          </button>
        </div>
      )}

      {/* Diff controls */}
      {showDiffControls && state.mode === 'diff' && (
        <div className="pcb-toolbar__group">
          <span className="pcb-toolbar__label">Show</span>
          <button
            className={`pcb-btn ${state.showBeforeState ? 'pcb-btn--active' : ''}`}
            onClick={() => dispatch({ type: 'TOGGLE_BEFORE_STATE' })}
            title="Toggle before state"
            style={state.showBeforeState ? {
              background: 'var(--pcb-diff-modified-before)',
              borderColor: 'var(--pcb-diff-modified-before)',
            } : {}}
          >
            Before
          </button>
          <button
            className={`pcb-btn ${state.showAfterState ? 'pcb-btn--active' : ''}`}
            onClick={() => dispatch({ type: 'TOGGLE_AFTER_STATE' })}
            title="Toggle after state"
            style={state.showAfterState ? {
              background: 'var(--pcb-diff-modified-after)',
              borderColor: 'var(--pcb-diff-modified-after)',
            } : {}}
          >
            After
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="pcb-stats">
        {state.pcbData && (
          <>
            <div className="pcb-stats__item">
              <span className="pcb-stats__value">{state.pcbData.elements.footprints.length}</span>
              <span>footprints</span>
            </div>
            <div className="pcb-stats__item">
              <span className="pcb-stats__value">{state.pcbData.elements.segments.length}</span>
              <span>traces</span>
            </div>
            <div className="pcb-stats__item">
              <span className="pcb-stats__value">{state.pcbData.elements.vias.length}</span>
              <span>vias</span>
            </div>
          </>
        )}

        {state.diffData && state.mode === 'diff' && (
          <>
            <div className="pcb-stats__item pcb-stats__item--added">
              <span className="pcb-stats__value">
                {state.diffData.diff.footprints.filter(d => d.status === 'added').length +
                 state.diffData.diff.segments.filter(d => d.status === 'added').length +
                 state.diffData.diff.vias.filter(d => d.status === 'added').length}
              </span>
              <span>added</span>
            </div>
            <div className="pcb-stats__item pcb-stats__item--removed">
              <span className="pcb-stats__value">
                {state.diffData.diff.footprints.filter(d => d.status === 'removed').length +
                 state.diffData.diff.segments.filter(d => d.status === 'removed').length +
                 state.diffData.diff.vias.filter(d => d.status === 'removed').length}
              </span>
              <span>removed</span>
            </div>
            <div className="pcb-stats__item pcb-stats__item--modified">
              <span className="pcb-stats__value">
                {state.diffData.diff.footprints.filter(d => d.status === 'modified').length +
                 state.diffData.diff.segments.filter(d => d.status === 'modified').length +
                 state.diffData.diff.vias.filter(d => d.status === 'modified').length}
              </span>
              <span>modified</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
