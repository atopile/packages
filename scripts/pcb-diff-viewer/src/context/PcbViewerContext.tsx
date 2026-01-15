/**
 * PCB Viewer Context - Shared state for all viewer components
 */

import { createContext, useContext, useReducer, useCallback, type ReactNode } from 'react';
import type {
  PcbData,
  PcbDiffData,
  PcbElement,
  ViewState,
  LayerVisibility,
  ViewerMode
} from '../types/pcb';

// ============================================================================
// State Types
// ============================================================================

export type ColorMode = 'layer' | 'net';

interface PcbViewerState {
  // Data
  mode: ViewerMode;
  pcbData: PcbData | null;
  diffData: PcbDiffData | null;

  // View
  view: ViewState;
  layerVisibility: LayerVisibility;
  colorMode: ColorMode;

  // Selection
  hoveredElement: PcbElement | null;
  selectedElement: PcbElement | null;
  highlightedNet: number | null;

  // UI
  showDiffOverlay: boolean;
  showBeforeState: boolean;
  showAfterState: boolean;
}

type PcbViewerAction =
  | { type: 'SET_DATA'; payload: { mode: ViewerMode; pcbData?: PcbData; diffData?: PcbDiffData } }
  | { type: 'SET_MODE'; payload: ViewerMode }
  | { type: 'SET_VIEW'; payload: Partial<ViewState> }
  | { type: 'ZOOM'; payload: { delta: number; centerX: number; centerY: number } }
  | { type: 'PAN'; payload: { deltaX: number; deltaY: number } }
  | { type: 'FIT_VIEW' }
  | { type: 'SET_LAYER_VISIBILITY'; payload: { layer: string; visible: boolean } }
  | { type: 'TOGGLE_ALL_LAYERS'; payload: boolean }
  | { type: 'SET_HOVERED'; payload: PcbElement | null }
  | { type: 'SET_SELECTED'; payload: PcbElement | null }
  | { type: 'HIGHLIGHT_NET'; payload: number | null }
  | { type: 'SET_COLOR_MODE'; payload: ColorMode }
  | { type: 'TOGGLE_DIFF_OVERLAY' }
  | { type: 'TOGGLE_BEFORE_STATE' }
  | { type: 'TOGGLE_AFTER_STATE' };

// ============================================================================
// Initial State
// ============================================================================

const initialState: PcbViewerState = {
  mode: 'single',
  pcbData: null,
  diffData: null,
  view: {
    zoom: 50,
    panX: 0,
    panY: 0,
  },
  layerVisibility: {},
  colorMode: 'layer',
  hoveredElement: null,
  selectedElement: null,
  highlightedNet: null,
  showDiffOverlay: true,
  showBeforeState: true,
  showAfterState: true,
};

// ============================================================================
// Reducer
// ============================================================================

function pcbViewerReducer(state: PcbViewerState, action: PcbViewerAction): PcbViewerState {
  switch (action.type) {
    case 'SET_DATA': {
      const { mode, pcbData, diffData } = action.payload;

      // Initialize layer visibility from data
      const layers = pcbData?.layers || diffData?.after.layers || {};
      const layerVisibility: LayerVisibility = {};
      Object.keys(layers).forEach(layer => {
        layerVisibility[layer] = true;
      });

      // When loading diff data, also set pcbData to "after" for single view mode
      const effectivePcbData = pcbData || (diffData ? diffData.after : null);

      return {
        ...state,
        mode,
        pcbData: effectivePcbData,
        diffData: diffData || null,
        layerVisibility,
      };
    }

    case 'SET_MODE':
      return {
        ...state,
        mode: action.payload,
        // When switching to single mode with diff data, use "after" as pcbData
        pcbData: action.payload === 'single' && state.diffData ? state.diffData.after : state.pcbData,
      };

    case 'SET_VIEW':
      return {
        ...state,
        view: { ...state.view, ...action.payload },
      };

    case 'ZOOM': {
      // centerX/centerY are offsets from canvas center (mouse position - canvas center)
      const { delta, centerX, centerY } = action.payload;
      const newZoom = Math.max(5, Math.min(500, state.view.zoom * (1 + delta * 0.001)));
      const zoomRatio = newZoom / state.view.zoom;

      // Zoom toward cursor: adjust pan so the PCB point under cursor stays fixed
      // The point at canvas offset (offsetX, offsetY) from center corresponds to:
      //   pcbPoint = (offsetX - panX) / zoom
      // After zoom, to keep the same pcbPoint at the same canvas position:
      //   offsetX - newPanX = pcbPoint * newZoom
      //   newPanX = offsetX - pcbPoint * newZoom
      //          = offsetX - (offsetX - panX) / zoom * newZoom
      //          = offsetX - (offsetX - panX) * zoomRatio
      //          = offsetX * (1 - zoomRatio) + panX * zoomRatio
      const newPanX = state.view.panX * zoomRatio + centerX * (1 - zoomRatio);
      const newPanY = state.view.panY * zoomRatio + centerY * (1 - zoomRatio);

      return {
        ...state,
        view: {
          ...state.view,
          zoom: newZoom,
          panX: newPanX,
          panY: newPanY,
        },
      };
    }

    case 'PAN':
      return {
        ...state,
        view: {
          ...state.view,
          panX: state.view.panX + action.payload.deltaX,
          panY: state.view.panY + action.payload.deltaY,
        },
      };

    case 'FIT_VIEW': {
      // Will be implemented with canvas dimensions
      return state;
    }

    case 'SET_LAYER_VISIBILITY':
      return {
        ...state,
        layerVisibility: {
          ...state.layerVisibility,
          [action.payload.layer]: action.payload.visible,
        },
      };

    case 'TOGGLE_ALL_LAYERS': {
      const newVisibility: LayerVisibility = {};
      Object.keys(state.layerVisibility).forEach(layer => {
        newVisibility[layer] = action.payload;
      });
      return {
        ...state,
        layerVisibility: newVisibility,
      };
    }

    case 'SET_HOVERED':
      return { ...state, hoveredElement: action.payload };

    case 'SET_SELECTED':
      return { ...state, selectedElement: action.payload };

    case 'HIGHLIGHT_NET':
      return { ...state, highlightedNet: action.payload };

    case 'SET_COLOR_MODE':
      return { ...state, colorMode: action.payload };

    case 'TOGGLE_DIFF_OVERLAY':
      return { ...state, showDiffOverlay: !state.showDiffOverlay };

    case 'TOGGLE_BEFORE_STATE':
      return { ...state, showBeforeState: !state.showBeforeState };

    case 'TOGGLE_AFTER_STATE':
      return { ...state, showAfterState: !state.showAfterState };

    default:
      return state;
  }
}

