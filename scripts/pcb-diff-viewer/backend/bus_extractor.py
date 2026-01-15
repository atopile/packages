"""
Bus Extractor - Extract bus/interface information from ato designs.

Uses the fast Zig BFS-based bus grouping to identify which nets belong
to which buses (ElectricPower, I2C, SPI, etc.)
"""

import logging
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

# Add atopile src to path
ATOPILE_SRC = Path(__file__).parent.parent.parent.parent.parent / "atopile" / "src"
sys.path.insert(0, str(ATOPILE_SRC))

logger = logging.getLogger(__name__)

# Define suggested colors for bus types
BUS_COLORS = {
    "ElectricPower": "#ef4444",  # Red for power
    "I2C": "#22c55e",  # Green
    "SPI": "#3b82f6",  # Blue
    "I2S": "#8b5cf6",  # Purple
    "UART": "#f97316",  # Orange
    "USB": "#ec4899",  # Pink
    "DifferentialPair": "#06b6d4",  # Cyan
    "ElectricLogic": "#a3e635",  # Lime
    "ElectricSignal": "#fbbf24",  # Amber
    "CAN": "#14b8a6",  # Teal
    "Ethernet": "#6366f1",  # Indigo
}

# Known interface types that represent buses
# Priority order: higher index = more specific (prefer these)
BUS_TYPE_PRIORITY = {
    "Electrical": 0,
    "ElectricSignal": 1,
    "ElectricLogic": 2,
    "DifferentialPair": 3,
    "ElectricPower": 4,
    # Protocol-level buses (most specific)
    "I2C": 10,
    "SPI": 10,
    "I2S": 10,
    "UART": 10,
    "USB": 10,
    "CAN": 10,
    "Ethernet": 10,
}

# Types we want to report (exclude base Electrical)
BUS_INTERFACE_TYPES = set(BUS_TYPE_PRIORITY.keys()) - {"Electrical"}


