/**
 * Canvas Renderer Hook - Handles all PCB rendering logic
 *
 * All layer/color information is derived dynamically from the parsed KiCad data.
 * No hardcoded layer names or colors.
 */

import { useRef, useEffect, useCallback } from 'react';
import { usePcbViewer } from '../context/PcbViewerContext';
import type {
  PcbElement,
  Footprint,
  Segment,
  Via,
  GraphicLine,
  Arc,
  Point,
  PcbData,
  LayerInfo,
  DiffStatus
} from '../types/pcb';

// ============================================================================
// Dynamic Color Generation
// ============================================================================

/**
 * Generate a color for a layer based on its properties from KiCad.
 * Layer types from KiCad: signal, power, mixed, user, jumper
 */
function generateLayerColor(layer: LayerInfo, layerName: string): string {
  // Use layer number to generate distinct colors via HSL
  // Copper layers (signal/power/mixed) get warm colors
  // User layers get cool colors

  const isFront = layerName.startsWith('F.');
  const isBack = layerName.startsWith('B.');
  const isInner = layerName.startsWith('In');
  const isSilkscreen = layerName.includes('SilkS');
  const isMask = layerName.includes('Mask');
  const isPaste = layerName.includes('Paste');
  const isCourtyard = layerName.includes('Courtyard');
  const isFab = layerName.includes('Fab');
  const isEdge = layerName.includes('Edge');
  const isCopper = layer.type === 'signal' || layer.type === 'power' || layer.type === 'mixed' || layerName.endsWith('.Cu');

  // Base hue based on layer category
  let hue: number;
  let saturation = 70;
  let lightness = 60;
  let alpha = 1;

  if (isCopper) {
    // Copper layers: red/pink for front, blue for back, green for inner
    if (isFront) {
      hue = 350; // Pink/red
    } else if (isBack) {
      hue = 210; // Blue
    } else if (isInner) {
      // Spread inner layers across green-yellow range
      hue = 90 + (layer.number % 10) * 20;
    } else {
      hue = 30; // Orange fallback
    }
  } else if (isSilkscreen) {
    hue = isFront ? 45 : 260; // Cream/yellow for front, purple for back
    saturation = 40;
    lightness = 85;
  } else if (isMask) {
    hue = isFront ? 120 : 240; // Green for front, blue for back
    saturation = 30;
    lightness = 50;
    alpha = 0.5;
  } else if (isPaste) {
    hue = 0;
    saturation = 0;
    lightness = 70;
  } else if (isCourtyard) {
    hue = isFront ? 180 : 300;
    saturation = 50;
    lightness = 50;
    alpha = 0.6;
  } else if (isFab) {
    hue = isFront ? 60 : 280;
    saturation = 40;
    lightness = 60;
  } else if (isEdge) {
    hue = 0;
    saturation = 0;
    lightness = 90;
  } else {
    // User layers - spread across spectrum
    hue = (layer.number * 37) % 360;
    saturation = 50;
    lightness = 55;
  }

  if (alpha < 1) {
    return `hsla(${hue}, ${saturation}%, ${lightness}%, ${alpha})`;
  }
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Build a color map from the layer definitions in the PCB data
 */
function buildLayerColorMap(layers: Record<string, LayerInfo>): Map<string, string> {
  const colorMap = new Map<string, string>();

  for (const [name, info] of Object.entries(layers)) {
    colorMap.set(name, generateLayerColor(info, name));
  }

  return colorMap;
}

/**
 * Get diff overlay colors
 */
function getDiffColor(status: DiffStatus): string {
  // These are semantic colors that could also be made configurable via props
  switch (status) {
    case 'unchanged': return '#585b70'; // Gray
    case 'added': return '#a6e3a1'; // Green
    case 'removed': return '#f38ba8'; // Red/pink
    case 'modified': return '#fab387'; // Orange
    default: return '#cdd6f4';
  }
}

/**
 * Generate a distinct color for a net based on its number.
 * Uses golden ratio to spread colors evenly across the hue spectrum.
 */
function generateNetColor(netNumber: number): string {
  if (netNumber === 0) {
    // Net 0 is typically unconnected/no net - use gray
    return '#6c7086';
  }

  // Use golden ratio to distribute hues evenly
  const goldenRatio = 0.618033988749895;
  const hue = ((netNumber * goldenRatio) % 1) * 360;

  // Vary saturation and lightness slightly for more distinct colors
  const saturation = 65 + (netNumber % 3) * 10; // 65-85%
  const lightness = 55 + (netNumber % 4) * 5;   // 55-70%

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
}

/**
 * Build a color map for all nets in the PCB data
 */
function buildNetColorMap(nets: Record<number, { number: number; name: string }>): Map<number, string> {
  const colorMap = new Map<number, string>();

  for (const [numStr, info] of Object.entries(nets)) {
    const num = parseInt(numStr);
    colorMap.set(num, generateNetColor(num));
  }

  return colorMap;
}

// ============================================================================
// Element Comparison Helpers
// ============================================================================

/** Check if two segments are the same (by position and properties) */
function isSameSegment(a: Segment, b: Segment): boolean {
  return a.start.x === b.start.x && a.start.y === b.start.y &&
         a.end.x === b.end.x && a.end.y === b.end.y &&
         a.layer === b.layer;
}

/** Check if two vias are the same (by position) */
function isSameVia(a: Via, b: Via): boolean {
  return a.at.x === b.at.x && a.at.y === b.at.y;
}

// ============================================================================
// Coordinate Transformation
// ============================================================================

interface Transform {
  pcbToCanvas: (x: number, y: number) => Point;
  canvasToPcb: (x: number, y: number) => Point;
  scale: (size: number) => number;
}

function createTransform(
  canvasWidth: number,
  canvasHeight: number,
  zoom: number,
  panX: number,
  panY: number,
  centerX: number,
  centerY: number
): Transform {
  return {
    pcbToCanvas: (x: number, y: number) => ({
      x: (x - centerX) * zoom + canvasWidth / 2 + panX,
      y: (y - centerY) * zoom + canvasHeight / 2 + panY,
    }),
    canvasToPcb: (x: number, y: number) => ({
      x: (x - canvasWidth / 2 - panX) / zoom + centerX,
      y: (y - canvasHeight / 2 - panY) / zoom + centerY,
    }),
    scale: (size: number) => size * zoom,
  };
}

// ============================================================================
// Rendering Functions
// ============================================================================

function renderFootprint(
  ctx: CanvasRenderingContext2D,
  fp: Footprint,
  transform: Transform,
  color: string,
  isHovered: boolean,
  highlightedNet: number | null,
  highlightColor: string,
  colorByNet: boolean = false,
  getNetColor?: (net: number | null) => string
) {
  const pos = transform.pcbToCanvas(fp.at.x, fp.at.y);

  ctx.save();
  ctx.translate(pos.x, pos.y);
  // Negate rotation: KiCad uses counter-clockwise positive, canvas uses clockwise
  ctx.rotate((-fp.at.r * Math.PI) / 180);

  // Add glow effect when hovered
  if (isHovered) {
    ctx.shadowColor = highlightColor;
    ctx.shadowBlur = 15;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
  }

  // Draw pads
  fp.pads.forEach(pad => {
    // Pad positions are relative to footprint center in mm
    // Scale by zoom to convert to canvas pixels
    // Note: KiCad pad coordinates are in footprint-local space
    const zoom = transform.scale(1);
    // Negate Y because KiCad uses Y-down but after footprint rotation
    // the local coordinate system might be different
    const padPos = { x: pad.at.x * zoom, y: -pad.at.y * zoom };

    // Check if this pad's net is highlighted
    const isPadHighlighted = highlightedNet !== null && pad.net === highlightedNet;

    // Determine pad color: highlighted > net color > base color
    let padColor = color;
    if (isPadHighlighted) {
      padColor = highlightColor;
    } else if (colorByNet && getNetColor && pad.net !== null) {
      padColor = getNetColor(pad.net);
    }

    ctx.save();
    ctx.translate(padPos.x, padPos.y);
    // Pad rotation is relative to the footprint (already rotated)
    // Negate to match KiCad's counter-clockwise convention
    if (pad.at.r !== 0) {
      ctx.rotate((-pad.at.r * Math.PI) / 180);
    }

    if (pad.size) {
      const w = transform.scale(pad.size.w);
      const h = transform.scale(pad.size.h);

      ctx.fillStyle = padColor;
      ctx.globalAlpha = isPadHighlighted ? 1 : 0.8;

      // Normalize shape to lowercase for comparison
      const shape = (pad.shape || '').toLowerCase();

      if (shape === 'circle') {
        ctx.beginPath();
        ctx.arc(0, 0, w / 2, 0, Math.PI * 2);
        ctx.fill();
      } else if (shape === 'oval') {
        // Oval is like a rounded rect with maximum rounding
        ctx.beginPath();
        const radius = Math.min(w, h) / 2;
        ctx.roundRect(-w / 2, -h / 2, w, h, radius);
        ctx.fill();
      } else if (shape === 'roundrect' || shape === 'chamfered_rect') {
        const radius = Math.min(w, h) * 0.25;
        ctx.beginPath();
        ctx.roundRect(-w / 2, -h / 2, w, h, radius);
        ctx.fill();
      } else if (shape === 'trapezoid') {
        // Approximate trapezoid as a slightly narrower rectangle at one end
        const inset = Math.min(w, h) * 0.1;
        ctx.beginPath();
        ctx.moveTo(-w / 2 + inset, -h / 2);
        ctx.lineTo(w / 2 - inset, -h / 2);
        ctx.lineTo(w / 2, h / 2);
        ctx.lineTo(-w / 2, h / 2);
        ctx.closePath();
        ctx.fill();
      } else {
        // Default: rect or unknown shapes - use rectangle
        ctx.fillRect(-w / 2, -h / 2, w, h);
      }
    }

    ctx.restore();
  });

  // Draw reference designator if it exists
  if (fp.reference) {
    const fontSize = Math.max(8, transform.scale(0.8));
    ctx.font = `${fontSize}px monospace`;
    ctx.fillStyle = isHovered ? highlightColor : color;
    ctx.globalAlpha = 0.9;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(fp.reference, 0, -transform.scale(2));
  }

  ctx.restore();
}

function renderSegment(
  ctx: CanvasRenderingContext2D,
  seg: Segment,
  transform: Transform,
  color: string,
  isHighlighted: boolean,
  highlightColor: string,
  isHovered: boolean = false
) {
  const start = transform.pcbToCanvas(seg.start.x, seg.start.y);
  const end = transform.pcbToCanvas(seg.end.x, seg.end.y);
  const width = transform.scale(seg.width);

  ctx.save();

  // Add glow effect when hovered
  if (isHovered) {
    ctx.shadowColor = highlightColor;
    ctx.shadowBlur = 12;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
  }

  ctx.strokeStyle = isHovered ? highlightColor : (isHighlighted ? highlightColor : color);
  ctx.lineWidth = Math.max(1, width);
  ctx.lineCap = 'round';
  ctx.globalAlpha = isHighlighted || isHovered ? 1 : 0.9;

  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();

  ctx.restore();
}

function renderVia(
  ctx: CanvasRenderingContext2D,
  via: Via,
  transform: Transform,
  color: string,
  isHighlighted: boolean,
  highlightColor: string,
  bgColor: string,
  isHovered: boolean = false
) {
  const pos = transform.pcbToCanvas(via.at.x, via.at.y);
  const outerRadius = transform.scale(via.size / 2);
  const innerRadius = transform.scale(via.drill / 2);

  ctx.save();

  // Add glow effect when hovered
  if (isHovered) {
    ctx.shadowColor = highlightColor;
    ctx.shadowBlur = 12;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 0;
  }

  // Outer ring
  ctx.fillStyle = isHovered ? highlightColor : (isHighlighted ? highlightColor : color);
  ctx.globalAlpha = isHighlighted || isHovered ? 1 : 0.9;
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, Math.max(2, outerRadius), 0, Math.PI * 2);
  ctx.fill();

  // Reset shadow for inner hole
  ctx.shadowBlur = 0;

  // Inner hole
  ctx.fillStyle = bgColor;
  ctx.globalAlpha = 1;
  ctx.beginPath();
  ctx.arc(pos.x, pos.y, Math.max(1, innerRadius), 0, Math.PI * 2);
  ctx.fill();

  ctx.restore();
}

