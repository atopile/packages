#!/usr/bin/env python3
"""Validate benchmarks.yaml configuration."""

import sys
from pathlib import Path

import yaml


def validate_config(config_file: Path) -> bool:
    """Validate the configuration file.

    Args:
        config_file: Path to benchmarks.yaml

    Returns:
        True if valid, False otherwise
    """
    if not config_file.exists():
        print(f"❌ Config file not found: {config_file}")
        return False

    print(f"📋 Validating {config_file}...")

    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Failed to parse YAML: {e}")
        return False

    errors = []

    # Check required top-level keys
    required_keys = ['atopile_versions', 'package_benchmarks', 'build_commands']
    for key in required_keys:
        if key not in config:
            errors.append(f"Missing required key: {key}")

    # Validate atopile_versions
    if 'atopile_versions' in config:
        versions = config['atopile_versions']
        if not isinstance(versions, list):
            errors.append("atopile_versions must be a list")
        else:
            for i, version in enumerate(versions):
                if not isinstance(version, dict):
                    errors.append(f"atopile_versions[{i}] must be a dict")
                    continue

                if 'type' not in version:
                    errors.append(f"atopile_versions[{i}] missing 'type'")
                elif version['type'] not in ['release', 'branch', 'commit']:
                    errors.append(f"atopile_versions[{i}] has invalid type: {version['type']}")

                if 'version' not in version:
                    errors.append(f"atopile_versions[{i}] missing 'version'")

                if 'date' not in version:
                    errors.append(f"atopile_versions[{i}] missing 'date'")

    # Validate package_benchmarks
    if 'package_benchmarks' in config:
        packages = config['package_benchmarks']
        if not isinstance(packages, list):
            errors.append("package_benchmarks must be a list")
        else:
            for i, pkg in enumerate(packages):
                if not isinstance(pkg, dict):
                    errors.append(f"package_benchmarks[{i}] must be a dict")
                    continue

                required_pkg_keys = ['name', 'package', 'source']
                for key in required_pkg_keys:
                    if key not in pkg:
                        errors.append(f"package_benchmarks[{i}] missing '{key}'")

    # Validate build_commands
    if 'build_commands' in config:
        commands = config['build_commands']
        if not isinstance(commands, list):
            errors.append("build_commands must be a list")
        else:
            for i, cmd in enumerate(commands):
                if not isinstance(cmd, dict):
                    errors.append(f"build_commands[{i}] must be a dict")
                    continue

                required_cmd_keys = ['name', 'command', 'description']
                for key in required_cmd_keys:
                    if key not in cmd:
                        errors.append(f"build_commands[{i}] missing '{key}'")

    if errors:
        print("\n❌ Validation failed with errors:")
        for error in errors:
            print(f"  - {error}")
        return False

    print("✅ Configuration is valid!")

    # Print summary
    print("\nConfiguration Summary:")
    print(f"  Versions: {len(config.get('atopile_versions', []))}")
    print(f"  Packages: {len([p for p in config.get('package_benchmarks', []) if p.get('enabled', True)])}")
    print(f"  Build Commands: {len(config.get('build_commands', []))}")
    print(f"  Total Benchmarks: {len(config.get('atopile_versions', [])) * len([p for p in config.get('package_benchmarks', []) if p.get('enabled', True)]) * len(config.get('build_commands', []))}")

    return True


def main():
    """Main entry point."""
    config_file = Path('benchmarks.yaml')

    if len(sys.argv) > 1:
        config_file = Path(sys.argv[1])

    valid = validate_config(config_file)
    return 0 if valid else 1


if __name__ == '__main__':
    sys.exit(main())