def extract_bus_info(
    project_dir: Path,
    build_name: str = "default",
) -> dict[str, Any]:
    """
    Build an ato design up to load-pcb and extract bus information.
    Uses fast Zig BFS for bus grouping.
    """
    import faebryk.core.node as fabll
    import faebryk.library._F as F
    from atopile.build import init_app
    from atopile.build_steps import muster
    from atopile.cli.logging_ import LoggingStage
    from atopile.config import config
    from faebryk.core.solver.defaultsolver import DefaultSolver

    # Apply configuration
    config.apply_options(
        entry=None,
        working_dir=project_dir,
        selected_builds=[build_name],
    )
    config.interactive = False

    buses: dict[str, dict] = {}
    net_to_bus: dict[str, str] = {}

    with config.select_build(build_name):
        logger.info(f"Building target '{config.build.name}' for bus extraction")

        # Initialize the app
        app = init_app()
        g = app.g
        tg = app.tg

        # Create solver and PCB
        solver = DefaultSolver()
        pcb = (
            F.PCB.bind_typegraph(tg)
            .create_instance(g=g)
            .setup(path=str(config.build.paths.layout), app=app)
        )

        # Run build stages up to load-pcb only (skip picker)
        for target in muster.select({"load-pcb"}):
            with LoggingStage(name=target.name, description=target.description):
                target(app, solver, pcb)

        # FAST PATH: Build KiCad net name -> electrical mapping from pads
        print("Building net name -> electrical mapping...")
        net_to_electricals: dict[str, set[fabll.Node]] = defaultdict(set)

        # Get all leads with associated pads
        for is_lead_trait in fabll.Traits.get_implementors(
            F.Lead.is_lead.bind_typegraph(tg), g=g
        ):
            interface_node = fabll.Traits.bind(is_lead_trait).get_obj_raw()

            if not interface_node.has_trait(fabll.is_interface):
                continue

            # Check if this lead has associated pads
            if not is_lead_trait.has_trait(F.Lead.has_associated_pads):
                continue

            has_pads = is_lead_trait.get_trait(F.Lead.has_associated_pads)
            for is_pad in has_pads.get_pads():
                if is_pad.has_trait(F.KiCadFootprints.has_associated_kicad_pcb_pad):
                    kicad_pad_trait = is_pad.get_trait(
                        F.KiCadFootprints.has_associated_kicad_pcb_pad
                    )
                    kicad_pad = kicad_pad_trait.get_pad()
                    if kicad_pad and kicad_pad.net and kicad_pad.net.name:
                        net_name = kicad_pad.net.name
                        net_to_electricals[net_name].add(interface_node)

        print(f"Found {len(net_to_electricals)} nets with electrical associations")

        # Build UUID -> net_name mapping for fast lookup
        uuid_to_nets: dict[int, set[str]] = defaultdict(set)
        for net_name, electricals in net_to_electricals.items():
            for elec in electricals:
                uuid = elec.instance.node().get_uuid()
                uuid_to_nets[uuid].add(net_name)

        # FAST: Use Zig BFS to group all electricals into buses
        all_electricals = set()
        for electricals in net_to_electricals.values():
            all_electricals.update(electricals)

        print(f"Grouping {len(all_electricals)} electricals into buses...")

        # This uses the fast Zig BFS internally
        # Suppress verbose logging during grouping
        logging.getLogger("faebryk.core.node").setLevel(logging.WARNING)
        bus_groups = fabll.is_interface.group_into_buses(all_electricals)
        logging.getLogger("faebryk.core.node").setLevel(logging.INFO)
        print(f"Found {len(bus_groups)} bus groups")

        # First pass: collect info for each bus group
        # Groups with the same parent interface will be merged
        parent_to_groups: dict[str, list[dict]] = {}  # parent_uuid -> list of group info
        ungrouped = []

        for representative, members in bus_groups.items():
            # Collect all net names for this bus
            bus_nets: set[str] = set()
            for member in members:
                uuid = member.instance.node().get_uuid()
                if uuid in uuid_to_nets:
                    bus_nets.update(uuid_to_nets[uuid])

            # Skip buses with no nets
            if not bus_nets:
                continue

            # Find the bus type by checking ALL members and picking the most specific
            # Also get the parent interface UUID for merging
            all_found_types: list[tuple[str, str, int, str | None]] = []
            for member in members:
                member_type, member_instance, parent_uuid = _find_bus_type(member)
                if member_type:
                    priority = BUS_TYPE_PRIORITY.get(member_type, 0)
                    all_found_types.append((member_type, member_instance, priority, parent_uuid))

            # Pick the most specific type (highest priority)
            bus_type, bus_instance, parent_uuid = None, None, None
            if all_found_types:
                all_found_types.sort(key=lambda x: x[2], reverse=True)
                bus_type, bus_instance, _, parent_uuid = all_found_types[0]

            group_info = {
                "type": bus_type,
                "instance": bus_instance,
                "nets": bus_nets,
                "parent_uuid": parent_uuid,
            }

            # Group by parent interface UUID for merging (only for protocol-level buses)
            if parent_uuid and bus_type and BUS_TYPE_PRIORITY.get(bus_type, 0) >= 10:
                if parent_uuid not in parent_to_groups:
                    parent_to_groups[parent_uuid] = []
                parent_to_groups[parent_uuid].append(group_info)
            else:
                ungrouped.append(group_info)

        # Second pass: merge groups with same parent and create final buses
        bus_id_counter = 0

        # Process merged groups (protocol buses like I2C, SPI with same parent)
        for parent_uuid, groups in parent_to_groups.items():
            # Merge all nets from groups with same parent
            merged_nets: set[str] = set()
            for g in groups:
                merged_nets.update(g["nets"])

            # Use the type/instance from the first group (they should all be the same)
            bus_type = groups[0]["type"]
            bus_instance = groups[0]["instance"]

            # Generate bus_id
            base_id = f"{bus_type}:{bus_instance}"
            bus_id = base_id
            suffix = 1
            while bus_id in buses:
                bus_id = f"{base_id}_{suffix}"
                suffix += 1

            buses[bus_id] = {
                "id": bus_id,
                "type": bus_type or "Unknown",
                "instance": bus_instance or "unknown",
                "nets": [{"name": n} for n in sorted(merged_nets)],
                "color": BUS_COLORS.get(bus_type, "#888888"),
            }

            for net_name in merged_nets:
                if net_name not in net_to_bus:
                    net_to_bus[net_name] = bus_id

        # Process ungrouped buses
        for group_info in ungrouped:
            bus_type = group_info["type"]
            bus_instance = group_info["instance"]
            bus_nets = group_info["nets"]

            if bus_type:
                base_id = f"{bus_type}:{bus_instance}"
            else:
                base_id = f"bus_{bus_id_counter}"
            bus_id_counter += 1

            bus_id = base_id
            suffix = 1
            while bus_id in buses:
                bus_id = f"{base_id}_{suffix}"
                suffix += 1

            buses[bus_id] = {
                "id": bus_id,
                "type": bus_type or "Unknown",
                "instance": bus_instance or "unknown",
                "nets": [{"name": n} for n in sorted(bus_nets)],
                "color": BUS_COLORS.get(bus_type, "#888888"),
            }

            for net_name in bus_nets:
                if net_name not in net_to_bus:
                    net_to_bus[net_name] = bus_id

    return {
        "buses": buses,
        "net_to_bus": net_to_bus,
        "bus_colors": BUS_COLORS,
    }


