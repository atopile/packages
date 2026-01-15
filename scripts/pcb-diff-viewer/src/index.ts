/**
 * PCB Viewer - Main library export
 *
 * This is the entry point for using PcbViewer as a library in other projects.
 *
 * Usage:
 * ```tsx
 * import { PcbViewer } from '@atopile/pcb-viewer';
 *
 * function MyApp() {
 *   return <PcbViewer data={pcbData} />;
 * }
 * ```
 */

// Main component
export { PcbViewer } from './components/PcbViewer';

// Individual components for custom layouts
export { Canvas } from './components/Canvas';
export { LayerPanel } from './components/LayerPanel';
export { NetPanel } from './components/NetPanel';
export { Inspector } from './components/Inspector';
export { Toolbar } from './components/Toolbar';
export { DiffSummary } from './components/DiffSummary';

// Context and hooks for advanced usage
export { PcbViewerProvider, usePcbViewer } from './context/PcbViewerContext';
export { useCanvasRenderer } from './hooks/useCanvasRenderer';

// Types
export type {
  // Main types
  PcbViewerProps,
  PcbData,
  PcbDiffData,
  ViewerMode,

  // Element types
  PcbElement,
  Footprint,
  Segment,
  Via,
  GraphicLine,
  Arc,
  Zone,
  Pad,

  // Metadata types
  NetInfo,
  LayerInfo,
  BoundingBox,

  // State types
  ViewState,
  SelectionState,
  LayerVisibility,

  // Diff types
  DiffStatus,
  DiffElement,

  // Theme types
  PcbViewerTheme,
} from './types/pcb';

// Default themes
export { defaultDarkTheme, defaultLightTheme } from './types/pcb';

// Styles (can be imported separately for customization)
// import '@atopile/pcb-viewer/styles/theme.css';
// import '@atopile/pcb-viewer/styles/components.css';
