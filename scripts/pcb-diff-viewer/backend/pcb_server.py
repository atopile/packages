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

    # Extract footprint graphics (lines, rects, circles, arcs) for outline rendering
    # Prioritize courtyard layer, but also include fab and silkscreen
    graphics = []

    # Extract fp_lines
    for line in getattr(fp, 'fp_lines', []):
        layer = line.layer.layer if hasattr(line.layer, 'layer') else str(line.layer)
        graphics.append({
            "type": "line",
            "layer": layer,
            "start": {"x": line.start.x, "y": line.start.y},
            "end": {"x": line.end.x, "y": line.end.y},
            "width": line.stroke.width if hasattr(line, 'stroke') and line.stroke else 0.1,
        })

    # Extract fp_rects
    for rect in getattr(fp, 'fp_rects', []):
        layer = rect.layer.layer if hasattr(rect.layer, 'layer') else str(rect.layer)
        graphics.append({
            "type": "rect",
            "layer": layer,
            "start": {"x": rect.start.x, "y": rect.start.y},
            "end": {"x": rect.end.x, "y": rect.end.y},
            "width": rect.stroke.width if hasattr(rect, 'stroke') and rect.stroke else 0.1,
        })

    # Extract fp_circles
    for circle in getattr(fp, 'fp_circles', []):
        layer = circle.layer.layer if hasattr(circle.layer, 'layer') else str(circle.layer)
        graphics.append({
            "type": "circle",
            "layer": layer,
            "center": {"x": circle.center.x, "y": circle.center.y},
            "end": {"x": circle.end.x, "y": circle.end.y},  # Point on circumference
            "width": circle.stroke.width if hasattr(circle, 'stroke') and circle.stroke else 0.1,
        })

    # Extract fp_arcs
    for arc in getattr(fp, 'fp_arcs', []):
        layer = arc.layer.layer if hasattr(arc.layer, 'layer') else str(arc.layer)
        graphics.append({
            "type": "arc",
            "layer": layer,
            "start": {"x": arc.start.x, "y": arc.start.y},
            "mid": {"x": arc.mid.x, "y": arc.mid.y} if hasattr(arc, 'mid') and arc.mid else None,
            "end": {"x": arc.end.x, "y": arc.end.y},
            "width": arc.stroke.width if hasattr(arc, 'stroke') and arc.stroke else 0.1,
        })

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
        "graphics": graphics,
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
    """Extract arc segment (copper trace arc) data."""
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


def extract_gr_arc(arc) -> dict:
    """Extract graphic arc (board outline, etc.) data."""
    return {
        "type": "arc",
        "uuid": getattr(arc, 'uuid', None),
        "start": {"x": arc.start.x, "y": arc.start.y},
        "mid": {"x": arc.mid.x, "y": arc.mid.y},
        "end": {"x": arc.end.x, "y": arc.end.y},
        "width": arc.stroke.width if arc.stroke else 0.15,
        "layer": arc.layer,
        "net": None,
    }


def extract_zone(zone) -> dict:
    """Extract zone (polygon pour) data."""
    # Get outline polygon points
    outline_points = []
    if zone.polygon and zone.polygon.pts:
        outline_points = [{"x": pt.x, "y": pt.y} for pt in zone.polygon.pts.xys]

    # Get filled polygon points (actual copper after fill)
    filled_polygons = []
    for fp in zone.filled_polygon:
        points = [{"x": pt.x, "y": pt.y} for pt in fp.pts.xys]
        filled_polygons.append({
            "layer": fp.layer,
            "points": points,
        })

    # Get layer(s)
    layer = zone.layer
    if not layer and zone.layers:
        layer = list(zone.layers)[0] if zone.layers else None

    return {
        "type": "zone",
        "uuid": getattr(zone, 'uuid', None),
        "name": getattr(zone, 'name', None),
        "net": zone.net,
        "netName": zone.net_name,
        "layer": layer,
        "layers": list(zone.layers) if zone.layers else [],
        "priority": getattr(zone, 'priority', 0),
        "outline": outline_points,
        "filledPolygons": filled_polygons,
    }


