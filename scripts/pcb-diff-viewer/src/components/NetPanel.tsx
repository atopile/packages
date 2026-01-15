/**
 * Net Panel - Dynamic net list from parsed KiCad data
 *
 * All nets are derived from the PCB file's net definitions.
 */

import { useMemo, useState } from 'react';
import { usePcbViewer } from '../context/PcbViewerContext';

export function NetPanel() {
  const { state, highlightNet } = usePcbViewer();
  const [searchTerm, setSearchTerm] = useState('');

  // Get nets from current data
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const nets = data?.nets || {};

  // Count connections per net
  const netCounts = useMemo(() => {
    const counts: Record<number, { segments: number; vias: number; pads: number }> = {};
    if (!data) return counts;

    // Initialize counts for all nets
    for (const netNum of Object.keys(nets)) {
      counts[Number(netNum)] = { segments: 0, vias: 0, pads: 0 };
    }

    // Count segments
    data.elements.segments.forEach(seg => {
      if (counts[seg.net]) {
        counts[seg.net].segments++;
      }
    });

    // Count vias
    data.elements.vias.forEach(via => {
      if (counts[via.net]) {
        counts[via.net].vias++;
      }
    });

    // Count pads
    data.elements.footprints.forEach(fp => {
      fp.pads.forEach(pad => {
        if (pad.net !== null && counts[pad.net]) {
          counts[pad.net].pads++;
        }
      });
    });

    return counts;
  }, [data, nets]);

  // Filter and sort nets
  const filteredNets = useMemo(() => {
    const netList = Object.entries(nets)
      .map(([numStr, info]) => ({
        number: Number(numStr),
        name: info.name,
        counts: netCounts[Number(numStr)] || { segments: 0, vias: 0, pads: 0 },
      }))
      .filter(net => {
        if (net.number === 0) return false; // Skip unconnected net
        if (!searchTerm) return true;
        return net.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          net.number.toString().includes(searchTerm);
      })
      .sort((a, b) => {
        // Sort by name, but power nets first
        const aIsPower = a.name.startsWith('+') || a.name.includes('VCC') || a.name.includes('VDD') || a.name.includes('GND');
        const bIsPower = b.name.startsWith('+') || b.name.includes('VCC') || b.name.includes('VDD') || b.name.includes('GND');
        if (aIsPower && !bIsPower) return -1;
        if (!aIsPower && bIsPower) return 1;
        return a.name.localeCompare(b.name);
      });

    return netList;
  }, [nets, netCounts, searchTerm]);

  // Group nets by category
  const groupedNets = useMemo(() => {
    const groups: { power: typeof filteredNets; signal: typeof filteredNets } = {
      power: [],
      signal: [],
    };

    filteredNets.forEach(net => {
      const isPower = net.name.startsWith('+') ||
        net.name.includes('VCC') ||
        net.name.includes('VDD') ||
        net.name.includes('GND') ||
        net.name.includes('VBUS') ||
        net.name.includes('3V3') ||
        net.name.includes('5V') ||
        net.name.includes('12V');

      if (isPower) {
        groups.power.push(net);
      } else {
        groups.signal.push(net);
      }
    });

    return groups;
  }, [filteredNets]);

  const totalConnections = (counts: typeof netCounts[number]) =>
    counts.segments + counts.vias + counts.pads;

  return (
    <div className="pcb-panel">
      <div className="pcb-panel__header">
        <span>Nets</span>
        {state.highlightedNet !== null && (
          <button
            className="pcb-btn pcb-btn--icon"
            onClick={() => highlightNet(null)}
            title="Clear highlight"
          >
            ✕
          </button>
        )}
      </div>

      <div style={{ padding: '8px' }}>
        <div className="pcb-search">
          <span>🔍</span>
          <input
            type="text"
            className="pcb-search__input"
            placeholder="Filter nets..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="pcb-panel__content">
        {/* Power nets */}
        {groupedNets.power.length > 0 && (
          <div style={{ marginBottom: '12px' }}>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--pcb-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              padding: '4px 8px',
              marginBottom: '4px',
            }}>
              Power ({groupedNets.power.length})
            </div>
            <div className="pcb-net-list">
              {groupedNets.power.map(net => (
                <div
                  key={net.number}
                  className={`pcb-net-item ${state.highlightedNet === net.number ? 'pcb-net-item--highlighted' : ''}`}
                  onClick={() => highlightNet(state.highlightedNet === net.number ? null : net.number)}
                >
                  <span className="pcb-net-item__number">#{net.number}</span>
                  <span className="pcb-net-item__name" title={net.name}>
                    {net.name || `Net ${net.number}`}
                  </span>
                  <span className="pcb-net-item__count">
                    {totalConnections(net.counts)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Signal nets */}
        {groupedNets.signal.length > 0 && (
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--pcb-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              padding: '4px 8px',
              marginBottom: '4px',
            }}>
              Signals ({groupedNets.signal.length})
            </div>
            <div className="pcb-net-list">
              {groupedNets.signal.map(net => (
                <div
                  key={net.number}
                  className={`pcb-net-item ${state.highlightedNet === net.number ? 'pcb-net-item--highlighted' : ''}`}
                  onClick={() => highlightNet(state.highlightedNet === net.number ? null : net.number)}
                >
                  <span className="pcb-net-item__number">#{net.number}</span>
                  <span className="pcb-net-item__name" title={net.name}>
                    {net.name || `Net ${net.number}`}
                  </span>
                  <span className="pcb-net-item__count">
                    {totalConnections(net.counts)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {filteredNets.length === 0 && (
          <div style={{ padding: '16px', textAlign: 'center', color: 'var(--pcb-text-muted)' }}>
            No nets found
          </div>
        )}
      </div>

      <div className="pcb-panel__footer">
        {Object.keys(nets).length - 1} nets total {/* -1 for unconnected net 0 */}
      </div>
    </div>
  );
}
