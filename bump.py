import argparse
import tomllib
from enum import StrEnum
from pathlib import Path


class BumpMode(StrEnum):
    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"


def parse_mode(value) -> BumpMode:
    try:
        return BumpMode(value.lower())
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid version '{value}'. Choose from: major, minor, patch"
        )


def update_version(filename: Path, old_version: str, new_version: str) -> None:
    times_replaced = 0
    updated_lines = []
    with open(filename, "r", encoding="utf-8") as file:
        for line in file:
            if line.lstrip().startswith("version"):
                updated_lines.append(line.replace(old_version, new_version))
                times_replaced += 1
            else:
                updated_lines.append(line)
    assert times_replaced == 1, "Version needs to be replace exactly once"
    with open(filename, "w", encoding="utf-8") as file:
        file.writelines(updated_lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI template with versioning and dry run support"
    )
    parser.add_argument("path", help="Input file or directory path")
    parser.add_argument(
        "mode", type=parse_mode, help="Bump mode: major, minor, or patch"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no changes will be made)",
    )
    args = parser.parse_args()

    if args.dry_run:
        print("Dry run mode enabled")

    mode = args.mode
    pyproject = Path(f"{args.path}/pyproject.toml")
    if not pyproject.is_file():
        print(f"{pyproject} is no valid file")
        exit(1)

    with open(pyproject, "rb") as f:
        pyproject_data = tomllib.load(f)

    version = pyproject_data["project"]["version"]
    version_parts = version.split(".")

    assert len(version_parts) == 3

    major_part = int(version_parts[0])
    minor_part = int(version_parts[1])
    patch_part = int(version_parts[2])
    print(f"Crrr: Major {major_part} / Minor {minor_part} / Patch {patch_part}")

    if mode == BumpMode.MAJOR:
        new_version = f"{major_part + 1}.0.0"
    elif mode == BumpMode.MINOR:
        new_version = f"{major_part}.{minor_part + 1}.0"
    else:
        new_version = f"{major_part}.{minor_part}.{patch_part + 1}"

    print(f"New: {new_version}")
    if not args.dry_run:
        update_version(pyproject, version, new_version)


if __name__ == "__main__":
    main()