def extract_fp_text(fp_text, footprint) -> dict:
    """Extract footprint text element data (legacy fp_text elements)."""
    # For placeholder text like %R or ${REFERENCE}, skip - we extract from properties instead
    text_content = fp_text.text
    if text_content in ('%R', '${REFERENCE}', '%V', '${VALUE}'):
        return None  # Skip placeholders, we'll get these from properties

    is_hidden = fp_text.hide or False

    # Get layer from nested structure
    layer = fp_text.layer.layer if hasattr(fp_text.layer, 'layer') else str(fp_text.layer)

    # Get font info
    font_size = 1.0
    font_thickness = 0.15
    if fp_text.effects and fp_text.effects.font:
        if fp_text.effects.font.size:
            font_size = fp_text.effects.font.size.w
        if fp_text.effects.font.thickness:
            font_thickness = fp_text.effects.font.thickness

    # Calculate absolute position (footprint position + text offset)
    abs_x = footprint.at.x + fp_text.at.x
    abs_y = footprint.at.y + fp_text.at.y
    # Rotation: add footprint rotation to text rotation
    fp_rotation = getattr(footprint.at, 'r', 0) or 0
    text_rotation = getattr(fp_text.at, 'r', 0) or 0

    return {
        "type": "text",
        "uuid": getattr(fp_text, 'uuid', None),
        "text": text_content,
        "textType": enum_to_str(fp_text.type) if fp_text.type else "user",
        "at": {
            "x": abs_x,
            "y": abs_y,
            "r": fp_rotation + text_rotation,
        },
        "layer": layer,
        "hide": is_hidden,
        "fontSize": font_size,
        "fontThickness": font_thickness,
        "footprintRef": footprint.propertys[0].value if footprint.propertys else None,
    }


def extract_fp_property_text(prop, footprint) -> dict:
    """Extract text from footprint property (Reference, Value, etc.)."""
    # Skip non-text properties or those without position
    if not hasattr(prop, 'at') or prop.at is None:
        return None

    # Get layer - property layer is a string directly
    layer = str(prop.layer) if prop.layer else "F.SilkS"

    # Check if hidden
    is_hidden = prop.hide or False

    # Get font info from effects
    font_size = 1.0
    font_thickness = 0.15
    if hasattr(prop, 'effects') and prop.effects:
        if prop.effects.font and prop.effects.font.size:
            font_size = prop.effects.font.size.w
        if prop.effects.font and prop.effects.font.thickness:
            font_thickness = prop.effects.font.thickness

    # Calculate absolute position (footprint position + property offset)
    abs_x = footprint.at.x + prop.at.x
    abs_y = footprint.at.y + prop.at.y
    # Rotation: add footprint rotation to text rotation
    fp_rotation = getattr(footprint.at, 'r', 0) or 0
    text_rotation = getattr(prop.at, 'r', 0) or 0

    return {
        "type": "text",
        "uuid": getattr(prop, 'uuid', None),
        "text": prop.value,
        "textType": prop.name.lower() if hasattr(prop, 'name') else "property",
        "at": {
            "x": abs_x,
            "y": abs_y,
            "r": fp_rotation + text_rotation,
        },
        "layer": layer,
        "hide": is_hidden,
        "fontSize": font_size,
        "fontThickness": font_thickness,
        "footprintRef": footprint.propertys[0].value if footprint.propertys else None,
    }


def extract_gr_text(gr_text) -> dict:
    """Extract graphic text element data."""
    # Get layer
    layer = gr_text.layer.layer if hasattr(gr_text.layer, 'layer') else str(gr_text.layer)

    # Get font info
    font_size = 1.0
    font_thickness = 0.15
    if gr_text.effects and gr_text.effects.font:
        if gr_text.effects.font.size:
            font_size = gr_text.effects.font.size.w
        if gr_text.effects.font.thickness:
            font_thickness = gr_text.effects.font.thickness

    return {
        "type": "text",
        "uuid": getattr(gr_text, 'uuid', None),
        "text": gr_text.text,
        "textType": "graphic",
        "at": {
            "x": gr_text.at.x,
            "y": gr_text.at.y,
            "r": getattr(gr_text.at, 'r', 0) or 0,
        },
        "layer": layer,
        "hide": getattr(gr_text, 'hide', False) or False,
        "fontSize": font_size,
        "fontThickness": font_thickness,
        "footprintRef": None,
    }