// ============================================================================
// Context
// ============================================================================

interface PcbViewerContextType {
  state: PcbViewerState;
  dispatch: React.Dispatch<PcbViewerAction>;
  // Convenience actions
  setView: (view: Partial<ViewState>) => void;
  zoom: (delta: number, centerX: number, centerY: number) => void;
  pan: (deltaX: number, deltaY: number) => void;
  setLayerVisible: (layer: string, visible: boolean) => void;
  toggleAllLayers: (visible: boolean) => void;
  setHovered: (element: PcbElement | null) => void;
  setSelected: (element: PcbElement | null) => void;
  highlightNet: (net: number | null) => void;
  setColorMode: (mode: ColorMode) => void;
}

const PcbViewerContext = createContext<PcbViewerContextType | null>(null);

// ============================================================================
// Provider
// ============================================================================

interface PcbViewerProviderProps {
  children: ReactNode;
  initialState?: Partial<PcbViewerState>;
}

export function PcbViewerProvider({ children, initialState: customInitial }: PcbViewerProviderProps) {
  const [state, dispatch] = useReducer(
    pcbViewerReducer,
    { ...initialState, ...customInitial }
  );

  const setView = useCallback((view: Partial<ViewState>) => {
    dispatch({ type: 'SET_VIEW', payload: view });
  }, []);

  const zoom = useCallback((delta: number, centerX: number, centerY: number) => {
    dispatch({ type: 'ZOOM', payload: { delta, centerX, centerY } });
  }, []);

  const pan = useCallback((deltaX: number, deltaY: number) => {
    dispatch({ type: 'PAN', payload: { deltaX, deltaY } });
  }, []);

  const setLayerVisible = useCallback((layer: string, visible: boolean) => {
    dispatch({ type: 'SET_LAYER_VISIBILITY', payload: { layer, visible } });
  }, []);

  const toggleAllLayers = useCallback((visible: boolean) => {
    dispatch({ type: 'TOGGLE_ALL_LAYERS', payload: visible });
  }, []);

  const setHovered = useCallback((element: PcbElement | null) => {
    dispatch({ type: 'SET_HOVERED', payload: element });
  }, []);

  const setSelected = useCallback((element: PcbElement | null) => {
    dispatch({ type: 'SET_SELECTED', payload: element });
  }, []);

  const highlightNet = useCallback((net: number | null) => {
    dispatch({ type: 'HIGHLIGHT_NET', payload: net });
  }, []);

  const setColorMode = useCallback((mode: ColorMode) => {
    dispatch({ type: 'SET_COLOR_MODE', payload: mode });
  }, []);

  return (
    <PcbViewerContext.Provider value={{
      state,
      dispatch,
      setView,
      zoom,
      pan,
      setLayerVisible,
      toggleAllLayers,
      setHovered,
      setSelected,
      highlightNet,
      setColorMode,
    }}>
      {children}
    </PcbViewerContext.Provider>
  );
}

// ============================================================================
// Hook
// ============================================================================

export function usePcbViewer() {
  const context = useContext(PcbViewerContext);
  if (!context) {
    throw new Error('usePcbViewer must be used within a PcbViewerProvider');
  }
  return context;
}
