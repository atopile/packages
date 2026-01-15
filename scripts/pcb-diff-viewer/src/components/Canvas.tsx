/**
 * PCB Canvas - Main rendering surface with pan/zoom interactions
 */

import { useRef, useEffect, useCallback, useState } from 'react';
import { usePcbViewer } from '../context/PcbViewerContext';
import { useCanvasRenderer } from '../hooks/useCanvasRenderer';
import type { Point, Footprint, Segment, Via, PcbElement } from '../types/pcb';

interface CanvasProps {
  className?: string;
  backgroundColor?: string;
  highlightColor?: string;
}

/**
 * Calculate distance from a point to a line segment
 */
function pointToSegmentDistance(
  point: Point,
  segStart: Point,
  segEnd: Point
): number {
  const dx = segEnd.x - segStart.x;
  const dy = segEnd.y - segStart.y;
  const lengthSq = dx * dx + dy * dy;

  if (lengthSq === 0) {
    // Segment is a point
    return Math.sqrt(Math.pow(point.x - segStart.x, 2) + Math.pow(point.y - segStart.y, 2));
  }

  // Project point onto line, clamped to segment
  let t = ((point.x - segStart.x) * dx + (point.y - segStart.y) * dy) / lengthSq;
  t = Math.max(0, Math.min(1, t));

  const projX = segStart.x + t * dx;
  const projY = segStart.y + t * dy;

  return Math.sqrt(Math.pow(point.x - projX, 2) + Math.pow(point.y - projY, 2));
}

