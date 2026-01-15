/**
 * Net Panel - Dynamic net list from parsed KiCad data
 *
 * When bus data is available from atopile, nets are grouped by their
 * bus/interface type (I2C, SPI, ElectricPower, etc.)
 */

import { useMemo, useState } from 'react';
import { usePcbViewer } from '../context/PcbViewerContext';
import type { BusInfo, BusType } from '../types/pcb';

// Bus type display order and icons
const BUS_TYPE_CONFIG: Record<BusType | string, { icon: string; order: number }> = {
  ElectricPower: { icon: '⚡', order: 0 },
  I2C: { icon: '🔌', order: 1 },
  SPI: { icon: '📡', order: 2 },
  I2S: { icon: '🎵', order: 3 },
  UART: { icon: '📝', order: 4 },
  USB: { icon: '🔗', order: 5 },
  CAN: { icon: '🚗', order: 6 },
  Ethernet: { icon: '🌐', order: 7 },
  DifferentialPair: { icon: '↔️', order: 8 },
  ElectricLogic: { icon: '🔲', order: 9 },
  ElectricSignal: { icon: '📶', order: 10 },
  Unknown: { icon: '❓', order: 99 },
};

export function NetPanel() {
  const { state, highlightNet, highlightBus } = usePcbViewer();
  const [searchTerm, setSearchTerm] = useState('');
  const [collapsedBuses, setCollapsedBuses] = useState<Set<string>>(new Set());

  // Get nets from current data
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const nets = data?.nets || {};
  const busData = state.busData;

  // Count connections per net
  const netCounts = useMemo(() => {
    const counts: Record<number, { segments: number; vias: number; pads: number }> = {};
    if (!data) return counts;

    for (const netNum of Object.keys(nets)) {
      counts[Number(netNum)] = { segments: 0, vias: 0, pads: 0 };
    }

    data.elements.segments.forEach(seg => {
      if (counts[seg.net]) counts[seg.net].segments++;
    });

    data.elements.vias.forEach(via => {
      if (counts[via.net]) counts[via.net].vias++;
    });

    data.elements.footprints.forEach(fp => {
      fp.pads.forEach(pad => {
        if (pad.net !== null && counts[pad.net]) counts[pad.net].pads++;
      });
    });

    return counts;
  }, [data, nets]);

  // Build net name to number mapping
  const netNameToNumber = useMemo(() => {
    const mapping: Record<string, number> = {};
    Object.entries(nets).forEach(([numStr, info]) => {
      mapping[info.name] = Number(numStr);
    });
    return mapping;
  }, [nets]);

  // Group nets by bus when bus data is available
  const groupedByBus = useMemo(() => {
    if (!busData) return null;

    const groups: Record<string, {
      bus: BusInfo;
      nets: Array<{ number: number; name: string; counts: { segments: number; vias: number; pads: number } }>;
    }> = {};

    const unmappedNets: Array<{ number: number; name: string; counts: { segments: number; vias: number; pads: number } }> = [];
    const mappedNetNames = new Set<string>();

    // Group nets by their bus
    Object.entries(busData.buses).forEach(([busId, bus]) => {
      groups[busId] = { bus, nets: [] };

      bus.nets.forEach(netInfo => {
        const netNumber = netNameToNumber[netInfo.name];
        if (netNumber !== undefined) {
          mappedNetNames.add(netInfo.name);
          const counts = netCounts[netNumber] || { segments: 0, vias: 0, pads: 0 };
          groups[busId].nets.push({
            number: netNumber,
            name: netInfo.name,
            counts,
          });
        }
      });
    });

    // Collect unmapped nets
    Object.entries(nets).forEach(([numStr, info]) => {
      const num = Number(numStr);
      if (num === 0) return; // Skip unconnected
      if (!mappedNetNames.has(info.name)) {
        unmappedNets.push({
          number: num,
          name: info.name,
          counts: netCounts[num] || { segments: 0, vias: 0, pads: 0 },
        });
      }
    });

    return { groups, unmappedNets };
  }, [busData, nets, netCounts, netNameToNumber]);

  // Sort and filter bus groups
  const sortedBusGroups = useMemo(() => {
    if (!groupedByBus) return [];

    return Object.entries(groupedByBus.groups)
      .filter(([, group]) => group.nets.length > 0)
      .filter(([busId, group]) => {
        if (!searchTerm) return true;
        const term = searchTerm.toLowerCase();
        return busId.toLowerCase().includes(term) ||
          group.bus.type.toLowerCase().includes(term) ||
          group.nets.some(n => n.name.toLowerCase().includes(term));
      })
      .sort((a, b) => {
        const orderA = BUS_TYPE_CONFIG[a[1].bus.type]?.order ?? 50;
        const orderB = BUS_TYPE_CONFIG[b[1].bus.type]?.order ?? 50;
        if (orderA !== orderB) return orderA - orderB;
        return a[0].localeCompare(b[0]);
      });
  }, [groupedByBus, searchTerm]);

  // Filter unmapped nets
  const filteredUnmappedNets = useMemo(() => {
    if (!groupedByBus) return [];
    if (!searchTerm) return groupedByBus.unmappedNets;
    const term = searchTerm.toLowerCase();
    return groupedByBus.unmappedNets.filter(n =>
      n.name.toLowerCase().includes(term) || n.number.toString().includes(term)
    );
  }, [groupedByBus, searchTerm]);

  // Fallback: old-style grouping when no bus data
  const legacyGroupedNets = useMemo(() => {
    if (groupedByBus) return null;

    const netList = Object.entries(nets)
      .map(([numStr, info]) => ({
        number: Number(numStr),
        name: info.name,
        counts: netCounts[Number(numStr)] || { segments: 0, vias: 0, pads: 0 },
      }))
      .filter(net => {
        if (net.number === 0) return false;
        if (!searchTerm) return true;
        return net.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          net.number.toString().includes(searchTerm);
      })
      .sort((a, b) => a.name.localeCompare(b.name));

    const groups = { power: [] as typeof netList, signal: [] as typeof netList };
    netList.forEach(net => {
      const isPower = /\+|VCC|VDD|GND|VBUS|3V3|5V|12V/i.test(net.name);
      groups[isPower ? 'power' : 'signal'].push(net);
    });

    return groups;
  }, [nets, netCounts, searchTerm, groupedByBus]);

  const totalConnections = (counts: { segments: number; vias: number; pads: number }) =>
    counts.segments + counts.vias + counts.pads;

  const toggleBusCollapse = (busId: string) => {
    setCollapsedBuses(prev => {
      const next = new Set(prev);
      if (next.has(busId)) next.delete(busId);
      else next.add(busId);
      return next;
    });
  };

  const handleBusClick = (busId: string) => {
    highlightBus(state.highlightedBus === busId ? null : busId);
  };

  const handleNetClick = (netNumber: number) => {
    highlightNet(state.highlightedNet === netNumber ? null : netNumber);
  };

  // Check if a net belongs to the highlighted bus
  const isNetInHighlightedBus = (netName: string) => {
    if (!state.highlightedBus || !busData) return false;
    const bus = busData.buses[state.highlightedBus];
    return bus?.nets.some(n => n.name === netName);
  };

  return (
    <div className="pcb-panel">
      <div className="pcb-panel__header">
        <span>Nets</span>
        {(state.highlightedNet !== null || state.highlightedBus !== null) && (
          <button
            className="pcb-btn pcb-btn--icon"
            onClick={() => {
              highlightNet(null);
              highlightBus(null);
            }}
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
        {/* Bus-based grouping (when bus data available) */}
        {groupedByBus && sortedBusGroups.map(([busId, group]) => {
          const isCollapsed = collapsedBuses.has(busId);
          const config = BUS_TYPE_CONFIG[group.bus.type] || BUS_TYPE_CONFIG.Unknown;
          const isHighlighted = state.highlightedBus === busId;

          return (
            <div key={busId} className="pcb-bus-group" style={{ marginBottom: '8px' }}>
              <div
                className={`pcb-bus-group__header ${isHighlighted ? 'pcb-bus-group__header--highlighted' : ''}`}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  padding: '6px 8px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  background: isHighlighted ? `${group.bus.color}22` : 'var(--pcb-surface-1)',
                  border: `1px solid ${isHighlighted ? group.bus.color : 'transparent'}`,
                  transition: 'all 0.15s ease',
                }}
                onClick={() => handleBusClick(busId)}
              >
                <span
                  onClick={(e) => { e.stopPropagation(); toggleBusCollapse(busId); }}
                  style={{ cursor: 'pointer', fontSize: '10px', opacity: 0.7 }}
                >
                  {isCollapsed ? '▶' : '▼'}
                </span>
                <span
                  style={{
                    width: '10px',
                    height: '10px',
                    borderRadius: '50%',
                    background: group.bus.color,
                    flexShrink: 0,
                  }}
                />
                <span style={{ fontSize: '11px' }}>{config.icon}</span>
                <span style={{
                  flex: 1,
                  fontSize: '12px',
                  fontWeight: 500,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {group.bus.instance}
                </span>
                <span style={{
                  fontSize: '10px',
                  color: 'var(--pcb-text-muted)',
                  background: 'var(--pcb-surface-2)',
                  padding: '2px 6px',
                  borderRadius: '10px',
                }}>
                  {group.nets.length}
                </span>
              </div>

              {!isCollapsed && (
                <div className="pcb-net-list" style={{ marginLeft: '16px', marginTop: '4px' }}>
                  {group.nets.map(net => (
                    <div
                      key={net.number}
                      className={`pcb-net-item ${state.highlightedNet === net.number || isNetInHighlightedBus(net.name) ? 'pcb-net-item--highlighted' : ''}`}
                      onClick={() => handleNetClick(net.number)}
                      style={{
                        borderLeft: `2px solid ${group.bus.color}`,
                        marginLeft: '4px',
                        paddingLeft: '8px',
                      }}
                    >
                      <span className="pcb-net-item__name" title={net.name}>
                        {net.name}
                      </span>
                      <span className="pcb-net-item__count">
                        {totalConnections(net.counts)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Unmapped nets (when bus data available) */}
        {groupedByBus && filteredUnmappedNets.length > 0 && (
          <div style={{ marginTop: '12px' }}>
            <div style={{
              fontSize: '11px',
              fontWeight: 600,
              color: 'var(--pcb-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              padding: '4px 8px',
              marginBottom: '4px',
            }}>
              Other ({filteredUnmappedNets.length})
            </div>
            <div className="pcb-net-list">
              {filteredUnmappedNets.map(net => (
                <div
                  key={net.number}
                  className={`pcb-net-item ${state.highlightedNet === net.number ? 'pcb-net-item--highlighted' : ''}`}
                  onClick={() => handleNetClick(net.number)}
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

        {/* Legacy grouping (when no bus data) */}
        {legacyGroupedNets && (
          <>
            {legacyGroupedNets.power.length > 0 && (
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
                  Power ({legacyGroupedNets.power.length})
                </div>
                <div className="pcb-net-list">
                  {legacyGroupedNets.power.map(net => (
                    <div
                      key={net.number}
                      className={`pcb-net-item ${state.highlightedNet === net.number ? 'pcb-net-item--highlighted' : ''}`}
                      onClick={() => handleNetClick(net.number)}
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

            {legacyGroupedNets.signal.length > 0 && (
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
                  Signals ({legacyGroupedNets.signal.length})
                </div>
                <div className="pcb-net-list">
                  {legacyGroupedNets.signal.map(net => (
                    <div
                      key={net.number}
                      className={`pcb-net-item ${state.highlightedNet === net.number ? 'pcb-net-item--highlighted' : ''}`}
                      onClick={() => handleNetClick(net.number)}
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
          </>
        )}

        {(sortedBusGroups.length === 0 && filteredUnmappedNets.length === 0 && !legacyGroupedNets) && (
          <div style={{ padding: '16px', textAlign: 'center', color: 'var(--pcb-text-muted)' }}>
            No nets found
          </div>
        )}
      </div>

      <div className="pcb-panel__footer">
        {busData ? (
          <span>{Object.keys(busData.buses).length} buses • {Object.keys(nets).length - 1} nets</span>
        ) : (
          <span>{Object.keys(nets).length - 1} nets total</span>
        )}
      </div>
    </div>
  );
}
