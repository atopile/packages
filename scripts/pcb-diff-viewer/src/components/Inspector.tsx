/**
 * Inspector Panel - Shows details of selected/hovered element
 *
 * All information is derived from the parsed KiCad data.
 */

import { usePcbViewer } from '../context/PcbViewerContext';
import type { Footprint, Segment, Via, PcbElement } from '../types/pcb';

function formatNumber(n: number, precision: number = 3): string {
  return n.toFixed(precision).replace(/\.?0+$/, '');
}

function FootprintInspector({ fp }: { fp: Footprint }) {
  const { state } = usePcbViewer();
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;

  // Get unique nets connected to this footprint
  const connectedNets = new Set<number>();
  fp.pads.forEach(pad => {
    if (pad.net !== null) connectedNets.add(pad.net);
  });

  // Get net names
  const netNames = Array.from(connectedNets)
    .filter(n => n !== 0) // Exclude unconnected
    .map(n => data?.nets[n]?.name || `Net ${n}`)
    .slice(0, 5); // Limit display

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
        <div className="pcb-inspector__title">Pads ({fp.pads.length})</div>
        {fp.pads.slice(0, 8).map((pad, i) => (
          <div key={i} className="pcb-inspector__row">
            <span className="pcb-inspector__label">{pad.name}</span>
            <span className="pcb-inspector__value" style={{ fontSize: '10px' }}>
              {pad.netName || (pad.net ? `Net ${pad.net}` : 'NC')}
            </span>
          </div>
        ))}
        {fp.pads.length > 8 && (
          <div style={{ fontSize: '10px', color: 'var(--pcb-text-muted)', marginTop: '4px' }}>
            +{fp.pads.length - 8} more pads
          </div>
        )}
      </div>

      {netNames.length > 0 && (
        <div className="pcb-inspector__section">
          <div className="pcb-inspector__title">Connected Nets</div>
          {netNames.map((name, i) => (
            <div key={i} className="pcb-inspector__row">
              <span className="pcb-inspector__value pcb-inspector__value--highlight">
                {name}
              </span>
            </div>
          ))}
          {connectedNets.size > 5 && (
            <div style={{ fontSize: '10px', color: 'var(--pcb-text-muted)', marginTop: '4px' }}>
              +{connectedNets.size - 5} more nets
            </div>
          )}
        </div>
      )}
    </>
  );
}

function SegmentInspector({ seg }: { seg: Segment }) {
  const { state } = usePcbViewer();
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const netName = data?.nets[seg.net]?.name;

  const length = Math.sqrt(
    Math.pow(seg.end.x - seg.start.x, 2) +
    Math.pow(seg.end.y - seg.start.y, 2)
  );

  return (
    <>
      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Trace Segment</div>
        <div className="pcb-inspector__row">
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
  const { state } = usePcbViewer();
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const netName = data?.nets[via.net]?.name;

  return (
    <>
      <div className="pcb-inspector__section">
        <div className="pcb-inspector__title">Via</div>
        <div className="pcb-inspector__row">
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
