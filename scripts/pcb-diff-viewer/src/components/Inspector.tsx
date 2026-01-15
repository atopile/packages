/**
 * Inspector Panel - Shows details of selected/hovered element
 *
 * All information is derived from the parsed KiCad data.
 */

import { useState, useMemo } from 'react';
import { usePcbViewer } from '../context/PcbViewerContext';
import type { Footprint, Segment, Via, Pad } from '../types/pcb';

function formatNumber(n: number, precision: number = 3): string {
  return n.toFixed(precision).replace(/\.?0+$/, '');
}

function FootprintInspector({ fp }: { fp: Footprint }) {
  const { state, highlightNet } = usePcbViewer();
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const [padFilter, setPadFilter] = useState('');
  const [showAllPads, setShowAllPads] = useState(false);

  // Filter pads based on search
  const filteredPads = useMemo(() => {
    if (!padFilter) return fp.pads;
    const lower = padFilter.toLowerCase();
    return fp.pads.filter(pad =>
      pad.name.toLowerCase().includes(lower) ||
      (pad.netName && pad.netName.toLowerCase().includes(lower))
    );
  }, [fp.pads, padFilter]);

  // Get unique nets connected to this footprint
  const connectedNets = useMemo(() => {
    const nets = new Map<number, { name: string; pads: Pad[] }>();
    fp.pads.forEach(pad => {
      if (pad.net !== null && pad.net !== 0) {
        const existing = nets.get(pad.net);
        const netName = pad.netName || data?.nets[pad.net]?.name || `Net ${pad.net}`;
        if (existing) {
          existing.pads.push(pad);
        } else {
          nets.set(pad.net, { name: netName, pads: [pad] });
        }
      }
    });
    return nets;
  }, [fp.pads, data?.nets]);

  const handleNetClick = (netId: number) => {
    highlightNet(state.highlightedNet === netId ? null : netId);
  };

  const padsToShow = showAllPads ? filteredPads : filteredPads.slice(0, 10);
  const hasMorePads = filteredPads.length > 10 && !showAllPads;

  return (
    <>
      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Footprint</div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Reference</span>
          <span className="pcb-inspector__value pcb-inspector__value--highlight">
            {fp.reference || '—'}
          </span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Value</span>
          <span className="pcb-inspector__value">{fp.value || '—'}</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Footprint</span>
          <span className="pcb-inspector__value" style={{ fontSize: '10px' }}>
            {fp.name.split(':').pop() || fp.name}
          </span>
        </div>
      </div>

      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Position</div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">X</span>
          <span className="pcb-inspector__value">{formatNumber(fp.at.x)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Y</span>
          <span className="pcb-inspector__value">{formatNumber(fp.at.y)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Rotation</span>
          <span className="pcb-inspector__value">{formatNumber(fp.at.r)}°</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Layer</span>
          <span className="pcb-inspector__value">{fp.layer}</span>
        </div>
      </div>

      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Pads ({fp.pads.length})</span>
        </div>
        {fp.pads.length > 5 && (
          <input
            type="text"
            placeholder="Filter pads..."
            value={padFilter}
            onChange={(e) => setPadFilter(e.target.value)}
            className="pcb-input"
            style={{ marginBottom: '8px', fontSize: '11px', padding: '4px 8px' }}
          />
        )}
        <div style={{ maxHeight: showAllPads ? '200px' : 'auto', overflowY: showAllPads ? 'auto' : 'visible' }}>
          {padsToShow.map((pad, i) => (
            <div
              key={i}
              className={`pcb-inspector__row ${pad.net ? 'pcb-inspector__row--clickable' : ''} ${state.highlightedNet === pad.net ? 'pcb-inspector__row--active' : ''}`}
              onClick={() => pad.net && handleNetClick(pad.net)}
            >
              <span className="pcb-inspector__label">{pad.name}</span>
              <span
                className="pcb-inspector__value"
                style={{
                  fontSize: '10px',
                  color: state.highlightedNet === pad.net ? 'var(--pcb-highlight)' : undefined
                }}
              >
                {pad.netName || (pad.net ? `Net ${pad.net}` : 'NC')}
              </span>
            </div>
          ))}
        </div>
        {hasMorePads && (
          <button
            onClick={() => setShowAllPads(true)}
            style={{
              fontSize: '10px',
              color: 'var(--pcb-text-muted)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              marginTop: '4px',
              textDecoration: 'underline'
            }}
          >
            Show all {filteredPads.length} pads
          </button>
        )}
        {showAllPads && filteredPads.length > 10 && (
          <button
            onClick={() => setShowAllPads(false)}
            style={{
              fontSize: '10px',
              color: 'var(--pcb-text-muted)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              marginTop: '4px',
              textDecoration: 'underline'
            }}
          >
            Show less
          </button>
        )}
      </div>

      {connectedNets.size > 0 && (
        <div className="pcb-inspector__section">
          <div className="pcb-inspector__title">Connected Nets ({connectedNets.size})</div>
          <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
            {Array.from(connectedNets.entries()).map(([netId, { name, pads }]) => (
              <div
                key={netId}
                className={`pcb-inspector__row pcb-inspector__row--clickable ${state.highlightedNet === netId ? 'pcb-inspector__row--active' : ''}`}
                onClick={() => handleNetClick(netId)}
              >
                <span
                  className="pcb-inspector__value pcb-inspector__value--highlight"
                  style={{
                    color: state.highlightedNet === netId ? 'var(--pcb-highlight)' : undefined
                  }}
                >
                  {name}
                </span>
                <span className="pcb-inspector__label" style={{ fontSize: '9px' }}>
                  ({pads.length} pad{pads.length > 1 ? 's' : ''})
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

function SegmentInspector({ seg }: { seg: Segment }) {
  const { state, highlightNet } = usePcbViewer();
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const netName = data?.nets[seg.net]?.name;

  const length = Math.sqrt(
    Math.pow(seg.end.x - seg.start.x, 2) +
    Math.pow(seg.end.y - seg.start.y, 2)
  );

  const handleNetClick = () => {
    highlightNet(state.highlightedNet === seg.net ? null : seg.net);
  };

  return (
    <>
      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Trace Segment</div>
        <div
          className={`pcb-inspector__row pcb-inspector__row--clickable ${state.highlightedNet === seg.net ? 'pcb-inspector__row--active' : ''}`}
          onClick={handleNetClick}
        >
          <span className="pcb-inspector__label">Net</span>
          <span className="pcb-inspector__value pcb-inspector__value--highlight">
            {netName || `Net ${seg.net}`}
          </span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Layer</span>
          <span className="pcb-inspector__value">{seg.layer}</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Width</span>
          <span className="pcb-inspector__value">{formatNumber(seg.width)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Length</span>
          <span className="pcb-inspector__value">{formatNumber(length)} mm</span>
        </div>
      </div>

      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Start</div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">X</span>
          <span className="pcb-inspector__value">{formatNumber(seg.start.x)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Y</span>
          <span className="pcb-inspector__value">{formatNumber(seg.start.y)} mm</span>
        </div>
      </div>

      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">End</div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">X</span>
          <span className="pcb-inspector__value">{formatNumber(seg.end.x)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Y</span>
          <span className="pcb-inspector__value">{formatNumber(seg.end.y)} mm</span>
        </div>
      </div>
    </>
  );
}

function ViaInspector({ via }: { via: Via }) {
  const { state, highlightNet } = usePcbViewer();
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const netName = data?.nets[via.net]?.name;

  const handleNetClick = () => {
    highlightNet(state.highlightedNet === via.net ? null : via.net);
  };

  return (
    <>
      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Via</div>
        <div
          className={`pcb-inspector__row pcb-inspector__row--clickable ${state.highlightedNet === via.net ? 'pcb-inspector__row--active' : ''}`}
          onClick={handleNetClick}
        >
          <span className="pcb-inspector__label">Net</span>
          <span className="pcb-inspector__value pcb-inspector__value--highlight">
            {netName || `Net ${via.net}`}
          </span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Size</span>
          <span className="pcb-inspector__value">{formatNumber(via.size)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Drill</span>
          <span className="pcb-inspector__value">{formatNumber(via.drill)} mm</span>
        </div>
      </div>

      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Position</div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">X</span>
          <span className="pcb-inspector__value">{formatNumber(via.at.x)} mm</span>
        </div>
        <div className="pcb-inspector__row">
          <span className="pcb-inspector__label">Y</span>
          <span className="pcb-inspector__value">{formatNumber(via.at.y)} mm</span>
        </div>
      </div>

      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Layers</div>
        {via.layers.map((layer, i) => (
          <div key={i} className="pcb-inspector__row">
            <span className="pcb-inspector__value">{layer}</span>
          </div>
        ))}
      </div>
    </>
  );
}

export function Inspector() {
  const { state } = usePcbViewer();

  // Show selected element, or hovered if nothing selected
  const element = state.selectedElement || state.hoveredElement;

  return (
    <div className="pcb-panel">
      <div className="pcb-panel__header">
        <span>Inspector</span>
        {state.selectedElement && (
          <span style={{ fontSize: '10px', color: 'var(--pcb-highlight)' }}>Selected</span>
        )}
      </div>

      <div className="pcb-panel__content pcb-inspector">
        {!element && (
          <div className="pcb-inspector__empty">
            Hover or click an element to inspect
          </div>
        )}

        {element?.type === 'footprint' && (
          <FootprintInspector fp={element as Footprint} />
        )}

        {element?.type === 'segment' && (
          <SegmentInspector seg={element as Segment} />
        )}

        {element?.type === 'via' && (
          <ViaInspector via={element as Via} />
        )}
      </div>
    </div>
  );
}
