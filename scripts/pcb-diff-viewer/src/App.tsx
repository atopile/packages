/**
 * PCB Viewer Demo App
 *
 * This is a standalone demo application that shows how to use the PcbViewer component.
 * It can load PCB data from a JSON file served by the Python backend.
 */

import { useState, useEffect } from 'react';
import { PcbViewer } from './components/PcbViewer';
import type { PcbData, PcbDiffData } from './types/pcb';

function App() {
  const [data, setData] = useState<PcbData | null>(null);
  const [diffData, setDiffData] = useState<PcbDiffData | null>(null);
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

  if (loading) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#1e1e2e',
        color: '#cdd6f4',
        fontFamily: 'system-ui, sans-serif',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '32px', marginBottom: '16px' }}>⏳</div>
          <div>Loading PCB data...</div>
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
        background: '#1e1e2e',
        color: '#cdd6f4',
        fontFamily: 'system-ui, sans-serif',
        padding: '32px',
      }}>
        <div style={{
          textAlign: 'center',
          maxWidth: '500px',
          background: '#313244',
          padding: '32px',
          borderRadius: '12px',
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
          <div style={{ marginBottom: '16px', color: '#f38ba8' }}>{error}</div>
          <div style={{ fontSize: '14px', color: '#6c7086' }}>
            To use the PCB Viewer, run the Python backend:
            <pre style={{
              background: '#1e1e2e',
              padding: '12px',
              borderRadius: '8px',
              marginTop: '12px',
              fontSize: '12px',
              textAlign: 'left',
            }}>
              cd pcb_diff_poc{'\n'}
              python pcb_diff.py before.kicad_pcb after.kicad_pcb
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
