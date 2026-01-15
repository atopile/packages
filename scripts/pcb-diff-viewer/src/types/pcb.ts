/**
 * PCB Viewer - Core Types
 *
 * This is a reusable PCB viewer component that can be embedded in:
 * - Package review station
 * - VS Code extension webview
 * - atopile website
 * - Any React application
 *
 * Supports:
 * - Single PCB viewing
 * - Side-by-side comparison
 * - Diff overlay mode
 */

// ============================================================================
// Geometry Types
// ============================================================================

export interface Point {
  x: number;
  y: number;
}

export interface PointWithRotation extends Point {
  r: number;
}

export interface Size {
  w: number;
  h: number;
}

export interface BoundingBox {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
}

// ============================================================================
// PCB Element Types
// ============================================================================

export interface Pad {
  name: string;
  type: string | null;
  at: PointWithRotation;
  size: Size | null;
  shape: string | null;
  layers: string[];
  net: number | null;
  netName: string | null;
}

/** Graphics element within a footprint (lines, rects, circles, arcs) */
export interface FootprintGraphic {
  type: 'line' | 'rect' | 'circle' | 'arc';
  layer: string;
  start?: Point;
  end?: Point;
  mid?: Point | null;
  center?: Point;
  width: number;
}

export interface Footprint {
  type: 'footprint';
  uuid: string;
  name: string;
  reference: string | null;
  value: string | null;
  at: PointWithRotation;
  layer: string;
  pads: Pad[];
  graphics: FootprintGraphic[];
}

export interface Segment {
  type: 'segment';
  uuid: string;
  start: Point;
  end: Point;
  width: number;
  layer: string;
  net: number;
}

export interface Via {
  type: 'via';
  uuid: string;
  at: Point;
  size: number;
  drill: number;
  layers: string[];
  net: number;
}

export interface GraphicLine {
  type: 'gr_line';
  uuid: string | null;
  start: Point;
  end: Point;
  layer: string;
  strokeWidth: number | null;
}

export interface Arc {
  type: 'arc';
  uuid: string | null;
  start: Point;
  mid: Point | null;
  end: Point;
  width: number | null;
  layer: string;
  net: number | null;
}

export interface FilledPolygon {
  layer: string;
  points: Point[];
}

export interface Zone {
  type: 'zone';
  uuid: string | null;
  name: string | null;
  net: number;
  netName: string | null;
  layer: string | null;
  layers: string[];
  priority: number;
  outline: Point[];
  filledPolygons: FilledPolygon[];
}

export interface PcbText {
  type: 'text';
  uuid: string | null;
  text: string;
  textType: string; // 'reference', 'value', 'user', 'graphic'
  at: PointWithRotation;
  layer: string;
  hide: boolean;
  fontSize: number;
  fontThickness: number;
  footprintRef: string | null;
}

export type PcbElement = Footprint | Segment | Via | GraphicLine | Arc | Zone | PcbText;

// ============================================================================
// PCB Metadata
// ============================================================================

export interface NetInfo {
  number: number;
  name: string;
}

export interface LayerInfo {
  number: number;
  name: string;
  type: string | null;
  alias: string | null;
}

// ============================================================================
// Bus/Interface Types (from atopile design)
// ============================================================================

/** Known bus/interface types in atopile designs */
export type BusType =
  | 'ElectricPower'
  | 'I2C'
  | 'SPI'
  | 'I2S'
  | 'UART'
  | 'USB'
  | 'DifferentialPair'
  | 'ElectricLogic'
  | 'ElectricSignal'
  | 'CAN'
  | 'Ethernet'
  | 'Unknown';

/** Information about a bus/interface instance */
export interface BusInfo {
  id: string;
  type: BusType;
  instance: string;
  nets: { name: string }[];
  color: string;
}

/** Bus data from atopile design extraction */
export interface BusData {
  buses: Record<string, BusInfo>;
  net_to_bus: Record<string, string>;
  bus_colors: Record<BusType, string>;
}

// ============================================================================
// PCB Data (loaded from .kicad_pcb file)
// ============================================================================

export interface PcbData {
  filename?: string;
  bounds: BoundingBox;
  nets: Record<number, NetInfo>;
  layers: Record<string, LayerInfo>;
  elements: {
    footprints: Footprint[];
    segments: Segment[];
    vias: Via[];
    graphicLines: GraphicLine[];
    arcs: Arc[];
    zones: Zone[];
    texts: PcbText[];
  };
}

// ============================================================================
// Diff Types (for comparison mode)
// ============================================================================

export type DiffStatus = 'unchanged' | 'added' | 'removed' | 'modified';

export interface DiffElement<T extends PcbElement> {
  status: DiffStatus;
  element: T;
  /** For modified elements, this is the element from the other file */
  counterpart?: T;
}