def load_pcb(filepath: Path) -> dict:
    """Load a PCB file and extract all data."""
    pcb_file = kicad.loads(kicad.pcb.PcbFile, filepath)
    kicad_pcb = pcb_file.kicad_pcb

    # Combine copper arcs and graphic arcs
    all_arcs = [extract_arc(arc) for arc in kicad_pcb.arcs]
    all_arcs.extend([extract_gr_arc(arc) for arc in kicad_pcb.gr_arcs])

    # Extract all text elements (footprint texts + property texts + graphic texts)
    all_texts = []
    for fp in kicad_pcb.footprints:
        # Extract legacy fp_text elements (skip placeholders)
        for fp_text in fp.fp_texts:
            text_data = extract_fp_text(fp_text, fp)
            if text_data:  # Skip None (placeholders)
                all_texts.append(text_data)
        # Extract property text (Reference, Value, etc.) - these have their own positions
        for prop in fp.propertys:
            # Only extract Reference and Value as visible text
            if hasattr(prop, 'name') and prop.name in ('Reference', 'Value'):
                prop_text = extract_fp_property_text(prop, fp)
                if prop_text:
                    all_texts.append(prop_text)
    for gr_text in kicad_pcb.gr_texts:
        all_texts.append(extract_gr_text(gr_text))

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
            "arcs": all_arcs,
            "zones": [extract_zone(zone) for zone in kicad_pcb.zones],
            "texts": all_texts,
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
            "zones": diff_elements(
                before_data["elements"]["zones"],
                after_data["elements"]["zones"]
            ),
        },
    }


# ============================================================================
# HTTP Server
# ============================================================================

class PcbViewerHandler(SimpleHTTPRequestHandler):
    """HTTP handler that serves PCB data via API endpoints."""

    pcb_data: dict | None = None
    diff_data: dict | None = None
    bus_data: dict | None = None
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

        if parsed.path == '/api/buses':
            if self.bus_data:
                self.send_json(self.bus_data)
            else:
                self.send_error(404, "No bus data available (run with --ato-project)")
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


def run_server(
    port: int,
    pcb_data: dict | None,
    diff_data: dict | None,
    bus_data: dict | None,
    static_dir: Path | None
):
    """Run the HTTP server."""
    # Configure handler with data
    PcbViewerHandler.pcb_data = pcb_data
    PcbViewerHandler.diff_data = diff_data
    PcbViewerHandler.bus_data = bus_data
    PcbViewerHandler.static_dir = static_dir

    server = HTTPServer(('localhost', port), PcbViewerHandler)
    print(f"🚀 PCB Viewer server running at http://localhost:{port}")
    print(f"   API endpoints:")
    print(f"   - GET /api/pcb   (single PCB data)")
    print(f"   - GET /api/diff  (diff data)")
    if bus_data:
        print(f"   - GET /api/buses (bus/interface data)")
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
    parser.add_argument('--ato-project', help="Atopile project directory for bus extraction")
    parser.add_argument('--ato-build', default='default', help="Atopile build target (default: 'default')")

    args = parser.parse_args()

    pcb_data = None
    diff_data = None
    bus_data = None

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

    # Load bus data from atopile project
    if args.ato_project:
        try:
            from bus_extractor import extract_bus_info
            print(f"🔌 Extracting bus info from: {args.ato_project}")
            bus_data = extract_bus_info(Path(args.ato_project), args.ato_build)
            print(f"   ✅ {len(bus_data['buses'])} buses")
            print(f"   ✅ {len(bus_data['net_to_bus'])} net mappings")
        except Exception as e:
            print(f"   ⚠️ Bus extraction failed: {e}")

    # Output to file
    if args.output:
        output_path = Path(args.output)
        data = diff_data if diff_data else pcb_data
        output_path.write_text(json.dumps(data, indent=2))
        print(f"\n💾 Saved to {output_path}")
        return

    # Run server
    static_dir = Path(args.static) if args.static else None
    run_server(args.port, pcb_data, diff_data, bus_data, static_dir)


if __name__ == "__main__":
    main()
