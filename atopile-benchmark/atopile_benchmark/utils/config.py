"""Configuration loading and saving utilities.

This module provides functions for loading and saving YAML configuration
files, with support for preserving header comments.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


def load_config(config_file: Path) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        config_file: Path to the YAML configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If the configuration file doesn't exist
        yaml.YAMLError: If the YAML is invalid
    """
    with open(config_file, "r") as f:
        return yaml.safe_load(f)


def save_config(config_file: Path, config: dict) -> None:
    """Save configuration to YAML file, preserving comments where possible.

    Args:
        config_file: Path to the YAML configuration file
        config: Configuration dictionary to save
    """
    # Read the original file to preserve structure
    header_lines = []
    try:
        with open(config_file, "r") as f:
            original_content = f.read()

        # For simplicity, we'll rewrite the entire file with a clean structure
        # but preserve any comments at the top
        for line in original_content.split("\n"):
            if line.startswith("#") or line.strip() == "":
                header_lines.append(line)
            else:
                break
    except FileNotFoundError:
        pass

    header = "\n".join(header_lines)
    if header and not header.endswith("\n"):
        header += "\n"

    # Write the config
    with open(config_file, "w") as f:
        if header:
            f.write(header)
        yaml.dump(
            config, f, default_flow_style=False, sort_keys=False, allow_unicode=True
        )

    logger.debug(f"Saved configuration to {config_file}")