def _find_bus_type(electrical) -> tuple[str | None, str | None, str | None]:
    """
    Find the bus type by tracing up the FULL hierarchy from an electrical.
    Collects all interface types and returns the most specific one.

    Example hierarchy: line -> MOSI (ElectricLogic) -> SPI
    We want to return SPI, not ElectricLogic.

    Returns (bus_type, instance_name, parent_interface_id) or (None, None, None).
    The parent_interface_id is used to merge groups that belong to the same interface.
    """
    import faebryk.core.node as fabll

    try:
        hierarchy = electrical.get_hierarchy()

        # Collect all interface types found in hierarchy
        # (type_name, instance_name, priority, node_uuid)
        found_types: list[tuple[str, str, int, str]] = []

        # Walk up hierarchy collecting all interface types
        for i, (node, name) in enumerate(hierarchy):
            # Skip the leaf node (the electrical itself)
            if i == len(hierarchy) - 1:
                continue

            # Skip nodes without is_interface trait (like resistors, capacitors)
            if not node.has_trait(fabll.is_interface):
                continue

            # Get the type name from the graph
            type_name = node.get_type_name()
            if type_name and type_name in BUS_INTERFACE_TYPES:
                priority = BUS_TYPE_PRIORITY.get(type_name, 0)
                instance = name if name and not name.startswith("0x") else type_name
                # Use node's UUID as identifier for merging
                node_uuid = node.instance.node().get_uuid()
                found_types.append((type_name, instance, priority, node_uuid))

        # Return the most specific type (highest priority)
        if found_types:
            found_types.sort(key=lambda x: x[2], reverse=True)
            best_type, best_instance, _, parent_uuid = found_types[0]
            return (best_type, best_instance, parent_uuid)

    except Exception as e:
        logger.debug(f"Error finding bus type: {e}")

    return (None, None, None)


# For testing
if __name__ == "__main__":
    import json

    # Test with LED badge
    project_dir = Path("/Users/narayanpowderly/projects/atopile/examples/led_badge")
    build_name = "badge"

    print(f"Extracting bus info from: {project_dir}")

    try:
        result = extract_bus_info(project_dir, build_name)

        print(f"\n{'=' * 60}")
        print(f"BUS EXTRACTION RESULTS")
        print(f"{'=' * 60}")

        print(f"\nFound {len(result['buses'])} buses:")
        for bus_id, bus in sorted(result["buses"].items()):
            print(f"\n  {bus_id}:")
            print(f"    Type: {bus['type']}")
            print(f"    Color: {bus['color']}")
            print(f"    Nets ({len(bus['nets'])}):")
            for net in bus["nets"][:5]:
                print(f"      - {net['name']}")
            if len(bus["nets"]) > 5:
                print(f"      ... and {len(bus['nets']) - 5} more")

        print(f"\n\nTotal net mappings: {len(result['net_to_bus'])}")

        # Output as JSON
        print(f"\n\n{'=' * 60}")
        print("JSON OUTPUT:")
        print(json.dumps(result, indent=2))

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
