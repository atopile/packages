#!/usr/bin/env python3
"""
PCB Diff Tool - Uses atopile's KiCad parser to compute and visualize PCB differences.

MVP: Overlay two PCBs with:
- Common/unchanged elements in light grey
- Differences highlighted in orange
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Add atopile to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "atopile" / "src"))

from faebryk.libs.kicad.fileformats import kicad, Property


@dataclass
class DiffResult:
    """Result of comparing two PCB elements."""

    only_in_before: list[dict]  # Elements only in 'before' file (removed)
    only_in_after: list[dict]  # Elements only in 'after' file (added)
    common: list[dict]  # Elements in both files (unchanged)
    modified: list[dict]  # Elements that exist in both but changed position/properties


def extract_footprint_data(fp) -> dict:
    """Extract comparable data from a footprint."""
    # Get reference and value from properties
    reference = None
    value = None
    for prop in fp.propertys:
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
        "at": {"x": fp.at.x, "y": fp.at.y, "r": getattr(fp.at, "r", 0)},
        "layer": fp.layer,
        "pads": [
            {
                "name": p.name,
                "type": str(p.type) if p.type else None,
                "at": {"x": p.at.x, "y": p.at.y, "r": getattr(p.at, "r", 0)},
                # Wh uses w/h not x/y
                "size": {"w": p.size.w, "h": p.size.h} if p.size else None,
                "shape": str(p.shape) if p.shape else None,
                "layers": list(p.layers) if p.layers else [],
                "net": p.net.number if p.net else None,
                "net_name": p.net.name if p.net else None,
            }
            for p in fp.pads
        ],
    }


def extract_segment_data(seg) -> dict:
    """Extract comparable data from a trace segment."""
    return {
        "type": "segment",
        "uuid": seg.uuid,
        "start": {"x": seg.start.x, "y": seg.start.y},
        "end": {"x": seg.end.x, "y": seg.end.y},
        "width": seg.width,
        "layer": seg.layer,
        "net": seg.net,
    }


def extract_via_data(via) -> dict:
    """Extract comparable data from a via."""
    return {
        "type": "via",
        "uuid": via.uuid,
        "at": {"x": via.at.x, "y": via.at.y},
        "size": via.size,
        "drill": via.drill,
        "layers": list(via.layers) if via.layers else [],
        "net": via.net,
    }


def extract_gr_line_data(line) -> dict:
    """Extract comparable data from a graphic line."""
    return {
        "type": "gr_line",
        "uuid": getattr(line, "uuid", None),
        "start": {"x": line.start.x, "y": line.start.y},
        "end": {"x": line.end.x, "y": line.end.y},
        "layer": line.layer,
        "stroke_width": line.stroke.width if line.stroke else None,
    }


def extract_arc_data(arc) -> dict:
    """Extract comparable data from an arc segment."""
    return {
        "type": "arc",
        "uuid": getattr(arc, "uuid", None),
        "start": {"x": arc.start.x, "y": arc.start.y},
        "mid": {"x": arc.mid.x, "y": arc.mid.y} if arc.mid else None,
        "end": {"x": arc.end.x, "y": arc.end.y},
        "width": getattr(arc, "width", None),
        "layer": arc.layer,
        "net": getattr(arc, "net", None),
    }


def extract_pcb_metadata(pcb_file: kicad.pcb.PcbFile) -> dict:
    """Extract metadata like nets and layers from a PCB file."""
    pcb = pcb_file.kicad_pcb

    # Extract nets
    nets = {}
    for net in pcb.nets:
        nets[net.number] = {
            "number": net.number,
            "name": net.name or f"Net {net.number}",
        }

    # Extract layers
    layers = {}
    for layer in pcb.layers:
        layers[layer.name] = {
            "number": layer.number,
            "name": layer.name,
            "type": str(layer.type) if layer.type else None,
            "alias": layer.alias,
        }

    return {
        "nets": nets,
        "layers": layers,
    }


def extract_pcb_elements(pcb_file: kicad.pcb.PcbFile) -> dict[str, list[dict]]:
    """Extract all comparable elements from a PCB file."""
    pcb = pcb_file.kicad_pcb

    elements = {
        "footprints": [extract_footprint_data(fp) for fp in pcb.footprints],
        "segments": [extract_segment_data(seg) for seg in pcb.segments],
        "vias": [extract_via_data(via) for via in pcb.vias],
        "gr_lines": [extract_gr_line_data(line) for line in pcb.gr_lines],
        "arcs": [extract_arc_data(arc) for arc in pcb.arcs],
    }

    return elements


def elements_match(e1: dict, e2: dict, check_position: bool = True) -> bool:
    """Check if two elements match (same UUID or same identity)."""
    # Match by UUID first
    if e1.get("uuid") and e2.get("uuid") and e1["uuid"] == e2["uuid"]:
        return True

    # For segments, match by start/end points (approximately)
    if e1["type"] == "segment" and e2["type"] == "segment":
        if not check_position:
            return False
        # Same start/end within tolerance
        tol = 0.01
        return (
            abs(e1["start"]["x"] - e2["start"]["x"]) < tol
            and abs(e1["start"]["y"] - e2["start"]["y"]) < tol
            and abs(e1["end"]["x"] - e2["end"]["x"]) < tol
            and abs(e1["end"]["y"] - e2["end"]["y"]) < tol
            and e1["layer"] == e2["layer"]
        )

    return False


def elements_equal(e1: dict, e2: dict) -> bool:
    """Check if two elements are exactly equal (same position and properties)."""
    if e1["type"] != e2["type"]:
        return False

    if e1["type"] == "footprint":
        # Check position
        tol = 0.01
        if (
            abs(e1["at"]["x"] - e2["at"]["x"]) > tol
            or abs(e1["at"]["y"] - e2["at"]["y"]) > tol
        ):
            return False
        return True

    if e1["type"] == "segment":
        tol = 0.01
        return (
            abs(e1["start"]["x"] - e2["start"]["x"]) < tol
            and abs(e1["start"]["y"] - e2["start"]["y"]) < tol
            and abs(e1["end"]["x"] - e2["end"]["x"]) < tol
            and abs(e1["end"]["y"] - e2["end"]["y"]) < tol
        )

    # For other types, compare all fields
    return e1 == e2


def compute_diff(
    before_elements: dict[str, list[dict]], after_elements: dict[str, list[dict]]
) -> dict[str, DiffResult]:
    """Compute the diff between two sets of PCB elements."""
    results = {}

    for element_type in before_elements.keys():
        before_list = before_elements.get(element_type, [])
        after_list = after_elements.get(element_type, [])

        only_in_before = []
        only_in_after = list(after_list)  # Start with all, remove matches
        common = []
        modified = []

        for b_elem in before_list:
            # Find matching element in after
            match_idx = None
            for i, a_elem in enumerate(only_in_after):
                if elements_match(b_elem, a_elem, check_position=False):
                    match_idx = i
                    break

            if match_idx is not None:
                a_elem = only_in_after.pop(match_idx)
                if elements_equal(b_elem, a_elem):
                    common.append(b_elem)
                else:
                    # Same element but different position/properties
                    modified.append({"before": b_elem, "after": a_elem})
            else:
                only_in_before.append(b_elem)

        results[element_type] = DiffResult(
            only_in_before=only_in_before,
            only_in_after=only_in_after,
            common=common,
            modified=modified,
        )

    return results


def diff_to_json(diff_results: dict[str, DiffResult]) -> dict:
    """Convert diff results to JSON-serializable format."""
    output = {}
    for element_type, result in diff_results.items():
        output[element_type] = {
            "removed": result.only_in_before,
            "added": result.only_in_after,
            "unchanged": result.common,
            "modified": result.modified,
        }
    return output


def load_pcb(path: Path) -> kicad.pcb.PcbFile:
    """Load a KiCad PCB file."""
    return kicad.loads(kicad.pcb.PcbFile, path)


def compute_pcb_diff(before_path: Path, after_path: Path) -> dict:
    """Main function to compute diff between two PCB files."""
    print(f"Loading before: {before_path}")
    before_pcb = load_pcb(before_path)

    print(f"Loading after: {after_path}")
    after_pcb = load_pcb(after_path)

    print("Extracting metadata...")
    before_meta = extract_pcb_metadata(before_pcb)
    after_meta = extract_pcb_metadata(after_pcb)

    print("Extracting elements...")
    before_elements = extract_pcb_elements(before_pcb)
    after_elements = extract_pcb_elements(after_pcb)

    print(
        f"Before: {sum(len(v) for v in before_elements.values())} elements, "
        f"After: {sum(len(v) for v in after_elements.values())} elements"
    )

    print("Computing diff...")
    diff_results = compute_diff(before_elements, after_elements)

    # Build net usage map (which elements use which nets)
    net_usage = {}
    for net_num, net_info in after_meta["nets"].items():
        net_usage[net_num] = {
            "name": net_info["name"],
            "segments": [],
            "vias": [],
            "pads": [],
        }

    # Collect all elements for net highlighting
    all_elements = {
        "footprints": [],
        "segments": [],
        "vias": [],
        "gr_lines": [],
        "arcs": [],
    }

    for element_type, diff in diff_results.items():
        for elem in diff.common:
            all_elements[element_type].append({**elem, "status": "unchanged"})
            # Track net usage
            if element_type == "segments" and elem.get("net"):
                net_num = elem["net"]
                if net_num in net_usage:
                    net_usage[net_num]["segments"].append(elem["uuid"])
            elif element_type == "vias" and elem.get("net"):
                net_num = elem["net"]
                if net_num in net_usage:
                    net_usage[net_num]["vias"].append(elem["uuid"])

        for mod in diff.modified:
            all_elements[element_type].append({**mod["before"], "status": "modified_before"})
            all_elements[element_type].append({**mod["after"], "status": "modified_after"})

        for elem in diff.only_in_before:
            all_elements[element_type].append({**elem, "status": "removed"})

        for elem in diff.only_in_after:
            all_elements[element_type].append({**elem, "status": "added"})

    # Track pad net usage
    for fp in all_elements["footprints"]:
        for pad in fp.get("pads", []):
            if pad.get("net"):
                net_num = pad["net"]
                if net_num in net_usage:
                    net_usage[net_num]["pads"].append({
                        "footprint": fp["uuid"],
                        "pad": pad["name"],
                        "reference": fp.get("reference"),
                    })

    return {
        "metadata": {
            "before": before_meta,
            "after": after_meta,
        },
        "nets": net_usage,
        "layers": after_meta["layers"],
        "diff": diff_to_json(diff_results),
        "elements": all_elements,
    }


if __name__ == "__main__":
    # Test with our sample files
    poc_dir = Path(__file__).parent
    before_path = poc_dir / "before.kicad_pcb"
    after_path = poc_dir / "after.kicad_pcb"

    if not before_path.exists() or not after_path.exists():
        print(f"Error: Test files not found in {poc_dir}")
        sys.exit(1)

    result = compute_pcb_diff(before_path, after_path)

    # Print summary
    diff = result["diff"]
    for element_type, data in diff.items():
        print(f"\n{element_type}:")
        print(f"  Removed: {len(data['removed'])}")
        print(f"  Added: {len(data['added'])}")
        print(f"  Unchanged: {len(data['unchanged'])}")
        print(f"  Modified: {len(data['modified'])}")

    print(f"\nNets: {len(result['nets'])}")
    print(f"Layers: {len(result['layers'])}")

    # Save to JSON for the viewer
    output_path = poc_dir / "diff_result.json"
    with open(output_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nDiff saved to {output_path}")
