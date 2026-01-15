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
  Zone,
  PcbText,
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
    // Bright yellow for edge cuts to make them very visible
    hue = 60;
    saturation = 100;
    lightness = 70;
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
  isNetHighlighted: (net: number | null) => boolean,
  highlightColor: string,
  colorByNet: boolean = false,
  getNetColor?: (net: number | null) => string
) {
  const pos = transform.pcbToCanvas(fp.at.x, fp.at.y);

  ctx.save();
  ctx.translate(pos.x, pos.y);
  // KiCad rotation: positive = counter-clockwise
  // Canvas rotation: positive = clockwise
  // To convert: negate the angle
  const fpRotationRad = (-fp.at.r * Math.PI) / 180;
  ctx.rotate(fpRotationRad);

  const zoom = transform.scale(1);

  // Draw footprint outline with glow when hovered/selected
  if (isHovered && fp.graphics && fp.graphics.length > 0) {
    // Find courtyard graphics first, then fab, then any graphics
    const courtyardGraphics = fp.graphics.filter(g => g.layer.includes('CrtYd'));
    const fabGraphics = fp.graphics.filter(g => g.layer.includes('Fab'));
    const silkGraphics = fp.graphics.filter(g => g.layer.includes('SilkS'));
    const outlineGraphics = courtyardGraphics.length > 0 ? courtyardGraphics :
                           fabGraphics.length > 0 ? fabGraphics :
                           silkGraphics.length > 0 ? silkGraphics : [];

    if (outlineGraphics.length > 0) {
      ctx.save();
      ctx.strokeStyle = highlightColor;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.8;
      ctx.shadowColor = highlightColor;
      ctx.shadowBlur = 20;

      outlineGraphics.forEach(g => {
        ctx.beginPath();
        if (g.type === 'line' && g.start && g.end) {
          ctx.moveTo(g.start.x * zoom, g.start.y * zoom);
          ctx.lineTo(g.end.x * zoom, g.end.y * zoom);
        } else if (g.type === 'rect' && g.start && g.end) {
          const x = Math.min(g.start.x, g.end.x) * zoom;
          const y = Math.min(g.start.y, g.end.y) * zoom;
          const w = Math.abs(g.end.x - g.start.x) * zoom;
          const h = Math.abs(g.end.y - g.start.y) * zoom;
          ctx.rect(x, y, w, h);
        } else if (g.type === 'circle' && g.center && g.end) {
          const radius = Math.sqrt(
            Math.pow((g.end.x - g.center.x) * zoom, 2) +
            Math.pow((g.end.y - g.center.y) * zoom, 2)
          );
          ctx.arc(g.center.x * zoom, g.center.y * zoom, radius, 0, Math.PI * 2);
        } else if (g.type === 'arc' && g.start && g.end && g.mid) {
          // Similar arc rendering as renderArc
          const ax = g.start.x * zoom, ay = g.start.y * zoom;
          const bx = g.mid.x * zoom, by = g.mid.y * zoom;
          const cx = g.end.x * zoom, cy = g.end.y * zoom;
          const d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));
          if (Math.abs(d) > 0.0001) {
            const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d;
            const uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;
            const radius = Math.sqrt((ax - ux) * (ax - ux) + (ay - uy) * (ay - uy));
            const startAngle = Math.atan2(ay - uy, ax - ux);
            const endAngle = Math.atan2(cy - uy, cx - ux);
            ctx.arc(ux, uy, radius, startAngle, endAngle);
          }
        }
        ctx.stroke();
      });
      ctx.restore();
    }
  }

  // Fallback: draw bounding box outline from pads when hovered and no graphics
  if (isHovered && (!fp.graphics || fp.graphics.length === 0) && fp.pads.length > 0) {
    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    fp.pads.forEach(pad => {
      const halfW = (pad.size?.w || 0.5) / 2;
      const halfH = (pad.size?.h || 0.5) / 2;
      minX = Math.min(minX, pad.at.x - halfW);
      minY = Math.min(minY, pad.at.y - halfH);
      maxX = Math.max(maxX, pad.at.x + halfW);
      maxY = Math.max(maxY, pad.at.y + halfH);
    });
    // Add margin
    const margin = 0.3;
    minX -= margin; minY -= margin; maxX += margin; maxY += margin;

    ctx.save();
    ctx.strokeStyle = highlightColor;
    ctx.lineWidth = 2;
    ctx.globalAlpha = 0.6;
    ctx.shadowColor = highlightColor;
    ctx.shadowBlur = 15;
    ctx.setLineDash([4, 4]);
    ctx.strokeRect(minX * zoom, minY * zoom, (maxX - minX) * zoom, (maxY - minY) * zoom);
    ctx.restore();
  }

  // Draw pads
  fp.pads.forEach(pad => {
    // Pad positions are in footprint-local coordinates (mm)
    const padPos = { x: pad.at.x * zoom, y: pad.at.y * zoom };

    // Check if this pad's net is highlighted
    const isPadHighlighted = isNetHighlighted(pad.net);

    // Determine pad color: highlighted > net color > base color
    let padColor = color;
    if (isPadHighlighted) {
      padColor = highlightColor;
    } else if (colorByNet && getNetColor && pad.net !== null) {
      padColor = getNetColor(pad.net);
    }

    ctx.save();
    ctx.translate(padPos.x, padPos.y);
    // IMPORTANT: In KiCad, pad.at.r is in BOARD coordinates, not footprint-local!
    // When a footprint is rotated, KiCad updates pad rotations to include the fp rotation.
    // Since we already applied fp rotation to the context, we need the pad's LOCAL rotation,
    // which is: pad_board_rotation - footprint_rotation
    const padLocalRotation = (pad.at.r || 0) - (fp.at.r || 0);
    if (padLocalRotation !== 0) {
      ctx.rotate((-padLocalRotation * Math.PI) / 180);
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

  ctx.restore();
}

function renderSegment(
  ctx: CanvasRenderingContext2D,
  seg: Segment,
  transform: Transform,
  color: string,
  isHighlighted: boolean,
  highlightColor: string,
  isHovered: boolean = false,
  baseOpacity: number = 0.9
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
  ctx.globalAlpha = isHighlighted || isHovered ? 1 : baseOpacity;

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
  isHovered: boolean = false,
  baseOpacity: number = 0.9
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
  ctx.globalAlpha = isHighlighted || isHovered ? 1 : baseOpacity;
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
  ctx.lineWidth = Math.max(2, width);
  ctx.lineCap = 'round';
  ctx.globalAlpha = 1.0;

  if (arc.mid) {
    const mid = transform.pcbToCanvas(arc.mid.x, arc.mid.y);

    // Calculate circle center from 3 points (start, mid, end)
    const ax = start.x, ay = start.y;
    const bx = mid.x, by = mid.y;
    const cx = end.x, cy = end.y;

    // Determinant for center calculation
    const d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by));

    if (Math.abs(d) < 0.0001) {
      // Points are collinear, draw a line
      ctx.beginPath();
      ctx.moveTo(start.x, start.y);
      ctx.lineTo(end.x, end.y);
      ctx.stroke();
    } else {
      // Calculate center of circle through 3 points
      const ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d;
      const uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d;

      const radius = Math.sqrt((ax - ux) * (ax - ux) + (ay - uy) * (ay - uy));

      // Calculate angles
      const startAngle = Math.atan2(ay - uy, ax - ux);
      const midAngle = Math.atan2(by - uy, bx - ux);
      const endAngle = Math.atan2(cy - uy, cx - ux);

      // Determine if we go clockwise or counter-clockwise
      // The mid point tells us which way to go around the circle
      // Normalize angles to [0, 2π)
      const normalize = (a: number) => ((a % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
      const sn = normalize(startAngle);
      const mn = normalize(midAngle);
      const en = normalize(endAngle);

      // Check if mid is between start and end going counter-clockwise
      let anticlockwise: boolean;
      if (sn <= en) {
        anticlockwise = mn >= sn && mn <= en;
      } else {
        anticlockwise = mn >= sn || mn <= en;
      }

      ctx.beginPath();
      ctx.arc(ux, uy, radius, startAngle, endAngle, !anticlockwise);
      ctx.stroke();
    }
  } else {
    // No mid point - just draw a line from start to end
    ctx.beginPath();
    ctx.moveTo(start.x, start.y);
    ctx.lineTo(end.x, end.y);
    ctx.stroke();
  }

  ctx.restore();
}

function renderZone(
  ctx: CanvasRenderingContext2D,
  zone: Zone,
  transform: Transform,
  color: string,
  isHighlighted: boolean,
  highlightColor: string,
  baseOpacity: number = 0.25
) {
  // Only render zones that have filled polygons (actual copper after DRC fill)
  // Skip zones with only outline (keepout rectangles, unfilled zones)
  if (zone.filledPolygons.length === 0) return;

  ctx.save();

  // Use reduced opacity for zones to see traces through them
  ctx.globalAlpha = isHighlighted ? Math.min(baseOpacity * 2, 1) : baseOpacity;
  ctx.fillStyle = isHighlighted ? highlightColor : color;

  // Render only the filled polygons (actual copper shapes)
  for (const filledPoly of zone.filledPolygons) {
    const points = filledPoly.points;
    if (points.length < 3) continue;

    ctx.beginPath();
    const firstPoint = transform.pcbToCanvas(points[0].x, points[0].y);
    ctx.moveTo(firstPoint.x, firstPoint.y);

    for (let i = 1; i < points.length; i++) {
      const pt = transform.pcbToCanvas(points[i].x, points[i].y);
      ctx.lineTo(pt.x, pt.y);
    }

    ctx.closePath();
    ctx.fill();
  }

  ctx.restore();
}

function renderText(
  ctx: CanvasRenderingContext2D,
  text: PcbText,
  transform: Transform,
  color: string,
  baseOpacity: number = 0.9
) {
  // Skip hidden text
  if (text.hide) return;

  const pos = transform.pcbToCanvas(text.at.x, text.at.y);
  // Scale font size - KiCad uses mm, we need to scale
  const fontSize = Math.max(8, transform.scale(text.fontSize));

  ctx.save();
  ctx.translate(pos.x, pos.y);

  // Apply rotation (KiCad rotation is counter-clockwise, canvas is clockwise)
  if (text.at.r) {
    ctx.rotate((-text.at.r * Math.PI) / 180);
  }

  ctx.font = `${fontSize}px sans-serif`;
  ctx.fillStyle = color;
  ctx.globalAlpha = baseOpacity;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';

  ctx.fillText(text.text, 0, 0);

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

    const { layerVisibility, highlightedNet, highlightedBus, hoveredElement, selectedElement, colorMode, opacity, busData } = state;
    const layerColors = layerColorsRef.current;
    const netColors = netColorsRef.current;

    // Build net name to net number mapping for bus lookups
    const netNameToNumber: Record<string, number> = {};
    const netNumberToName: Record<number, string> = {};
    if (data?.nets) {
      Object.entries(data.nets).forEach(([numStr, info]) => {
        netNameToNumber[info.name] = Number(numStr);
        netNumberToName[Number(numStr)] = info.name;
      });
    }

    // Helper to check if a net should be highlighted (by direct net or bus membership)
    const isNetHighlighted = (netNumber: number | null): boolean => {
      if (netNumber === null) return false;
      if (highlightedNet === netNumber) return true;
      if (highlightedBus && busData) {
        const netName = netNumberToName[netNumber];
        const bus = busData.buses[highlightedBus];
        if (bus && netName) {
          return bus.nets.some(n => n.name === netName);
        }
      }
      return false;
    };

    // Helper to get bus color for a net (if available)
    const getBusColor = (netNumber: number | null): string | null => {
      if (!busData || netNumber === null) return null;
      const netName = netNumberToName[netNumber];
      if (!netName) return null;
      const busId = busData.net_to_bus[netName];
      if (!busId) return null;
      return busData.buses[busId]?.color || null;
    };

    // Helper to check if layer should be rendered
    const shouldRender = (layer: string) => layerVisibility[layer] !== false;

    // Helper to get layer color
    const getLayerColor = (layer: string) => layerColors.get(layer) || '#888888';

    // Helper to get net color (bus color if available, otherwise generated)
    const getNetColor = (netNumber: number | null) => {
      if (netNumber === null) return '#6c7086';
      // Prefer bus color when available
      const busColor = getBusColor(netNumber);
      if (busColor) return busColor;
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

    // Render order: zones (ground planes) -> graphic lines (board outline) -> segments (traces) -> vias -> footprints

    // Render zones (polygon pours / ground planes) - render first so they're behind everything
    if (data && data.elements.zones && opacity.zones > 0) {
      // Sort by priority (lower priority renders first / behind)
      const sortedZones = [...data.elements.zones].sort((a, b) => (a.priority || 0) - (b.priority || 0));

      sortedZones.forEach(zone => {
        // Check if any layer this zone is on should be rendered
        const zoneLayers = zone.layers.length > 0 ? zone.layers : (zone.layer ? [zone.layer] : []);
        const shouldRenderZone = zoneLayers.some(l => shouldRender(l));
        if (!shouldRenderZone) return;

        const isHighlighted = isNetHighlighted(zone.net);
        const primaryLayer = zoneLayers[0] || 'F.Cu';
        const color = getElementColor(primaryLayer, zone.net);

        renderZone(ctx, zone, transform, color, isHighlighted, highlightColor, opacity.zones);
      });
    }

    // Render graphic lines (board outline, etc.) - always use layer color
    if (data) {
      data.elements.graphicLines.forEach(line => {
        if (!shouldRender(line.layer)) return;
        const color = getLayerColor(line.layer);
        renderGraphicLine(ctx, line, transform, color);
      });
    }

    // Render arcs (curved board outline edges, etc.) - always use layer color
    if (data && data.elements.arcs) {
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
          const isHighlighted = isNetHighlighted(element.net);
          renderSegment(ctx, element, transform, getDiffColor('removed'), isHighlighted, highlightColor, isHovered);
        } else if (status === 'added') {
          if (!state.showAfterState) return;
          const isHighlighted = isNetHighlighted(element.net);
          renderSegment(ctx, element, transform, getDiffColor('added'), isHighlighted, highlightColor, isHovered);
        } else if (status === 'modified') {
          const isHighlighted = isNetHighlighted(element.net);
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
          const isHighlighted = isNetHighlighted(element.net);
          const color = colorMode === 'net' ? getNetColor(element.net) : getDiffColor('unchanged');
          renderSegment(ctx, element, transform, color, isHighlighted, highlightColor, isHovered);
        }
      });
    } else if (data) {
      // Single mode - use layer or net colors based on colorMode
      data.elements.segments.forEach(seg => {
        if (!shouldRender(seg.layer)) return;
        const isHighlighted = isNetHighlighted(seg.net);
        const isHovered = hoveredElement?.type === 'segment' &&
          isSameSegment(hoveredElement as Segment, seg);
        const color = getElementColor(seg.layer, seg.net);
        renderSegment(ctx, seg, transform, color, isHighlighted, highlightColor, isHovered, opacity.tracks);
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
        renderVia(ctx, element, transform, color, isHighlighted, highlightColor, bgColor, isHovered, opacity.vias);
      });
    } else if (data) {
      // Use net color in net mode, otherwise use copper color
      data.elements.vias.forEach(via => {
        const isHighlighted = isNetHighlighted(via.net);
        const isHovered = hoveredElement?.type === 'via' &&
          isSameVia(hoveredElement as Via, via);
        const color = colorMode === 'net'
          ? getNetColor(via.net)
          : (getLayerColor('F.Cu') || getLayerColor('B.Cu') || '#f38ba8');
        renderVia(ctx, via, transform, color, isHighlighted, highlightColor, bgColor, isHovered, opacity.vias);
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
          renderFootprint(ctx, element, transform, getDiffColor('removed'), isHighlighted, isNetHighlighted, highlightColor, false);
        } else if (status === 'added') {
          if (!state.showAfterState) return;
          renderFootprint(ctx, element, transform, getDiffColor('added'), isHighlighted, isNetHighlighted, highlightColor, false);
        } else if (status === 'modified') {
          // Render before state (counterpart) in orange
          if (state.showBeforeState && counterpart) {
            renderFootprint(ctx, counterpart as Footprint, transform, '#fab387', isHighlighted, isNetHighlighted, highlightColor, false);
          }
          // Render after state in blue
          if (state.showAfterState) {
            renderFootprint(ctx, element, transform, '#89b4fa', isHighlighted, isNetHighlighted, highlightColor, false);
          }
        } else {
          // Unchanged - respect colorMode for pads
          const color = colorMode === 'net' ? getLayerColor(element.layer) : getDiffColor('unchanged');
          renderFootprint(ctx, element, transform, color, isHighlighted, isNetHighlighted, highlightColor, colorMode === 'net', getNetColor);
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
        renderFootprint(ctx, fp, transform, baseColor, isHighlighted || isSelected, isNetHighlighted, highlightColor, colorMode === 'net', getNetColor);
      });
    }

    // Render texts (last, on top of everything)
    if (data && data.elements.texts && opacity.text > 0) {
      data.elements.texts.forEach(text => {
        if (!shouldRender(text.layer)) return;
        const color = getLayerColor(text.layer);
        renderText(ctx, text, transform, color, opacity.text);
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
