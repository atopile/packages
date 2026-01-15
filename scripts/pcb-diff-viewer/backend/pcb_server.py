#!/usr/bin/env python3
"""
PCB Viewer Backend Server

Uses atopile's KiCad parser to load PCB files and serve them
to the React frontend via a simple HTTP API.

Usage:
    # Single PCB viewing
    python pcb_server.py my_board.kicad_pcb

    # Diff mode
    python pcb_server.py --before old.kicad_pcb --after new.kicad_pcb

    # With custom port
    python pcb_server.py --port 3001 my_board.kicad_pcb
"""

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# Add atopile to path
ATOPILE_SRC = Path(__file__).parent.parent.parent.parent.parent / "atopile" / "src"
sys.path.insert(0, str(ATOPILE_SRC))

from faebryk.libs.kicad.fileformats import kicad


# ============================================================================
# Helpers
# ============================================================================

def enum_to_str(val) -> str | None:
    """Safely convert enum or string to string.

    For enums that inherit from str (like E_pad_shape), prefer .value
    which gives the lowercase string representation.
    """
    if val is None:
        return None
    # For str-based enums, value is the actual string we want
    if hasattr(val, 'value') and isinstance(val.value, str):
        return val.value
    # Fallback to name for other enum types
    if hasattr(val, 'name'):
        return val.name
    return str(val)


# ============================================================================
# Data Extraction
# ============================================================================

def extract_bounds(kicad_pcb) -> dict:
    """Calculate bounding box from all elements."""
    min_x, min_y = float('inf'), float('inf')
    max_x, max_y = float('-inf'), float('-inf')

    def update_bounds(x, y):
        nonlocal min_x, min_y, max_x, max_y
        min_x = min(min_x, x)
        min_y = min(min_y, y)
        max_x = max(max_x, x)
        max_y = max(max_y, y)

    # Footprints
    for fp in kicad_pcb.footprints:
        update_bounds(fp.at.x, fp.at.y)
        for pad in fp.pads:
            px = fp.at.x + pad.at.x
            py = fp.at.y + pad.at.y
            update_bounds(px, py)

    # Segments
    for seg in kicad_pcb.segments:
        update_bounds(seg.start.x, seg.start.y)
        update_bounds(seg.end.x, seg.end.y)

    # Vias
    for via in kicad_pcb.vias:
        update_bounds(via.at.x, via.at.y)

    # Graphic lines
    for line in kicad_pcb.gr_lines:
        update_bounds(line.start.x, line.start.y)
        update_bounds(line.end.x, line.end.y)

    # Add some padding
    padding = 5
    return {
        "minX": min_x - padding if min_x != float('inf') else 0,
        "minY": min_y - padding if min_y != float('inf') else 0,
        "maxX": max_x + padding if max_x != float('-inf') else 100,
        "maxY": max_y + padding if max_y != float('-inf') else 100,
    }


def extract_layers(kicad_pcb) -> dict:
    """Extract layer definitions from PCB."""
    layers = {}
    for layer in kicad_pcb.layers:
        layers[layer.name] = {
            "number": layer.number,
            "name": layer.name,
            "type": enum_to_str(layer.type),
            "alias": layer.alias,
        }
    return layers


def extract_nets(kicad_pcb) -> dict:
    """Extract net definitions from PCB."""
    nets = {}
    for net in kicad_pcb.nets:
        nets[net.number] = {
            "number": net.number,
            "name": net.name or "",
        }
    return nets


def extract_footprint(fp) -> dict:
    """Extract footprint data."""
    # Find reference and value properties
    reference = None
    value = None
    for prop in getattr(fp, 'properties', []):
        if prop.name == "Reference":
            reference = prop.value
        elif prop.name == "Value":
            value = prop.value

    return {
        "type": "footprint",
        "uuid": fp.uuid,
        "name": fp.name,
        "reference": reference,
        "value": value,
        "at": {"x": fp.at.x, "y": fp.at.y, "r": getattr(fp.at, 'r', 0) or 0},
        "layer": fp.layer,
        "pads": [
            {
                "name": p.name,
                "type": enum_to_str(p.type),
                "at": {"x": p.at.x, "y": p.at.y, "r": getattr(p.at, 'r', 0) or 0},
                "size": {"w": p.size.w, "h": p.size.h or p.size.w} if p.size else None,
                "shape": enum_to_str(p.shape),
                "layers": list(p.layers) if p.layers else [],
                "net": p.net.number if p.net else None,
                "netName": p.net.name if p.net else None,
            }
            for p in fp.pads
        ],
    }