export interface PcbDiffData {
  before: PcbData;
  after: PcbData;
  diff: {
    footprints: DiffElement<Footprint>[];
    segments: DiffElement<Segment>[];
    vias: DiffElement<Via>[];
    graphicLines: DiffElement<GraphicLine>[];
    arcs: DiffElement<Arc>[];
    zones: DiffElement<Zone>[];
    texts: DiffElement<PcbText>[];
  };
}

// ============================================================================
// Viewer State Types
// ============================================================================

export interface ViewState {
  zoom: number;
  panX: number;
  panY: number;
}

export interface SelectionState {
  hoveredElement: PcbElement | null;
  selectedElement: PcbElement | null;
  highlightedNet: number | null;
}

export interface LayerVisibility {
  [layerName: string]: boolean;
}

// ============================================================================
// Component Props
// ============================================================================

export type ViewerMode = 'single' | 'diff' | 'side-by-side';

export interface PcbViewerTheme {
  background: string;
  // Copper layers
  copperFront: string;
  copperBack: string;
  copperInner: string;
  // Silkscreen
  silkscreenFront: string;
  silkscreenBack: string;
  // Mask
  maskFront: string;
  maskBack: string;
  // Board
  boardEdge: string;
  boardFill: string;
  // Selection/highlighting
  highlight: string;
  selected: string;
  hovered: string;
  // Diff colors
  diffUnchanged: string;
  diffAdded: string;
  diffRemoved: string;
  diffModifiedBefore: string;
  diffModifiedAfter: string;
  // UI
  text: string;
  textMuted: string;
  panel: string;
  panelBorder: string;
}

export interface PcbViewerProps {
  /** Single PCB data for 'single' mode */
  data?: PcbData;
  /** Diff data for 'diff' mode */
  diffData?: PcbDiffData;
  /** Bus/interface data from atopile design (optional) */
  busData?: BusData;
  /** Before/after PCB data for 'side-by-side' mode */
  compareData?: { before: PcbData; after: PcbData };
  /** Viewer mode */
  mode?: ViewerMode;
  /** Initial view state (zoom, pan) */
  initialView?: Partial<ViewState>;
  /** Initial layer visibility */
  initialLayers?: LayerVisibility;
  /** Theme customization */
  theme?: Partial<PcbViewerTheme>;
  /** Whether to show the layer panel */
  showLayerPanel?: boolean;
  /** Whether to show the net panel */
  showNetPanel?: boolean;
  /** Whether to show the inspector panel */
  showInspector?: boolean;
  /** Whether to show the toolbar */
  showToolbar?: boolean;
  /** Callback when an element is selected */
  onElementSelect?: (element: PcbElement | null) => void;
  /** Callback when an element is hovered */
  onElementHover?: (element: PcbElement | null) => void;
  /** Callback when a net is highlighted */
  onNetHighlight?: (netNumber: number | null) => void;
  /** Callback when view changes (zoom/pan) */
  onViewChange?: (view: ViewState) => void;
  /** Additional CSS class */
  className?: string;
  /** Inline styles */
  style?: React.CSSProperties;
  /** Width (default: 100%) */
  width?: string | number;
  /** Height (default: 100%) */
  height?: string | number;
}

// ============================================================================
// Default Theme
// ============================================================================

export const defaultDarkTheme: PcbViewerTheme = {
  background: '#1e1e2e',
  copperFront: '#f38ba8',
  copperBack: '#89b4fa',
  copperInner: '#a6e3a1',
  silkscreenFront: '#f5e0dc',
  silkscreenBack: '#b4befe',
  maskFront: '#45475a80',
  maskBack: '#31324480',
  boardEdge: '#cdd6f4',
  boardFill: '#313244',
  highlight: '#f9e2af',
  selected: '#fab387',
  hovered: '#94e2d5',
  diffUnchanged: '#585b70',
  diffAdded: '#a6e3a1',
  diffRemoved: '#f38ba8',
  diffModifiedBefore: '#fab387',
  diffModifiedAfter: '#89b4fa',
  text: '#cdd6f4',
  textMuted: '#6c7086',
  panel: '#313244',
  panelBorder: '#45475a',
};

export const defaultLightTheme: PcbViewerTheme = {
  background: '#eff1f5',
  copperFront: '#d20f39',
  copperBack: '#1e66f5',
  copperInner: '#40a02b',
  silkscreenFront: '#4c4f69',
  silkscreenBack: '#7287fd',
  maskFront: '#9ca0b080',
  maskBack: '#bcc0cc80',
  boardEdge: '#4c4f69',
  boardFill: '#e6e9ef',
  highlight: '#df8e1d',
  selected: '#fe640b',
  hovered: '#179299',
  diffUnchanged: '#9ca0b0',
  diffAdded: '#40a02b',
  diffRemoved: '#d20f39',
  diffModifiedBefore: '#fe640b',
  diffModifiedAfter: '#1e66f5',
  text: '#4c4f69',
  textMuted: '#8c8fa1',
  panel: '#e6e9ef',
  panelBorder: '#ccd0da',
};
