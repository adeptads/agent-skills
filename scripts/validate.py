"""Check package boundaries, copied skills, connection settings and archives."""

import hashlib
import json
from zipfile import ZipFile

from public_files import (
    ARCHIVE_KINDS,
    CLIENTS,
    ROOT,
    SKILL_FILES,
    archive_name,
    expected_json,
    install_steps,
    plugin_dir,
    plugin_files,
    render_readme,
    validate_public_tree,
    validate_skill_frontmatter,
)


def read_json(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_archive(path, source, expected):
    expected = set(expected)
    with ZipFile(path) as package:
        entries = package.namelist()
        require(
            len(entries) == len(expected) and set(entries) == expected,
            f"Unexpected ZIP entries: {path.name}",
        )
        for relative in expected:
            require(
                package.read(relative) == (source / relative).read_bytes(),
                f"ZIP content drift: {path.name}/{relative}",
            )


def validate(root=ROOT, *, check_archives=True):
    validate_public_tree(root, allow_local=check_archives)
    root = root.resolve()
    metadata = read_json(root / "package.json")
    name = metadata["name"]
    validate_skill_frontmatter(root, name)
    license_text = (root / "LICENSE").read_bytes()
    require(
        (root / "skills" / name / "LICENSE").read_bytes() == license_text,
        "Standalone license drift",
    )
    root_readme = (root / "README.md").read_text()
    for client in CLIENTS:
        require(
            install_steps(metadata, client) in root_readme,
            f"Root README install steps drift: {client}",
        )
        plugin = root / plugin_dir(name, client)
        require(
            (plugin / "LICENSE").read_bytes() == license_text, "Plugin license drift"
        )
        for relative, value in expected_json(metadata, client).items():
            require(
                read_json(root / relative) == value, f"Generated JSON drift: {relative}"
            )
        require(
            (plugin / "README.md").read_text() == render_readme(root, metadata, client),
            f"Generated README drift: {client}",
        )
        for relative in SKILL_FILES:
            require(
                (plugin / "skills" / name / relative).read_bytes()
                == (root / "skills" / name / relative).read_bytes(),
                f"Generated skill drift: {client}/{relative}",
            )
        if check_archives:
            validate_archive(
                root / "dist" / archive_name(metadata, client),
                plugin,
                plugin_files(name, client),
            )
    if check_archives:
        validate_archive(
            root / "dist" / archive_name(metadata, "skill"),
            root / "skills",
            (f"{name}/{path}" for path in SKILL_FILES),
        )
        inventory = read_json(root / "dist/manifest.json")
        require(
            set(inventory) == {"name", "version", "mcp_url", "archives"}
            and inventory["name"] == name
            and inventory["version"] == metadata["version"]
            and inventory["mcp_url"] == metadata["config"]["mcpUrl"],
            "Archive inventory metadata drift",
        )
        require(
            len(inventory["archives"]) == len(ARCHIVE_KINDS)
            and {archive["file"] for archive in inventory["archives"]}
            == {archive_name(metadata, kind) for kind in ARCHIVE_KINDS},
            "Unexpected archive inventory entries",
        )
        for archive in inventory["archives"]:
            require(
                set(archive) == {"file", "sha256", "bytes"}, "Unexpected archive fields"
            )
            path = root / "dist" / archive["file"]
            require(
                hashlib.sha256(path.read_bytes()).hexdigest() == archive["sha256"]
                and path.stat().st_size == archive["bytes"],
                f"Archive hash/size drift: {path.name}",
            )
    print(
        "PASS: public file/content boundary, skill frontmatter, catalogs, manifests, "
        "MCP configuration, READMEs and skill copies."
    )
    if check_archives:
        print("PASS: exact ZIP entries, contents and hashes.")


if __name__ == "__main__":
    validate()