def extract_segment(seg) -> dict:
    """Extract segment (trace) data."""
    return {
        "type": "segment",
        "uuid": seg.uuid,
        "start": {"x": seg.start.x, "y": seg.start.y},
        "end": {"x": seg.end.x, "y": seg.end.y},
        "width": seg.width,
        "layer": seg.layer,
        "net": seg.net,
    }


def extract_via(via) -> dict:
    """Extract via data."""
    return {
        "type": "via",
        "uuid": via.uuid,
        "at": {"x": via.at.x, "y": via.at.y},
        "size": via.size,
        "drill": via.drill,
        "layers": list(via.layers) if via.layers else [],
        "net": via.net,
    }


def extract_gr_line(line) -> dict:
    """Extract graphic line data."""
    return {
        "type": "gr_line",
        "uuid": getattr(line, 'uuid', None),
        "start": {"x": line.start.x, "y": line.start.y},
        "end": {"x": line.end.x, "y": line.end.y},
        "layer": line.layer,
        "strokeWidth": line.stroke.width if line.stroke else None,
    }


def extract_arc(arc) -> dict:
    """Extract arc data."""
    return {
        "type": "arc",
        "uuid": getattr(arc, 'uuid', None),
        "start": {"x": arc.start.x, "y": arc.start.y},
        "mid": {"x": arc.mid.x, "y": arc.mid.y} if arc.mid else None,
        "end": {"x": arc.end.x, "y": arc.end.y},
        "width": getattr(arc, 'width', None),
        "layer": arc.layer,
        "net": getattr(arc, 'net', None),
    }


def load_pcb(filepath: Path) -> dict:
    """Load a PCB file and extract all data."""
    pcb_file = kicad.loads(kicad.pcb.PcbFile, filepath)
    kicad_pcb = pcb_file.kicad_pcb

    return {
        "filename": filepath.name,
        "bounds": extract_bounds(kicad_pcb),
        "nets": extract_nets(kicad_pcb),
        "layers": extract_layers(kicad_pcb),
        "elements": {
            "footprints": [extract_footprint(fp) for fp in kicad_pcb.footprints],
            "segments": [extract_segment(seg) for seg in kicad_pcb.segments],
            "vias": [extract_via(via) for via in kicad_pcb.vias],
            "graphicLines": [extract_gr_line(line) for line in kicad_pcb.gr_lines],
            "arcs": [extract_arc(arc) for arc in kicad_pcb.arcs],
            "zones": [],  # TODO: Extract zones
        },
    }


# ============================================================================
# Diff Computation
# ============================================================================

def compute_diff(before_data: dict, after_data: dict) -> dict:
    """Compute diff between two PCB files."""

    def diff_elements(before_list: list, after_list: list, key: str = "uuid") -> list:
        """Compare two lists of elements."""
        before_map = {e[key]: e for e in before_list if e.get(key)}
        after_map = {e[key]: e for e in after_list if e.get(key)}

        result = []

        # Find added, removed, and modified
        all_keys = set(before_map.keys()) | set(after_map.keys())

        for k in all_keys:
            in_before = k in before_map
            in_after = k in after_map

            if in_before and not in_after:
                result.append({"status": "removed", "element": before_map[k]})
            elif not in_before and in_after:
                result.append({"status": "added", "element": after_map[k]})
            else:
                # Both exist - check if modified
                before_elem = before_map[k]
                after_elem = after_map[k]

                # Simple comparison - check position for footprints, geometry for traces
                modified = False
                elem_type = before_elem.get("type", "")

                if elem_type == "footprint":
                    if before_elem["at"] != after_elem["at"]:
                        modified = True
                elif elem_type == "segment":
                    if (before_elem["start"] != after_elem["start"] or
                        before_elem["end"] != after_elem["end"]):
                        modified = True
                elif elem_type == "via":
                    if before_elem["at"] != after_elem["at"]:
                        modified = True

                if modified:
                    result.append({
                        "status": "modified",
                        "element": after_elem,
                        "counterpart": before_elem,
                    })
                else:
                    result.append({"status": "unchanged", "element": after_elem})

        return result

    return {
        "before": before_data,
        "after": after_data,
        "diff": {
            "footprints": diff_elements(
                before_data["elements"]["footprints"],
                after_data["elements"]["footprints"]
            ),
            "segments": diff_elements(
                before_data["elements"]["segments"],
                after_data["elements"]["segments"]
            ),
            "vias": diff_elements(
                before_data["elements"]["vias"],
                after_data["elements"]["vias"]
            ),
            "graphicLines": diff_elements(
                before_data["elements"]["graphicLines"],
                after_data["elements"]["graphicLines"]
            ),
            "arcs": diff_elements(
                before_data["elements"]["arcs"],
                after_data["elements"]["arcs"]
            ),
            "zones": [],
        },
    }


