/**
 * Diff Summary - Shows overview of changes when in diff mode
 */

import { usePcbViewer } from '../context/PcbViewerContext';

export function DiffSummary() {
  const { state } = usePcbViewer();

  if (state.mode !== 'diff' || !state.diffData) {
    return null;
  }

  const { diff } = state.diffData;

  // Count by status
  const counts = {
    added: {
      footprints: diff.footprints.filter(d => d.status === 'added').length,
      segments: diff.segments.filter(d => d.status === 'added').length,
      vias: diff.vias.filter(d => d.status === 'added').length,
    },
    removed: {
      footprints: diff.footprints.filter(d => d.status === 'removed').length,
      segments: diff.segments.filter(d => d.status === 'removed').length,
      vias: diff.vias.filter(d => d.status === 'removed').length,
    },
    modified: {
      footprints: diff.footprints.filter(d => d.status === 'modified').length,
      segments: diff.segments.filter(d => d.status === 'modified').length,
      vias: diff.vias.filter(d => d.status === 'modified').length,
    },
    unchanged: {
      footprints: diff.footprints.filter(d => d.status === 'unchanged').length,
      segments: diff.segments.filter(d => d.status === 'unchanged').length,
      vias: diff.vias.filter(d => d.status === 'unchanged').length,
    },
  };

  const totalAdded = counts.added.footprints + counts.added.segments + counts.added.vias;
  const totalRemoved = counts.removed.footprints + counts.removed.segments + counts.removed.vias;
  const totalModified = counts.modified.footprints + counts.modified.segments + counts.modified.vias;
  const totalUnchanged = counts.unchanged.footprints + counts.unchanged.segments + counts.unchanged.vias;

  const hasChanges = totalAdded > 0 || totalRemoved > 0 || totalModified > 0;

  return (
    <div className="pcb-panel">
      <div className="pcb-panel__header">
        <span>Diff Summary</span>
      </div>

      <div className="pcb-panel__content">
        {!hasChanges ? (
          <div style={{
            padding: '16px',
            textAlign: 'center',
            color: 'var(--pcb-text-muted)',
            fontStyle: 'italic',
          }}>
            No changes detected
          </div>
        ) : (
          <>
            <div className="pcb-diff-summary">
              <div className="pcb-diff-stat">
                <div className="pcb-diff-stat__dot pcb-diff-stat__dot--added" />
                <span>{totalAdded} added</span>
              </div>
              <div className="pcb-diff-stat">
                <div className="pcb-diff-stat__dot pcb-diff-stat__dot--removed" />
                <span>{totalRemoved} removed</span>
              </div>
              <div className="pcb-diff-stat">
                <div className="pcb-diff-stat__dot pcb-diff-stat__dot--modified" />
                <span>{totalModified} modified</span>
              </div>
              <div className="pcb-diff-stat">
                <div className="pcb-diff-stat__dot pcb-diff-stat__dot--unchanged" />
                <span>{totalUnchanged} unchanged</span>
              </div>
            </div>

            {/* Detailed breakdown */}
            <div style={{ fontSize: '12px' }}>
              <div style={{
                fontWeight: 600,
                marginBottom: '8px',
                color: 'var(--pcb-text-muted)',
                textTransform: 'uppercase',
                fontSize: '11px',
                letterSpacing: '0.5px',
              }}>
                By Element Type
              </div>

              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ color: 'var(--pcb-text-muted)', fontSize: '10px' }}>
                    <th style={{ textAlign: 'left', padding: '4px 0' }}>Type</th>
                    <th style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-diff-added)' }}>+</th>
                    <th style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-diff-removed)' }}>−</th>
                    <th style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-diff-modified-after)' }}>~</th>
                    <th style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-diff-unchanged)' }}>=</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '4px 0' }}>Footprints</td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.added.footprints > 0 ? 'var(--pcb-diff-added)' : 'var(--pcb-text-muted)' }}>
                      {counts.added.footprints}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.removed.footprints > 0 ? 'var(--pcb-diff-removed)' : 'var(--pcb-text-muted)' }}>
                      {counts.removed.footprints}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.modified.footprints > 0 ? 'var(--pcb-diff-modified-after)' : 'var(--pcb-text-muted)' }}>
                      {counts.modified.footprints}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-text-muted)' }}>
                      {counts.unchanged.footprints}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '4px 0' }}>Traces</td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.added.segments > 0 ? 'var(--pcb-diff-added)' : 'var(--pcb-text-muted)' }}>
                      {counts.added.segments}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.removed.segments > 0 ? 'var(--pcb-diff-removed)' : 'var(--pcb-text-muted)' }}>
                      {counts.removed.segments}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.modified.segments > 0 ? 'var(--pcb-diff-modified-after)' : 'var(--pcb-text-muted)' }}>
                      {counts.modified.segments}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-text-muted)' }}>
                      {counts.unchanged.segments}
                    </td>
                  </tr>
                  <tr>
                    <td style={{ padding: '4px 0' }}>Vias</td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.added.vias > 0 ? 'var(--pcb-diff-added)' : 'var(--pcb-text-muted)' }}>
                      {counts.added.vias}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.removed.vias > 0 ? 'var(--pcb-diff-removed)' : 'var(--pcb-text-muted)' }}>
                      {counts.removed.vias}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: counts.modified.vias > 0 ? 'var(--pcb-diff-modified-after)' : 'var(--pcb-text-muted)' }}>
                      {counts.modified.vias}
                    </td>
                    <td style={{ textAlign: 'right', padding: '4px', color: 'var(--pcb-text-muted)' }}>
                      {counts.unchanged.vias}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
