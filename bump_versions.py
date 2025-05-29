# /// script
# dependencies = [
#   "typer>=0.12",
#   "pyyaml>=6.0.2",
#   "typing_extensions>=4.10.0",
# ]
# ///


# INSTRUCTIONS:
# - this shall be run with uv with embedded depencies so we need no venv etc
# - use typer for the cli
# - argumment: major, minor, patch (which one to bump)
# - optional regex for the package name
# - look for all ato.yaml files
# - use yaml to read the version, and bump the appropriate field
# - save yaml again (without changing formatting or anything else in the file)
# - (there is a library for that kind of yaml operation: ruamel.yaml)

import typer
from typing_extensions import Annotated
from pathlib import Path
import re
import yaml

app = typer.Typer()


@app.command()
def main(
    version_part: Annotated[
        str,
        typer.Argument(
            help="Which part of the version to bump: major, minor, or patch."
        ),
    ],
    package_regex: Annotated[
        str, typer.Option(help="Optional regex to filter package names.")
    ] = ".*",
    dry_run: Annotated[
        bool, typer.Option(help="Dry run, don't actually change anything.")
    ] = False,
):
    """
    Bumps the version in ato.yaml files.
    """
    if version_part not in ["major", "minor", "patch"]:
        print(
            f"Error: version_part must be one of 'major', 'minor', or 'patch'. Got '{version_part}'."
        )
        raise typer.Exit(code=1)

    print(
        f"Bumping {version_part} version for packages matching regex: '{package_regex}'"
    )

    current_path = Path(".")
    for ato_file in current_path.rglob("**/ato.yaml"):
        try:
            ato_yaml = ato_file.read_text()
            data = yaml.load(ato_yaml, Loader=yaml.FullLoader)

            package = data.get("package")
            if not package:
                print(f"Skipping {ato_file}, no package found.")
                continue

            package_name = package.get("identifier", "").split("/")[-1]
            if not package_name:
                print(f"Skipping {ato_file}, no package name found.")
                continue

            if not re.match(package_regex, package_name):
                print(
                    f"Skipping {ato_file} (name: {package_name}) due to regex mismatch or missing name."
                )
                continue

            version_str = package.get("version")
            if not version_str:
                print(f"Skipping {ato_file}, no version found.")
                continue

            major, minor, patch_val = map(int, version_str.split("."))

            if version_part == "major":
                major += 1
                minor = 0
                patch_val = 0
            elif version_part == "minor":
                minor += 1
                patch_val = 0
            elif version_part == "patch":
                patch_val += 1

            new_version_str = f"{major}.{minor}.{patch_val}"
            package["version"] = new_version_str

            # A bit ghetto, but doesn't fuck with the formatting
            ato_yaml = ato_yaml.replace(f'"{version_str}"', f'"{new_version_str}"')
            if not dry_run:
                ato_file.write_text(ato_yaml)

            print(f"✅ {version_str} -> {new_version_str} | {package_name} ")

        except Exception as e:
            print(f"Error processing {ato_file}: {e}")


if __name__ == "__main__":
    app()
