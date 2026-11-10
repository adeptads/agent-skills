"""Assemble local AdeptAds skill and plugin packages without publishing."""

import hashlib
import json
import re
import shutil
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

from public_files import (
    CLIENTS,
    ROOT,
    SKILL_FILES,
    archive_name,
    expected_json,
    plugin_dir,
    plugin_files,
    read_metadata,
    render_readme,
    validate_public_tree,
    validate_skill_frontmatter,
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def archive(path, root, files):
    with ZipFile(path, "w", compression=ZIP_DEFLATED) as output:
        for relative in sorted(files):
            info = ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, (root / relative).read_bytes())


def build():
    metadata = read_metadata(ROOT)
    name = metadata["name"]
    dist = ROOT / "dist"
    if dist.is_symlink():
        raise ValueError("Archive output directory must not be a symlink")
    if name != "adeptads-google-ads":
        raise ValueError("Unexpected package name")
    current = {archive_name(metadata, kind) for kind in (*CLIENTS, "skill")}
    owned_archive = re.compile(
        re.escape(name)
        + r"-(?:codex|claude|skill)-\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?\.zip"
    )
    if dist.exists():
        for path in dist.iterdir():
            if owned_archive.fullmatch(path.name) and path.name not in current:
                if path.is_symlink() or not path.is_file():
                    raise ValueError("Old package archive must be a regular file")
                path.unlink()
    validate_public_tree(ROOT, allow_local=True, require_complete=False)
    validate_skill_frontmatter(ROOT, name)
    shutil.copyfile(ROOT / "LICENSE", ROOT / "skills" / name / "LICENSE")
    dist.mkdir(exist_ok=True)
    archives = []
    for client in CLIENTS:
        plugin = ROOT / plugin_dir(name, client)
        shutil.copyfile(ROOT / "LICENSE", plugin / "LICENSE")
        for relative in SKILL_FILES:
            target = plugin / "skills" / name / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / "skills" / name / relative, target)
        (plugin / "README.md").write_text(render_readme(ROOT, metadata, client))
        for relative, value in expected_json(metadata, client).items():
            write_json(ROOT / relative, value)
        output = dist / archive_name(metadata, client)
        archive(output, plugin, plugin_files(name, client))
        archives.append(output)
    standalone = dist / archive_name(metadata, "skill")
    archive(standalone, ROOT / "skills", [f"{name}/{path}" for path in SKILL_FILES])
    archives.append(standalone)
    write_json(
        dist / "manifest.json",
        {
            "name": name,
            "version": metadata["version"],
            "mcp_url": metadata["config"]["mcpUrl"],
            "archives": [
                {
                    "file": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "bytes": path.stat().st_size,
                }
                for path in archives
            ],
        },
    )
    validate_public_tree(ROOT, allow_local=True)
    print(
        f"Prepared {len(archives)} ZIPs in {dist}. "
        "No upload, submission, or deployment."
    )


if __name__ == "__main__":
    build()