# ============================================================================
# HTTP Server
# ============================================================================

class PcbViewerHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves PCB data via API endpoints."""

    pcb_data: dict | None = None
    diff_data: dict | None = None
    static_dir: Path | None = None

    def __init__(self, *args, **kwargs):
        # Set directory for static files
        if self.static_dir:
            super().__init__(*args, directory=str(self.static_dir), **kwargs)
        else:
            super().__init__(*args, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)

        # API endpoints
        if parsed.path == '/api/pcb':
            self.send_json(self.pcb_data)
            return

        if parsed.path == '/api/diff':
            if self.diff_data:
                self.send_json(self.diff_data)
            else:
                self.send_error(404, "No diff data available")
            return

        # Serve static files for everything else
        super().do_GET()

    def send_json(self, data):
        if data is None:
            self.send_error(404, "No data available")
            return

        content = json.dumps(data).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', len(content))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        # Quieter logging
        if '/api/' in str(args[0]):
            print(f"[API] {args[0]}")


def run_server(port: int, pcb_data: dict | None, diff_data: dict | None, static_dir: Path | None):
    """Run the HTTP server."""
    # Configure handler with data
    PcbViewerHandler.pcb_data = pcb_data
    PcbViewerHandler.diff_data = diff_data
    PcbViewerHandler.static_dir = static_dir

    server = HTTPServer(('localhost', port), PcbViewerHandler)
    print(f"🚀 PCB Viewer server running at http://localhost:{port}")
    print(f"   API endpoints:")
    print(f"   - GET /api/pcb   (single PCB data)")
    print(f"   - GET /api/diff  (diff data)")
    print(f"\n   Press Ctrl+C to stop\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped")


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="PCB Viewer Backend Server")
    parser.add_argument('pcb_file', nargs='?', help="Single PCB file to view")
    parser.add_argument('--before', help="Before PCB file for diff mode")
    parser.add_argument('--after', help="After PCB file for diff mode")
    parser.add_argument('--port', type=int, default=3001, help="Server port (default: 3001)")
    parser.add_argument('--output', help="Output JSON file instead of serving")
    parser.add_argument('--static', help="Directory to serve static files from")

    args = parser.parse_args()

    pcb_data = None
    diff_data = None

    # Diff mode
    if args.before and args.after:
        print(f"📂 Loading before: {args.before}")
        before_data = load_pcb(Path(args.before))
        print(f"📂 Loading after: {args.after}")
        after_data = load_pcb(Path(args.after))
        print("🔍 Computing diff...")
        diff_data = compute_diff(before_data, after_data)
        pcb_data = after_data

        # Print summary
        added = sum(1 for d in diff_data["diff"]["footprints"] if d["status"] == "added")
        removed = sum(1 for d in diff_data["diff"]["footprints"] if d["status"] == "removed")
        modified = sum(1 for d in diff_data["diff"]["footprints"] if d["status"] == "modified")
        added += sum(1 for d in diff_data["diff"]["segments"] if d["status"] == "added")
        removed += sum(1 for d in diff_data["diff"]["segments"] if d["status"] == "removed")
        modified += sum(1 for d in diff_data["diff"]["segments"] if d["status"] == "modified")

        print(f"   ✅ {added} added, ❌ {removed} removed, 📝 {modified} modified")

    # Single PCB mode
    elif args.pcb_file:
        print(f"📂 Loading: {args.pcb_file}")
        pcb_data = load_pcb(Path(args.pcb_file))
        print(f"   ✅ {len(pcb_data['elements']['footprints'])} footprints")
        print(f"   ✅ {len(pcb_data['elements']['segments'])} traces")
        print(f"   ✅ {len(pcb_data['elements']['vias'])} vias")

    else:
        parser.print_help()
        return

    # Output to file
    if args.output:
        output_path = Path(args.output)
        data = diff_data if diff_data else pcb_data
        output_path.write_text(json.dumps(data, indent=2))
        print(f"\n💾 Saved to {output_path}")
        return

    # Run server
    static_dir = Path(args.static) if args.static else None
    run_server(args.port, pcb_data, diff_data, static_dir)


if __name__ == "__main__":
    main()
