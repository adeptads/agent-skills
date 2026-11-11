"""Explicit source and content boundary for public AdeptAds packages."""

import json
import os
import re
from pathlib import Path
from string import Template
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SKILL_FILES = ("SKILL.md", "references/tools.md", "references/ppc-checks.md", "LICENSE")
README_TEMPLATE = "templates/plugin-README.md"
LOGO = "assets/logo.svg"
SCHEMA_BASE = "https://agent-plugins.org/schemas/1.0.0"
CLIENTS = {
    "codex": {
        "manifest": "plugin.json",
        "mcp": "mcp.json",
        "catalog": ".agents/plugins/marketplace.json",
        "transport": "streamable-http",
    },
    "claude": {
        "manifest": ".claude-plugin/plugin.json",
        "mcp": ".mcp.json",
        "catalog": ".claude-plugin/marketplace.json",
        "transport": "http",
    },
}
ARCHIVE_KINDS = (*CLIENTS, "skill")
LOCAL_DIRECTORIES = {".git", ".ruff_cache", "__pycache__", ".venv", ".idea", ".vscode"}
LOCAL_FILES = {".DS_Store"}
FRONTMATTER_KEYS = {"name", "description", "license", "compatibility", "allowed-tools"}
PLAIN_SCALAR = re.compile(r"[^\s'\"\[\]{}>|*&!%@#`,?:-](?:(?!: | #).)*(?<!:)")
PRIVATE_CONTENT = (
    ("local filesystem path", r"(?:/(?:Users|home|private|tmp)/|[A-Za-z]:\\Users\\)"),
    (
        "internal document reference",
        r"(?:release-status|approval-options)\.(?:md|json)",
    ),
    ("internal evidence path", r"\b(?:releases|reviews|logs)/[\w.-]+"),
    ("private key", r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
    ("AWS access key", r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    (
        "GitHub token",
        r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b",
    ),
    ("Google OAuth token", r"\b(?:ya29\.[A-Za-z0-9_-]{20,}|1//[A-Za-z0-9_-]{20,})"),
    ("bearer credential", r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}=*"),
    ("account UUID", r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b"),
    ("Google customer identifier", r"\b\d{3}-\d{3}-\d{4}\b"),
)


def archive_name(metadata, kind):
    return f"{metadata['name']}-{kind}-{metadata['version']}.zip"


def plugin_dir(name, client):
    return f"plugins/{client}/{name}"


def plugin_files(name, client):
    layout = CLIENTS[client]
    return (
        "README.md",
        "LICENSE",
        layout["manifest"],
        layout["mcp"],
        LOGO,
        *(f"skills/{name}/{p}" for p in SKILL_FILES),
    )


def expected_json(metadata, client):
    """Generated JSON files for one client, keyed by path relative to ROOT."""
    name, config, layout = metadata["name"], metadata["config"], CLIENTS[client]
    common = {
        key: metadata[key]
        for key in ("name", "version", "description", "author", "repository", "license")
    }
    server = {"type": layout["transport"], "url": config["mcpUrl"]}
    source = f"./{plugin_dir(name, client)}"
    if client == "codex":
        listing = config["listing"]
        manifest = {
            "$schema": f"{SCHEMA_BASE}/plugin.schema.json",
            **common,
            "homepage": listing["websiteURL"],
            "extensions": {
                "com.openai": {
                    "interface": {
                        "displayName": config["displayName"],
                        "developerName": metadata["author"]["name"],
                        **{
                            key: listing[key]
                            for key in (
                                "shortDescription",
                                "category",
                                "capabilities",
                                "websiteURL",
                                "supportURL",
                                "privacyPolicyURL",
                                "termsOfServiceURL",
                                "defaultPrompt",
                            )
                        },
                        "longDescription": listing_description(metadata, client),
                        "logo": f"./{LOGO}",
                        "composerIcon": f"./{LOGO}",
                    },
                },
            },
        }
        connection = {
            "$schema": f"{SCHEMA_BASE}/mcp.schema.json",
            "mcpServers": {"adeptads": server},
        }
        catalog = {
            "name": config["marketplace"],
            "plugins": [
                {
                    "name": name,
                    "source": {"source": "local", "path": source},
                    "policy": {
                        "installation": "AVAILABLE",
                        "authentication": "ON_INSTALL",
                    },
                    "category": "Productivity",
                }
            ],
        }
    else:
        listing = config["listing"]
        manifest = {
            **common,
            "displayName": config["displayName"],
            "homepage": listing["websiteURL"],
            "icon": f"./{LOGO}",
            "documentationUrl": metadata["repository"] + "#readme",
            "supportUrl": listing["supportURL"],
            "privacyPolicyUrl": listing["privacyPolicyURL"],
            "termsOfServiceUrl": listing["termsOfServiceURL"],
        }
        connection = {"mcpServers": {"adeptads": server}}
        catalog = {
            "name": config["marketplace"],
            "description": metadata["description"],
            "owner": metadata["author"],
            "plugins": [{"name": name, "source": source}],
        }
    base = plugin_dir(name, client)
    return {
        f"{base}/{layout['manifest']}": manifest,
        f"{base}/{layout['mcp']}": connection,
        layout["catalog"]: catalog,
    }


def install_steps(metadata, client):
    repo = metadata["repository"].removeprefix("https://github.com/")
    marketplace = metadata["config"]["marketplace"]
    if client == "claude":
        return (
            f"```sh\nclaude plugin marketplace add {repo}\n"
            f"claude plugin install {metadata['name']}@{marketplace}\n```\n\n"
            "Start a new session and use `/mcp` to complete AdeptAds OAuth sign-in.\n"
        )
    return (
        f"```sh\ncodex plugin marketplace add {repo}\n"
        f"codex plugin add {metadata['name']}@{marketplace}\n```\n\n"
        "Start a new session and complete AdeptAds OAuth sign-in when prompted.\n"
    )


def listing_description(metadata, client):
    listing = metadata["config"]["listing"]
    copy = listing["clients"][client]
    return f"{copy['headline']}\n\n{copy['opening']}\n\n{listing['body']}"


def render_readme(root, metadata, client):
    template = Template((Path(root) / README_TEMPLATE).read_text())
    listing = metadata["config"]["listing"]
    text = template.substitute(
        display_name=metadata["config"]["displayName"],
        opening=listing["clients"][client]["opening"],
        body=listing["body"],
        prompts="\n".join(f'- "{prompt}"' for prompt in listing["defaultPrompt"]),
        repository=metadata["repository"],
        install=install_steps(metadata, client),
        headline=listing["clients"][client]["headline"],
        mcp_url=metadata["config"]["mcpUrl"],
        support_url=listing["supportURL"],
        privacy_url=listing["privacyPolicyURL"],
        terms_url=listing["termsOfServiceURL"],
    )
    return text.rstrip("\n") + "\n"


def validate_mcp_url(value):
    url = urlsplit(value)
    if (
        url.scheme != "https"
        or not url.hostname
        or url.path != "/mcp"
        or url.username is not None
        or url.password is not None
        or url.query
        or url.fragment
    ):
        raise ValueError("MCP URL must be a credential-free HTTPS URL ending in /mcp")


def validate_listing(metadata, root):
    config = metadata["config"]
    listing = config["listing"]
    url_fields = {"websiteURL", "supportURL", "privacyPolicyURL", "termsOfServiceURL"}
    if set(listing) != url_fields | {
        "shortDescription",
        "body",
        "clients",
        "category",
        "capabilities",
        "defaultPrompt",
    }:
        raise ValueError("Unexpected public listing fields")
    for field, value in {
        **{key: listing[key] for key in url_fields},
        "author.url": metadata["author"]["url"],
    }.items():
        url = urlsplit(value)
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError(
                f"Public listing {field} must be a credential-free HTTPS URL"
            )
        if len(value) > 1024:
            raise ValueError(f"Public listing {field} exceeds 1024 characters")
    for value, limit, field in (
        (config["displayName"], 30, "displayName"),
        (listing["shortDescription"], 30, "shortDescription"),
        (metadata["author"]["name"], 80, "developerName"),
        (metadata["author"]["email"], 320, "author.email"),
    ):
        if not isinstance(value, str) or not value.strip() or len(value) > limit:
            raise ValueError(f"Invalid public listing {field}")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", metadata["author"]["email"]):
        raise ValueError("Invalid public author.email")
    if set(listing["clients"]) != set(CLIENTS):
        raise ValueError("Public listing copy must cover each client")
    for client, copy in listing["clients"].items():
        if set(copy) != {"headline", "opening"} or any(
            not isinstance(value, str) or not value.strip() for value in copy.values()
        ):
            raise ValueError(f"Invalid public listing copy: {client}")
        if len(listing_description(metadata, client)) > 4000:
            raise ValueError(f"Public listing longDescription exceeds 4000: {client}")
    for field, max_items, limit in (
        ("defaultPrompt", 3, 128),
        ("capabilities", 20, 120),
    ):
        values = listing[field]
        if (
            not isinstance(values, list)
            or len(values) > max_items
            or any(
                not isinstance(value, str) or not value.strip() or len(value) > limit
                for value in values
            )
        ):
            raise ValueError(f"Invalid public listing {field}")
    if not (root / LOGO).is_file():
        raise ValueError("Public logo is missing")


def validate_skill_frontmatter(root, name):
    """Accept only single-line plain YAML scalars so clients parse what we check."""
    text = (Path(root) / "skills" / name / "SKILL.md").read_text()
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError("SKILL.md must start with YAML frontmatter")
    fields = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(": ")
        value = value.strip()
        if not separator or key not in FRONTMATTER_KEYS or key in fields:
            raise ValueError(f"Unsupported or duplicate SKILL.md key: {line!r}")
        if not PLAIN_SCALAR.fullmatch(value):
            raise ValueError(
                f"SKILL.md {key} must be a plain one-line value: {value!r}"
            )
        fields[key] = value
    if not {"name", "description"} <= set(fields):
        raise ValueError("SKILL.md frontmatter needs name and description")
    if fields["name"] != name or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name):
        raise ValueError("SKILL.md name must be kebab-case and match its directory")
    if len(name) > 64:
        raise ValueError("SKILL.md name exceeds 64 characters")
    if len(fields["description"]) > 1024 or re.search(r"[<>]", fields["description"]):
        raise ValueError(
            "SKILL.md description must be 1-1024 characters without < or >"
        )
    if len(fields.get("compatibility", "")) > 500:
        raise ValueError("SKILL.md compatibility exceeds 500 characters")


def public_files(name):
    files = {
        ".gitignore",
        "README.md",
        "LICENSE",
        "assets/banner.svg",
        "assets/how-it-works.svg",
        LOGO,
        "package.json",
        README_TEMPLATE,
        "scripts/build.py",
        "scripts/export.py",
        "scripts/public_files.py",
        "scripts/validate.py",
    }
    files.update(f"skills/{name}/{path}" for path in SKILL_FILES)
    for client, layout in CLIENTS.items():
        files.add(layout["catalog"])
        files.update(
            f"{plugin_dir(name, client)}/{p}" for p in plugin_files(name, client)
        )
    return files


def validate_public_content(relative, data):
    content = data.decode("utf-8")
    for label, pattern in PRIVATE_CONTENT:
        if re.search(pattern, content):
            raise ValueError(f"Public content rejected ({label}): {relative}")
    if relative.endswith(".json"):
        json.loads(content)


def read_metadata(root):
    metadata_path = root / "package.json"
    if metadata_path.is_symlink():
        raise ValueError("Public metadata must not be a symlink")
    metadata = json.loads(metadata_path.read_text())
    if set(metadata) != {
        "name",
        "version",
        "description",
        "private",
        "repository",
        "author",
        "config",
        "license",
    }:
        raise ValueError("Unexpected public package metadata fields")
    if metadata["name"] != "adeptads-google-ads" or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", metadata["version"]
    ):
        raise ValueError("Invalid public package name or version")
    if metadata["license"] != "MIT":
        raise ValueError("Public package license must be MIT")
    if set(metadata["config"]) != {
        "marketplace",
        "displayName",
        "mcpUrl",
        "listing",
    }:
        raise ValueError("Unexpected public package configuration fields")
    if set(metadata["author"]) != {"name", "email", "url"}:
        raise ValueError("Unexpected public author fields")
    validate_mcp_url(metadata["config"]["mcpUrl"])
    validate_listing(metadata, root)
    return metadata


def validate_public_tree(root, *, allow_local=False, require_complete=True):
    root = Path(root)
    if root.is_symlink():
        raise ValueError("Public source root must not be a symlink")
    metadata = read_metadata(root)
    expected = public_files(metadata["name"])
    local_files = {f"dist/{archive_name(metadata, kind)}" for kind in ARCHIVE_KINDS} | {
        "dist/manifest.json"
    }
    found = set()
    for directory, directories, filenames in os.walk(root, followlinks=False):
        for name in [*directories, *filenames]:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError(
                    f"Symlinks are not public package inputs: {path.relative_to(root)}"
                )
        if allow_local:
            directories[:] = [
                name for name in directories if name not in LOCAL_DIRECTORIES
            ]
        for name in filenames:
            path = Path(directory) / name
            relative = path.relative_to(root).as_posix()
            if allow_local and (relative in local_files or name in LOCAL_FILES):
                continue
            if relative not in expected or not path.is_file():
                raise ValueError(f"Unlisted public package input: {relative}")
            validate_public_content(relative, path.read_bytes())
            found.add(relative)
    if require_complete and (missing := expected - found):
        raise ValueError(f"Missing public package inputs: {', '.join(sorted(missing))}")
    return expected
