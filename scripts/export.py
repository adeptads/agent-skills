"""Stage validated public repository contents without publishing anything."""

import argparse
import shutil
import tempfile
from pathlib import Path

from public_files import ROOT, validate_public_tree
from validate import validate


def export_public(destination, source=ROOT):
    source = Path(source)
    if source.is_symlink():
        raise ValueError("Public source root must not be a symlink")
    source = source.resolve()
    destination = Path(destination).absolute()
    if destination.is_symlink() or destination.exists():
        raise ValueError("Export destination must not exist")
    destination = destination.resolve()
    if (
        source == destination
        or source in destination.parents
        or destination in source.parents
    ):
        raise ValueError("Export destination must be separate from the source tree")
    if not destination.parent.is_dir():
        raise ValueError("Export destination parent must already exist")
    validate(source)
    expected = validate_public_tree(source, allow_local=True)
    with tempfile.TemporaryDirectory(
        dir=destination.parent, prefix=".agent-skills-export-"
    ) as temporary:
        staged = Path(temporary) / "repository"
        staged.mkdir()
        for relative in sorted(expected):
            original = source / relative
            if original.is_symlink() or any(
                parent.is_symlink() for parent in original.parents if parent != source
            ):
                raise ValueError(f"Symlink encountered during export: {relative}")
            target = staged / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
        validate(staged, check_archives=False)
        for relative in expected:
            if (staged / relative).read_bytes() != (source / relative).read_bytes():
                raise ValueError(f"Source changed during export: {relative}")
        staged.rename(destination)
    print(f"Prepared {len(expected)} public files in {destination}. No publication.")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    export_public(parser.parse_args().destination)
