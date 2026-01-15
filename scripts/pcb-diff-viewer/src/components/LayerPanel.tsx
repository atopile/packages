/**
 * Layer Panel - Dynamic layer list from parsed KiCad data
 *
 * All layers are derived from the PCB file's layer definitions.
 * Colors are generated dynamically based on layer properties.
 */

import { useMemo, useState } from 'react';
import { usePcbViewer } from '../context/PcbViewerContext';
import type { LayerInfo } from '../types/pcb';

interface LayerPanelProps {
  /** Custom layer color map (optional - will generate if not provided) */
  layerColors?: Map<string, string>;
}

/**
 * Generate a color for a layer based on its properties
 */
function getLayerColor(layer: LayerInfo, layerName: string): string {
  const isFront = layerName.startsWith('F.');
  const isBack = layerName.startsWith('B.');
  const isInner = layerName.startsWith('In');
  const isSilkscreen = layerName.includes('SilkS');
  const isMask = layerName.includes('Mask');
  const isCopper = layer.type === 'signal' || layer.type === 'power' || layer.type === 'mixed' || layerName.endsWith('.Cu');

  let hue: number;
  let saturation = 70;
  let lightness = 60;

  if (isCopper) {
    if (isFront) hue = 350;
    else if (isBack) hue = 210;
    else if (isInner) hue = 90 + (layer.number % 10) * 20;
    else hue = 30;
  } else if (isSilkscreen) {
    hue = isFront ? 45 : 260;
    saturation = 40;
    lightness = 85;
  } else if (isMask) {
    hue = isFront ? 120 : 240;
    saturation = 30;
    lightness = 50;
  } else if (layerName.includes('Edge')) {
    hue = 0;
    saturation = 0;
    lightness = 90;
  } else {
    hue = (layer.number * 37) % 360;
    saturation = 50;
    lightness = 55;
  }

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Group layers by category for better organization
 */
function categorizeLayer(layerName: string): string {
  if (layerName.endsWith('.Cu')) return 'Copper';
  if (layerName.includes('SilkS')) return 'Silkscreen';
  if (layerName.includes('Mask')) return 'Solder Mask';
  if (layerName.includes('Paste')) return 'Paste';
  if (layerName.includes('Courtyard')) return 'Courtyard';
  if (layerName.includes('Fab')) return 'Fabrication';
  if (layerName.includes('Adhes')) return 'Adhesive';
  if (layerName.includes('Edge')) return 'Board';
  if (layerName.includes('Margin')) return 'Board';
  return 'User';
}

export function LayerPanel({ layerColors }: LayerPanelProps) {
  const { state, setLayerVisible, toggleAllLayers } = usePcbViewer();
  const [searchTerm, setSearchTerm] = useState('');
  const [collapsedCategories, setCollapsedCategories] = useState<Set<string>>(new Set());

  // Get layers from current data
  const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
  const layers = data?.layers || {};

  // Count elements per layer
  const layerCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    if (!data) return counts;

    // Count footprints
    data.elements.footprints.forEach(fp => {
      counts[fp.layer] = (counts[fp.layer] || 0) + 1;
    });

    // Count segments
    data.elements.segments.forEach(seg => {
      counts[seg.layer] = (counts[seg.layer] || 0) + 1;
    });

    // Count graphic lines
    data.elements.graphicLines.forEach(line => {
      counts[line.layer] = (counts[line.layer] || 0) + 1;
    });

    return counts;
  }, [data]);

  // Group and filter layers
  const groupedLayers = useMemo(() => {
    const groups: Record<string, Array<{ name: string; info: LayerInfo }>> = {};

    for (const [name, info] of Object.entries(layers)) {
      // Filter by search
      if (searchTerm && !name.toLowerCase().includes(searchTerm.toLowerCase())) {
        continue;
      }

      const category = categorizeLayer(name);
      if (!groups[category]) {
        groups[category] = [];
      }
      groups[category].push({ name, info });
    }

    // Sort layers within each group by layer number
    for (const category of Object.keys(groups)) {
      groups[category].sort((a, b) => a.info.number - b.info.number);
    }

    return groups;
  }, [layers, searchTerm]);

  // Category order for consistent display
  const categoryOrder = ['Copper', 'Silkscreen', 'Solder Mask', 'Paste', 'Board', 'Courtyard', 'Fabrication', 'Adhesive', 'User'];
  const sortedCategories = Object.keys(groupedLayers).sort(
    (a, b) => categoryOrder.indexOf(a) - categoryOrder.indexOf(b)
  );

  const toggleCategory = (category: string) => {
    setCollapsedCategories(prev => {
      const next = new Set(prev);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  };

  // Check if all/none visible
  const allVisible = Object.keys(state.layerVisibility).every(l => state.layerVisibility[l] !== false);
  const noneVisible = Object.keys(state.layerVisibility).every(l => state.layerVisibility[l] === false);

  return (
    <div className="pcb-panel">
      <div className="pcb-panel__header">
        <span>Layers</span>
        <div style={{ display: 'flex', gap: '4px' }}>
          <button
            className={`pcb-btn pcb-btn--icon ${allVisible ? 'pcb-btn--active' : ''}`}
            onClick={() => toggleAllLayers(true)}
            title="Show all"
          >
            👁
          </button>
          <button
            className={`pcb-btn pcb-btn--icon ${noneVisible ? 'pcb-btn--active' : ''}`}
            onClick={() => toggleAllLayers(false)}
            title="Hide all"
          >
            ◯
          </button>
        </div>
      </div>

      <div style={{ padding: '8px' }}>
        <div className="pcb-search">
          <span>🔍</span>
          <input
            type="text"
            className="pcb-search__input"
            placeholder="Filter layers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <div className="pcb-panel__content">
        {sortedCategories.map(category => (
          <div key={category} style={{ marginBottom: '8px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                cursor: 'pointer',
                padding: '4px 8px',
                borderRadius: '4px',
                fontSize: '11px',
                fontWeight: 600,
                color: 'var(--pcb-text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
              onClick={() => toggleCategory(category)}
            >
              <span style={{ transform: collapsedCategories.has(category) ? 'rotate(-90deg)' : 'rotate(0deg)', transition: '0.15s' }}>
                ▼
              </span>
              {category}
              <span style={{ marginLeft: 'auto', fontWeight: 400 }}>
                ({groupedLayers[category].length})
              </span>
            </div>

            {!collapsedCategories.has(category) && (
              <div className="pcb-layer-list">
                {groupedLayers[category].map(({ name, info }) => {
                  const isVisible = state.layerVisibility[name] !== false;
                  const count = layerCounts[name] || 0;
                  const color = layerColors?.get(name) || getLayerColor(info, name);

                  return (
                    <div
                      key={name}
                      className={`pcb-layer-item ${!isVisible ? 'pcb-layer-item--hidden' : ''}`}
                      onClick={() => setLayerVisible(name, !isVisible)}
                    >
                      <div
                        className="pcb-layer-item__color"
                        style={{ backgroundColor: color }}
                      />
                      <span className="pcb-layer-item__name" title={name}>
                        {name}
                      </span>
                      {count > 0 && (
                        <span className="pcb-layer-item__count">{count}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}

        {sortedCategories.length === 0 && (
          <div style={{ padding: '16px', textAlign: 'center', color: 'var(--pcb-text-muted)' }}>
            No layers found
          </div>
        )}
      </div>

      <div className="pcb-panel__footer">
        {Object.keys(layers).length} layers total
      </div>
    </div>
  );
}