function renderGraphicLine(
  ctx: CanvasRenderingContext2D,
  line: GraphicLine,
  transform: Transform,
  color: string
) {
  const start = transform.pcbToCanvas(line.start.x, line.start.y);
  const end = transform.pcbToCanvas(line.end.x, line.end.y);
  const width = transform.scale(line.strokeWidth || 0.15);

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, width);
  ctx.lineCap = 'round';
  ctx.globalAlpha = 0.9;

  ctx.beginPath();
  ctx.moveTo(start.x, start.y);
  ctx.lineTo(end.x, end.y);
  ctx.stroke();

  ctx.restore();
}

function renderArc(
  ctx: CanvasRenderingContext2D,
  arc: Arc,
  transform: Transform,
  color: string
) {
  const start = transform.pcbToCanvas(arc.start.x, arc.start.y);
  const end = transform.pcbToCanvas(arc.end.x, arc.end.y);
  const width = transform.scale(arc.width || 0.15);

  ctx.save();
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, width);
  ctx.lineCap = 'round';
  ctx.globalAlpha = 0.9;

  ctx.beginPath();

  if (arc.mid) {
    // We have a mid point - draw arc through three points using quadratic curve
    const mid = transform.pcbToCanvas(arc.mid.x, arc.mid.y);

    // Calculate the center and radius of the arc from 3 points
    // Using the perpendicular bisector method
    const ax = start.x, ay = start.y;
    const bx = mid.x, by = mid.y;
    const cx = end.x, cy = end.y;

    // Midpoints
    const d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));

    if (Math.abs(d) < 0.0001) {
      // Points are collinear, draw a line
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
    } else {
      // Calculate center
      const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d;
      const uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;

      const radius = Math.sqrt((ax - ux) * (ax - ux) + (ay - uy) * (ay - uy));

      // Calculate start and end angles
      const startAngle = Math.atan2(ay - uy, ax - ux);
      const endAngle = Math.atan2(cy - uy, cx - ux);
      const midAngle = Math.atan2(by - uy, bx - ux);

      // Determine direction (clockwise or counter-clockwise)
      // Check if mid angle is between start and end going counter-clockwise
      const normalizeAngle = (a: number) => (a + Math.PI * 2) % (Math.PI * 2);
      const startN = normalizeAngle(startAngle);
      const endN = normalizeAngle(endAngle);
      const midN = normalizeAngle(midAngle);

      let counterClockwise: boolean;
      if (startN < endN) {
        counterClockwise = midN > startN && midN < endN;
      } else {
        counterClockwise = midN > startN || midN < endN;
      }

      ctx.arc(ux, uy, radius, startAngle, endAngle, !counterClockwise);
    }
  } else {
    // No mid point - just draw a line from start to end
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
  }

  ctx.stroke();
  ctx.restore();
}

