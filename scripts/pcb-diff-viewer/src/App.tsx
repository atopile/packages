/**
 * PCB Viewer Demo App
 *
 * This is a standalone demo application that shows how to use the PcbViewer component.
 * It can load PCB data from a JSON file served by the Python backend.
 */

import { useState, useEffect } from 'react';
import { PcbViewer } from './components/PcbViewer';
import type { PcbData, PcbDiffData, BusData } from './types/pcb';

// atopile brand colors
const colors = {
  orange: '#f95015',
  orangeGlow: 'rgba(249, 80, 21, 0.15)',
  navy: '#070a23',
  navyLight: '#0e1338',
  text: '#cdd6f4',
  textMuted: '#6c7086',
  error: '#f38ba8',
  surface: '#313244',
};

function App() {
  const [data, setData] = useState<PcbData | null>(null);
  const [diffData, setDiffData] = useState<PcbDiffData | null>(null);
  const [busData, setBusData] = useState<BusData | null>(null);
  const [mode, setMode] = useState<'single' | 'diff'>('single');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load data on mount
  useEffect(() => {
    async function loadData() {
      // Try to load single PCB data from static file first
      try {
        const staticPcb = await fetch('/pcb_data.json');
        if (staticPcb.ok) {
          const pcbJson = await staticPcb.json();
          setData(pcbJson);
          setMode('single');
          setLoading(false);
          return;
        }
      } catch {
        // Ignore - try other sources
      }

      // Try to load diff data from static file (works in Vite dev)
      try {
        const staticDiff = await fetch('/diff_result.json');
        if (staticDiff.ok) {
          const diffJson = await staticDiff.json();
          setDiffData(diffJson);
          setMode('diff');
          setLoading(false);
          return;
        }
      } catch {
        // Ignore - try other sources
      }

      // Try API endpoints (works when running Python backend)
      try {
        const diffResponse = await fetch('/api/diff');
        if (diffResponse.ok) {
          const diffJson = await diffResponse.json();
          setDiffData(diffJson);
          setMode('diff');
          setLoading(false);
          return;
        }
      } catch {
        // Ignore - try other sources
      }

      try {
        const singleResponse = await fetch('/api/pcb');
        if (singleResponse.ok) {
          const pcbJson = await singleResponse.json();
          setData(pcbJson);
          setMode('single');
          setLoading(false);
          return;
        }
      } catch {
        // Ignore
      }

      // Demo mode with no data
      setError('No PCB data found. Run the Python backend to generate data.');
      setLoading(false);
    }

    loadData();
  }, []);

  // Load bus data separately (optional, only when available from atopile)
  useEffect(() => {
    async function loadBusData() {
      try {
        const response = await fetch('/api/buses');
        if (response.ok) {
          const busJson = await response.json();
          setBusData(busJson);
          console.log(`Loaded ${Object.keys(busJson.buses || {}).length} buses from atopile design`);
        }
      } catch {
        // Bus data is optional - ignore errors
      }
    }

    loadBusData();
  }, []);

  if (loading) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `
          radial-gradient(ellipse 1200px 900px at 10% -5%, ${colors.orangeGlow} 0%, transparent 50%),
          radial-gradient(ellipse 900px 700px at 90% -5%, rgba(137, 180, 250, 0.06) 0%, transparent 50%),
          ${colors.navy}
        `,
        color: colors.text,
        fontFamily: "'Inter', system-ui, sans-serif",
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: `3px solid ${colors.surface}`,
            borderTopColor: colors.orange,
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
            margin: '0 auto 16px',
          }} />
          <div style={{ color: colors.textMuted }}>Loading PCB data...</div>
          <style>{`
            @keyframes spin { to { transform: rotate(360deg); } }
          `}</style>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `
          radial-gradient(ellipse 1200px 900px at 10% -5%, ${colors.orangeGlow} 0%, transparent 50%),
          radial-gradient(ellipse 900px 700px at 90% -5%, rgba(137, 180, 250, 0.06) 0%, transparent 50%),
          ${colors.navy}
        `,
        color: colors.text,
        fontFamily: "'Inter', system-ui, sans-serif",
        padding: '32px',
      }}>
        <div style={{
          textAlign: 'center',
          maxWidth: '500px',
          background: colors.navyLight,
          padding: '40px',
          borderRadius: '16px',
          border: '1px solid rgba(255, 255, 255, 0.06)',
          boxShadow: '0 14px 50px rgba(7, 10, 35, 0.55)',
        }}>
          <div style={{
            width: '64px',
            height: '64px',
            background: 'rgba(243, 139, 168, 0.1)',
            borderRadius: '50%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 20px',
            fontSize: '28px',
          }}>
            ⚠️
          </div>
          <div style={{
            marginBottom: '16px',
            color: colors.error,
            fontWeight: 600,
            fontSize: '15px',
          }}>
            {error}
          </div>
          <div style={{ fontSize: '13px', color: colors.textMuted }}>
            To use the PCB Viewer, run the Python backend:
            <pre style={{
              background: colors.navy,
              padding: '16px',
              borderRadius: '10px',
              marginTop: '16px',
              fontSize: '12px',
              textAlign: 'left',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              fontFamily: "'JetBrains Mono', monospace",
              lineHeight: 1.6,
            }}>
              <span style={{ color: colors.textMuted }}>$</span> cd backend{'\n'}
              <span style={{ color: colors.textMuted }}>$</span> python pcb_server.py <span style={{ color: colors.orange }}>path/to/your.kicad_pcb</span>
            </pre>
          </div>
        </div>
      </div>
    );
  }

  return (
    <PcbViewer
      data={mode === 'single' ? data ?? undefined : undefined}
      diffData={mode === 'diff' ? diffData ?? undefined : undefined}
      busData={busData ?? undefined}
      mode={mode}
      width="100vw"
      height="100vh"
      showLayerPanel={true}
      showNetPanel={true}
      showInspector={true}
      showToolbar={true}
      onElementSelect={(element) => {
        console.log('Selected:', element);
      }}
      onNetHighlight={(net) => {
        console.log('Highlighted net:', net);
      }}
    />
  );
}

export default App;
