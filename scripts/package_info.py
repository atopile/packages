#! uv run
# /// script
# dependencies = [
#   "typer>=0.12",
#   "typing_extensions>=4.10.0",
#   "rich>=13.0.0",
#   "pyyaml>=6.0.2",
# ]
# ///

import typer
from typing_extensions import Annotated
from typing import Optional
from pathlib import Path
import re
import yaml
import subprocess
from datetime import datetime
from rich.console import Console
from rich.table import Table

app = typer.Typer()
console = Console()


def get_last_commit_date(package_path: Path) -> str:
    """Get the last commit date for a package directory."""
    try:
        result = subprocess.run(
            [
                "git",
                "log",
                "--pretty=format:%ad",
                "--date=iso",
                "--",
                str(package_path),
            ],
            capture_output=True,
            text=True,
            cwd=package_path.parent.parent,  # Go up to packages root
            check=True,
        )
        if result.stdout.strip():
            # Parse the ISO date and format it nicely
            date_str = result.stdout.strip().split("\n")[0]
            dt = datetime.fromisoformat(date_str.replace(" +", "+").replace(" -", "-"))
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        return "Unknown"
    except subprocess.CalledProcessError:
        return "Unknown"


def format_dependencies_markdown(deps: str) -> str:
    """Format dependencies for markdown (replace newlines with <br>)"""
    if deps == "":
        return ""
    return deps.replace("\n", "<br>")


def extract_dependencies(package_dir: Path, package_name: str) -> str:
    """Extract dependencies from .ato files in the package."""
    dependencies = set()

    # Look for .ato files in the package directory
    for ato_file in package_dir.glob("*.ato"):
        try:
            with open(ato_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Find "from" imports that reference atopile packages
            from_imports = re.findall(r'from\s+"(atopile/[^"]+)"', content)
            for imp in from_imports:
                # Extract package name from path like "atopile/package-name/file.ato"
                dep_package_name = imp.split("/")[1]
                # Exclude the package itself from dependencies
                if dep_package_name != package_name:
                    dependencies.add(dep_package_name)

        except Exception:
            continue

    if dependencies:
        return "\n".join(sorted(dependencies))
    return ""


@app.command()
def main(
    package_regex: Annotated[
        str, typer.Option(help="Regex to filter packages to build")
    ] = ".*",
    markdown_output: Annotated[
        Optional[Path], typer.Option(help="Export to markdown file")
    ] = None,
):
    """
    Prints a formatted table of packages with:
    - package name
    - version
    - requires-atopile version
    - date and time of last commit to the package
    - list of dependencies (other packages)
    """
    packages_root = Path(__file__).parent.parent / "packages"

    if not packages_root.exists():
        typer.echo("Error: packages directory not found", err=True)
        raise typer.Exit(1)

    # Collect package information
    packages_info = []

    for package_dir in sorted(packages_root.iterdir()):
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        # Check if package name matches regex
        if not re.search(package_regex, package_dir.name):
            continue

        ato_yaml_path = package_dir / "ato.yaml"
        if not ato_yaml_path.exists():
            continue

        try:
            with open(ato_yaml_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            package_info = config.get("package", {})
            package_name = package_info.get("identifier", package_dir.name)
            if package_name.startswith("atopile/"):
                package_name = package_name[8:]  # Remove 'atopile/' prefix

            version = package_info.get("version", "Unknown")
            requires_atopile = config.get("requires-atopile", "Unknown")
            last_commit = get_last_commit_date(package_dir)
            dependencies = extract_dependencies(package_dir, package_name)

            packages_info.append(
                {
                    "name": package_name,
                    "version": version,
                    "requires_atopile": requires_atopile,
                    "last_commit": last_commit,
                    "dependencies": dependencies,
                }
            )

        except Exception as e:
            typer.echo(f"Error processing {package_dir.name}: {e}", err=True)
            continue

    if not packages_info:
        typer.echo("No packages found matching the criteria.")
        return

    # Create Rich table
    table = Table(title=f"Package Information ({len(packages_info)} packages)")

    table.add_column("Package", style="cyan", no_wrap=True)
    table.add_column("Version", style="magenta")
    table.add_column("Requires Atopile", style="green")
    table.add_column("Last Commit", style="yellow")
    table.add_column("Dependencies", style="blue", no_wrap=True)

    for pkg in packages_info:
        table.add_row(
            pkg["name"],
            pkg["version"],
            pkg["requires_atopile"],
            pkg["last_commit"],
            pkg["dependencies"],
        )

    # Export to markdown if requested
    if markdown_output:
        with open(markdown_output, "w", encoding="utf-8") as f:
            f.write(f"# Package Information ({len(packages_info)} packages)\n\n")
            f.write(
                "| Package | Version | Requires Atopile | Last Commit | Dependencies |\n"
            )
            f.write(
                "|---------|---------|------------------|-------------|--------------|\n"
            )

            for pkg in packages_info:
                deps_md = format_dependencies_markdown(pkg["dependencies"])
                f.write(
                    f"| {pkg['name']} | {pkg['version']} | {pkg['requires_atopile']} | {pkg['last_commit']} | {deps_md} |\n"
                )

        typer.echo(f"Exported package information to {markdown_output}")

    # Always print to console
    console.print(table)


if __name__ == "__main__":
    app()