export function Canvas({ className, backgroundColor, highlightColor }: CanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { state, zoom, pan, setHovered, setSelected, highlightNet } = usePcbViewer();
  const { render, layerColors } = useCanvasRenderer(canvasRef, { backgroundColor, highlightColor });

  // Drag state
  const [isDragging, setIsDragging] = useState(false);
  const lastPosRef = useRef<Point>({ x: 0, y: 0 });

  // Handle wheel zoom
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault();
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    // Calculate mouse offset from canvas center (for zoom-toward-cursor)
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const offsetFromCenterX = mouseX - rect.width / 2;
    const offsetFromCenterY = mouseY - rect.height / 2;

    zoom(-e.deltaY, offsetFromCenterX, offsetFromCenterY);
  }, [zoom]);

  // Handle mouse down (start pan)
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0 || e.button === 1) { // Left or middle click
      setIsDragging(true);
      lastPosRef.current = { x: e.clientX, y: e.clientY };
    }
  }, []);

  // Handle mouse move (pan or hover detection)
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging) {
      const deltaX = e.clientX - lastPosRef.current.x;
      const deltaY = e.clientY - lastPosRef.current.y;
      pan(deltaX, deltaY);
      lastPosRef.current = { x: e.clientX, y: e.clientY };
    } else {
      // Hit detection for hover
      const rect = canvasRef.current?.getBoundingClientRect();
      if (!rect) return;

      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const data = state.mode === 'diff' ? state.diffData?.after : state.pcbData;
      if (!data) return;

      // Transform mouse to PCB coordinates (must match renderer transform exactly)
      const centerX = (data.bounds.minX + data.bounds.maxX) / 2;
      const centerY = (data.bounds.minY + data.bounds.maxY) / 2;
      const pcbX = (mouseX - rect.width / 2 - state.view.panX) / state.view.zoom + centerX;
      const pcbY = (mouseY - rect.height / 2 - state.view.panY) / state.view.zoom + centerY;

      // Hit threshold in PCB units (mm) - scales inversely with zoom for consistent feel
      // At zoom=1, threshold is ~2mm; at zoom=10, threshold is ~0.5mm
      const hitThreshold = Math.max(0.3, 2 / state.view.zoom);

      // Priority: vias (small, easy to miss) -> footprints (important) -> traces (everywhere)
      const { selectionFilter } = state;

      // Check vias first (they're small and easy to miss otherwise)
      if (selectionFilter.vias) {
        let hoveredVia: Via | null = null;
        let minViaDist = Infinity;
        for (const via of data.elements.vias) {
          const dist = Math.sqrt(Math.pow(via.at.x - pcbX, 2) + Math.pow(via.at.y - pcbY, 2));
          // Hit if within outer radius plus threshold
          if (dist < via.size / 2 + hitThreshold && dist < minViaDist) {
            hoveredVia = via;
            minViaDist = dist;
          }
        }

        if (hoveredVia) {
          setHovered(hoveredVia);
          return;
        }
      }

      // Check footprints - use pad-based hit detection for accuracy
      if (selectionFilter.footprints) {
        let hoveredFp: Footprint | null = null;
        let minFpDist = Infinity;
        for (const fp of data.elements.footprints) {
        // Transform point to footprint's local coordinates
        const cosR = Math.cos((-fp.at.r * Math.PI) / 180);
        const sinR = Math.sin((-fp.at.r * Math.PI) / 180);
        const relX = pcbX - fp.at.x;
        const relY = pcbY - fp.at.y;
        const localX = relX * cosR - relY * sinR;
        const localY = relX * sinR + relY * cosR;

        // Check if point is within any pad (most accurate)
        for (const pad of fp.pads) {
          if (!pad.size) continue;

          // Transform to pad's local coordinates
          // NOTE: pad.at.r is in BOARD coordinates. We need LOCAL rotation relative to footprint.
          const padLocalRotation = (pad.at.r || 0) - (fp.at.r || 0);
          const padCosR = Math.cos((-padLocalRotation * Math.PI) / 180);
          const padSinR = Math.sin((-padLocalRotation * Math.PI) / 180);
          const padRelX = localX - pad.at.x;
          const padRelY = localY - pad.at.y;
          const padLocalX = padRelX * padCosR - padRelY * padSinR;
          const padLocalY = padRelX * padSinR + padRelY * padCosR;

          // Check if within pad bounds (with threshold)
          const halfW = pad.size.w / 2 + hitThreshold;
          const halfH = pad.size.h / 2 + hitThreshold;

          if (Math.abs(padLocalX) <= halfW && Math.abs(padLocalY) <= halfH) {
            const distToCenter = Math.sqrt(relX * relX + relY * relY);
            if (distToCenter < minFpDist) {
              hoveredFp = fp;
              minFpDist = distToCenter;
            }
            break; // Found a matching pad, no need to check more pads in this footprint
          }
        }

        // Fallback: check distance to footprint center if no pads matched
          // (handles footprints with no pads or very small pads)
          if (!hoveredFp) {
            const distToCenter = Math.sqrt(relX * relX + relY * relY);
            if (distToCenter < 2 + hitThreshold && distToCenter < minFpDist) {
              hoveredFp = fp;
              minFpDist = distToCenter;
            }
          }
        }

        if (hoveredFp) {
          setHovered(hoveredFp);
          return;
        }
      }

      // Check segments (traces) last - they're everywhere
      if (selectionFilter.segments) {
        let hoveredSeg: Segment | null = null;
        let minSegDist = Infinity;
        for (const seg of data.elements.segments) {
          const dist = pointToSegmentDistance(
            { x: pcbX, y: pcbY },
            { x: seg.start.x, y: seg.start.y },
            { x: seg.end.x, y: seg.end.y }
          );
          const effectiveWidth = Math.max(seg.width / 2, hitThreshold);
          if (dist < effectiveWidth && dist < minSegDist) {
            hoveredSeg = seg;
            minSegDist = dist;
          }
        }

        if (hoveredSeg) {
          setHovered(hoveredSeg);
          return;
        }
      }

      // Nothing found
      setHovered(null);
    }
  }, [isDragging, pan, state, setHovered]);

  // Handle mouse up (end pan)
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // Handle click (select element or highlight net with cmd+click)
  const handleClick = useCallback((e: React.MouseEvent) => {
    const hovered = state.hoveredElement;

    if (e.metaKey || e.ctrlKey) {
      // Cmd+click (Mac) or Ctrl+click (Windows): highlight entire net
      if (hovered) {
        // Get net from element
        let netId: number | null = null;
        if (hovered.type === 'segment') {
          netId = (hovered as Segment).net;
        } else if (hovered.type === 'via') {
          netId = (hovered as Via).net;
        } else if (hovered.type === 'footprint') {
          // For footprints, could highlight first pad's net (or show a menu)
          const fp = hovered as Footprint;
          if (fp.pads.length > 0) {
            netId = fp.pads[0].net;
          }
        }

        if (netId !== null) {
          // Toggle net highlight (click again to unhighlight)
          highlightNet(state.highlightedNet === netId ? null : netId);
        }
      } else {
        // Cmd+click on empty space clears net highlight
        highlightNet(null);
      }
    } else {
      // Regular click: select element
      if (hovered) {
        setSelected(hovered);
        // Also highlight the net when selecting a trace/via
        if (hovered.type === 'segment' || hovered.type === 'via') {
          const netId = hovered.type === 'segment'
            ? (hovered as Segment).net
            : (hovered as Via).net;
          highlightNet(netId);
        }
      } else {
        // Click on empty space: clear selection and net highlight
        setSelected(null);
        highlightNet(null);
      }
    }
  }, [state.hoveredElement, state.highlightedNet, setSelected, highlightNet]);

  // Add wheel event listener (need passive: false for preventDefault)
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    canvas.addEventListener('wheel', handleWheel, { passive: false });
    return () => canvas.removeEventListener('wheel', handleWheel);
  }, [handleWheel]);

  // Handle window mouse up (in case drag ends outside canvas)
  useEffect(() => {
    if (isDragging) {
      const handleGlobalMouseUp = () => setIsDragging(false);
      window.addEventListener('mouseup', handleGlobalMouseUp);
      return () => window.removeEventListener('mouseup', handleGlobalMouseUp);
    }
  }, [isDragging]);

  // Resize observer
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const resizeObserver = new ResizeObserver(() => {
      render();
    });

    resizeObserver.observe(container);
    return () => resizeObserver.disconnect();
  }, [render]);

  // Determine cursor based on state
  const getCursor = () => {
    if (isDragging) return 'grabbing';
    if (state.hoveredElement) return 'pointer';
    return 'grab';
  };

  return (
    <div
      ref={containerRef}
      className={`pcb-canvas-container ${className || ''}`}
      style={{ cursor: getCursor() }}
    >
      <canvas
        ref={canvasRef}
        className="pcb-canvas"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onClick={handleClick}
      />

      {/* Keyboard hints */}
      <div className="pcb-keyboard-hint">
        <span><kbd>Scroll</kbd> Zoom</span>
        <span><kbd>Drag</kbd> Pan</span>
        <span><kbd>Click</kbd> Select</span>
        <span><kbd>⌘+Click</kbd> Highlight Net</span>
      </div>
    </div>
  );
}
