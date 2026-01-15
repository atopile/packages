/**
 * PCB Viewer Components - Export all components for use
 */

export { PcbViewer } from './PcbViewer';
export { Canvas } from './Canvas';
export { LayerPanel } from './LayerPanel';
export { NetPanel } from './NetPanel';
export { Inspector } from './Inspector';
export { Toolbar } from './Toolbar';
export { DiffSummary } from './DiffSummary';

// Re-export context and hooks for advanced usage
export { PcbViewerProvider, usePcbViewer } from '../context/PcbViewerContext';
export { useCanvasRenderer } from '../hooks/useCanvasRenderer';

// Re-export types
export type {
  PcbViewerProps,
  PcbData,
  PcbDiffData,
  ViewerMode,
  PcbElement,
  Footprint,
  Segment,
  Via,
  NetInfo,
  LayerInfo,
  ViewState,
  DiffStatus,
  DiffElement,
} from '../types/pcb';
