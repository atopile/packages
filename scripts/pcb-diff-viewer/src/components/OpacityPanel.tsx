/**
 * Opacity Panel - Sliders to control opacity of different board elements
 */

import { usePcbViewer, type OpacitySettings } from '../context/PcbViewerContext';

interface OpacitySliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  icon?: string;
}

function OpacitySlider({ label, value, onChange, icon }: OpacitySliderProps) {
  return (
    <div className="pcb-opacity-slider">
      <div className="pcb-opacity-slider__header">
        {icon && <span className="pcb-opacity-slider__icon">{icon}</span>}
        <span className="pcb-opacity-slider__label">{label}</span>
        <span className="pcb-opacity-slider__value">{Math.round(value * 100)}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={value * 100}
        onChange={(e) => onChange(Number(e.target.value) / 100)}
        className="pcb-opacity-slider__input"
      />
    </div>
  );
}

export function OpacityPanel() {
  const { state, setOpacity } = usePcbViewer();
  const { opacity } = state;

  const handleChange = (key: keyof OpacitySettings) => (value: number) => {
    setOpacity({ [key]: value });
  };

  return (
    <div className="pcb-panel">
      <div className="pcb-panel__header">
        <span>Opacity</span>
      </div>
      <div className="pcb-panel__content" style={{ padding: '12px' }}>
        <OpacitySlider
          label="Zones"
          icon="▦"
          value={opacity.zones}
          onChange={handleChange('zones')}
        />
        <OpacitySlider
          label="Tracks"
          icon="╱"
          value={opacity.tracks}
          onChange={handleChange('tracks')}
        />
        <OpacitySlider
          label="Pads"
          icon="⬜"
          value={opacity.pads}
          onChange={handleChange('pads')}
        />
        <OpacitySlider
          label="Vias"
          icon="◉"
          value={opacity.vias}
          onChange={handleChange('vias')}
        />
        <OpacitySlider
          label="Silkscreen"
          icon="T"
          value={opacity.silkscreen}
          onChange={handleChange('silkscreen')}
        />
        <OpacitySlider
          label="Board Edge"
          icon="▢"
          value={opacity.boardOutline}
          onChange={handleChange('boardOutline')}
        />
      </div>
    </div>
  );
}