// ============================================================================
// Main Hook
// ============================================================================

export interface CanvasRendererOptions {
  backgroundColor?: string;
  highlightColor?: string;
}

export function useCanvasRenderer(
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  options: CanvasRendererOptions = {}
) {
  const { state } = usePcbViewer();
  const animationFrameRef = useRef<number>(0);
  const layerColorsRef = useRef<Map<string, string>>(new Map());
  const netColorsRef = useRef<Map<number, string>>(new Map());

  // Update layer and net colors when data changes
  useEffect(() => {
    const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
    if (data?.layers) {
      layerColorsRef.current = buildLayerColorMap(data.layers);
    }
    if (data?.nets) {
      netColorsRef.current = buildNetColorMap(data.nets);
    }
  }, [state.pcbData, state.diffData, state.mode]);

  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Get actual canvas size
    const rect = canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;

    // Set canvas size to match display size
    if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.scale(dpr, dpr);
    }

    const bgColor = options.backgroundColor || '#1e1e2e';
    const highlightColor = options.highlightColor || '#f9e2af';

    // Clear canvas
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, rect.width, rect.height);

    // Get data
    const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
    if (!data) return;

    // Calculate center from bounds
    const centerX = (data.bounds.minX + data.bounds.maxX) / 2;
    const centerY = (data.bounds.minY + data.bounds.maxY) / 2;

    const transform = createTransform(
      rect.width,
      rect.height,
      state.view.zoom,
      state.view.panX,
      state.view.panY,
      centerX,
      centerY
    );

    const { layerVisibility, highlightedNet, hoveredElement, selectedElement, colorMode } = state;
    const layerColors = layerColorsRef.current;
    const netColors = netColorsRef.current;

    // Helper to check if layer should be rendered
    const shouldRender = (layer: string) => layerVisibility[layer] !== false;

    // Helper to get layer color
    const getLayerColor = (layer: string) => layerColors.get(layer) || '#888888';

    // Helper to get net color
    const getNetColor = (netNumber: number | null) => {
      if (netNumber === null) return '#6c7086';
      return netColors.get(netNumber) || generateNetColor(netNumber);
    };

    // Helper to get color based on current mode (for copper elements)
    const getElementColor = (layer: string, netNumber: number | null) => {
      if (colorMode === 'net' && netNumber !== null) {
        return getNetColor(netNumber);
      }
      return getLayerColor(layer);
    };

    // Get diff data if in diff mode
    const diffData = state.mode === 'diff' ? state.diffData : null;

    // Render order: graphic lines (board outline) -> segments (traces) -> vias -> footprints

    // Render graphic lines (board outline, etc.) - always use layer color
    if (data) {
      data.elements.graphicLines.forEach(line => {
        if (!shouldRender(line.layer)) return;
        const color = getLayerColor(line.layer);
        renderGraphicLine(ctx, line, transform, color);
      });
    }

    // Render arcs (curved board outline edges, etc.) - always use layer color
    if (data) {
      data.elements.arcs.forEach(arc => {
        if (!shouldRender(arc.layer)) return;
        const color = getLayerColor(arc.layer);
        renderArc(ctx, arc, transform, color);
      });
    }

    // Render segments
    if (diffData) {
      // Diff mode - render with diff colors (ignoring colorMode in diff view)
      diffData.diff.segments.forEach(({ status, element, counterpart }) => {
        if (!shouldRender(element.layer)) return;

        const isHovered = hoveredElement?.type === 'segment' &&
          isSameSegment(hoveredElement as Segment, element);

        if (status === 'removed') {
          if (!state.showBeforeState) return;
          const isHighlighted = highlightedNet === element.net;
          renderSegment(ctx, element, transform, getDiffColor('removed'), isHighlighted, highlightColor, isHovered);
        } else if (status === 'added') {
          if (!state.showAfterState) return;
          const isHighlighted = highlightedNet === element.net;
          renderSegment(ctx, element, transform, getDiffColor('added'), isHighlighted, highlightColor, isHovered);
        } else if (status === 'modified') {
          const isHighlighted = highlightedNet === element.net;
          // Render before state (counterpart) in orange
          if (state.showBeforeState && counterpart) {
            renderSegment(ctx, counterpart as Segment, transform, '#fab387', isHighlighted, highlightColor, false);
          }
          // Render after state in blue
          if (state.showAfterState) {
            renderSegment(ctx, element, transform, '#89b4fa', isHighlighted, highlightColor, isHovered);
          }
        } else {
          // Unchanged - use colorMode
          const isHighlighted = highlightedNet === element.net;
          const color = colorMode === 'net' ? getNetColor(element.net) : getDiffColor('unchanged');
          renderSegment(ctx, element, transform, color, isHighlighted, highlightColor, isHovered);
        }
      });
    } else if (data) {
      // Single mode - use layer or net colors based on colorMode
      data.elements.segments.forEach(seg => {
        if (!shouldRender(seg.layer)) return;
        const isHighlighted = highlightedNet === seg.net;
        const isHovered = hoveredElement?.type === 'segment' &&
          isSameSegment(hoveredElement as Segment, seg);
        const color = getElementColor(seg.layer, seg.net);
        renderSegment(ctx, seg, transform, color, isHighlighted, highlightColor, isHovered);
      });
    }

    // Render vias
    if (diffData) {
      diffData.diff.vias.forEach(({ status, element }) => {
        if (status === 'removed' && !state.showBeforeState) return;
        if ((status === 'added' || status === 'modified') && !state.showAfterState) return;

        const isHighlighted = highlightedNet === element.net;
        const isHovered = hoveredElement?.type === 'via' &&
          isSameVia(hoveredElement as Via, element);
        // For unchanged vias, respect colorMode
        const color = status === 'unchanged' && colorMode === 'net'
          ? getNetColor(element.net)
          : getDiffColor(status);
        renderVia(ctx, element, transform, color, isHighlighted, highlightColor, bgColor, isHovered);
      });
    } else if (data) {
      // Use net color in net mode, otherwise use copper color
      data.elements.vias.forEach(via => {
        const isHighlighted = highlightedNet === via.net;
        const isHovered = hoveredElement?.type === 'via' &&
          isSameVia(hoveredElement as Via, via);
        const color = colorMode === 'net'
          ? getNetColor(via.net)
          : (getLayerColor('F.Cu') || getLayerColor('B.Cu') || '#f38ba8');
        renderVia(ctx, via, transform, color, isHighlighted, highlightColor, bgColor, isHovered);
      });
    }

    // Render footprints
    if (diffData) {
      diffData.diff.footprints.forEach(({ status, element, counterpart }) => {
        if (!shouldRender(element.layer)) return;

        const isHighlighted = hoveredElement?.type === 'footprint' &&
          (hoveredElement as Footprint).uuid === element.uuid;

        if (status === 'removed') {
          if (!state.showBeforeState) return;
          renderFootprint(ctx, element, transform, getDiffColor('removed'), isHighlighted, highlightedNet, highlightColor, false);
        } else if (status === 'added') {
          if (!state.showAfterState) return;
          renderFootprint(ctx, element, transform, getDiffColor('added'), isHighlighted, highlightedNet, highlightColor, false);
        } else if (status === 'modified') {
          // Render before state (counterpart) in orange
          if (state.showBeforeState && counterpart) {
            renderFootprint(ctx, counterpart as Footprint, transform, '#fab387', isHighlighted, highlightedNet, highlightColor, false);
          }
          // Render after state in blue
          if (state.showAfterState) {
            renderFootprint(ctx, element, transform, '#89b4fa', isHighlighted, highlightedNet, highlightColor, false);
          }
        } else {
          // Unchanged - respect colorMode for pads
          const color = colorMode === 'net' ? getLayerColor(element.layer) : getDiffColor('unchanged');
          renderFootprint(ctx, element, transform, color, isHighlighted, highlightedNet, highlightColor, colorMode === 'net', getNetColor);
        }
      });
    } else if (data) {
      data.elements.footprints.forEach(fp => {
        if (!shouldRender(fp.layer)) return;
        const isHighlighted = hoveredElement?.type === 'footprint' &&
          (hoveredElement as Footprint).uuid === fp.uuid;
        const isSelected = selectedElement?.type === 'footprint' &&
          (selectedElement as Footprint).uuid === fp.uuid;
        const baseColor = isSelected ? highlightColor : getLayerColor(fp.layer);
        renderFootprint(ctx, fp, transform, baseColor, isHighlighted || isSelected, highlightedNet, highlightColor, colorMode === 'net', getNetColor);
      });
    }

  }, [state, canvasRef, options]);

  // Auto-render on state changes
  useEffect(() => {
    const scheduleRender = () => {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = requestAnimationFrame(render);
    };

    scheduleRender();

    return () => cancelAnimationFrame(animationFrameRef.current);
  }, [render]);

  return { render, layerColors: layerColorsRef.current };
}
