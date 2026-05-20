#!/usr/bin/env python3
"""
smith-build — deterministic release builder.

Walks the Smith CLI source tree (cli/bin/, cli/bundles/, cli/templates/,
cli/providers/) and produces one runnable release per AI provider under
cli/releases/<provider>/.

No LLM reasoning — pure file walking, YAML parsing, frontmatter
assembly.

Usage:
    python3 build.py [--provider <slug>] [--clean]

Defaults : every provider listed under cli/providers/ (minus specs/) is
built ; the target tree cli/releases/<provider>/ is always wiped before
the build.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml


# ---------------------------------------------------------------------------
# Provider rules.
#
# Each entry declares :
#   - runtime_root / skills_subpath / agents_subpath : where the release
#     places bin skills + bin agents inside the release tree.
#   - agent_frontmatter_* : how to compose agent frontmatter from
#     <slug>/metadata.yml at build time.
#   - consumer_* : consumer-side install path templates, written verbatim
#     to <release>/.smith/paths.yaml so /smith-new-project and its
#     sub-agents stay provider-agnostic.
# ---------------------------------------------------------------------------

def load_provider_build_config(repo_root: Path, provider: str) -> dict:
    """Read `cli/providers/<provider>/provider.yaml::build` — the single
    source of truth for everything provider-specific consumed by the
    build. Refuse cleanly if missing : the script carries no fallbacks
    or business logic of its own."""
    pyaml = repo_root / "cli" / "providers" / provider / "provider.yaml"
    if not pyaml.is_file():
        raise SystemExit(f"error: provider config not found at {pyaml}")
    data = read_yaml(pyaml)
    build = data.get("build")
    if not isinstance(build, dict):
        raise SystemExit(
            f"error: {pyaml} is missing a `build:` section "
            f"(see cli/providers/specs/provider.schema.json)"
        )
    return build


def render_tools(caps: list[str], rules: dict) -> dict:
    """Map a generic capability list to the provider's frontmatter
    representation. Returns a dict of keys to merge into the agent
    frontmatter. Empty dict when no capability resolves."""
    if not caps:
        return {}
    mapping = rules["capability_map"]
    resolved = []
    for c in caps:
        native = mapping.get(c)
        if native and native not in resolved:
            resolved.append(native)
    if not resolved:
        return {}
    style = rules["tools_style"]
    if style == "claude-string":
        return {"tools": ", ".join(resolved)}
    if style == "yaml-list":
        return {"tools": resolved}
    if style == "opencode-permission":
        return {"permission": {t: "allow" for t in resolved}}
    raise ValueError(f"unknown tools_style: {style}")


def render_skill_properties(metadata: dict, rules: dict) -> dict:
    """Map generic bundle-skill properties (declared in metadata.yml — e.g.
    `model`, `user-invocable`) to provider-native frontmatter keys via
    `provider.yaml::build.skill_property_map`. Properties absent from the
    map OR mapped to null are silently dropped from the rendered
    frontmatter. Values are passed through verbatim."""
    out: dict = {}
    mapping = rules.get("skill_property_map") or {}
    for generic_key, native_key in mapping.items():
        if native_key is None or generic_key not in metadata:
            continue
        out[native_key] = metadata[generic_key]
    return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    data = yaml.safe_load(text)
    return data if isinstance(data, dict) else {}


def _normalise_strings(obj):
    """Collapse paragraph-style blank lines (`\\n\\s*\\n+`) to a single
    `\\n` inside every string value. Single line breaks are preserved.
    Used at release-emission time so multi-line block scalars in source
    `config.yaml` files render cleanly (no big empty paragraphs between
    every sentence). Trailing whitespace per line is stripped too."""
    import re
    if isinstance(obj, dict):
        return {k: _normalise_strings(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_normalise_strings(v) for v in obj]
    if isinstance(obj, str):
        # Strip trailing whitespace on every line + collapse paragraph
        # breaks (≥2 consecutive line breaks) into a single newline.
        lines = [line.rstrip() for line in obj.splitlines()]
        joined = "\n".join(lines).strip()
        return re.sub(r"\n{2,}", "\n", joined)
    return obj


def _str_representer(dumper, data):
    """Use literal block style for any string with embedded newlines so
    multi-line descriptions stay readable in the dumped YAML."""
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


yaml.SafeDumper.add_representer(str, _str_representer)


def dump_yaml(data: dict) -> str:
    """One-stop YAML dump with the conventions we use across the build."""
    return yaml.safe_dump(
        _normalise_strings(data),
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=10_000,
    )


def dump_frontmatter(data: dict) -> str:
    body = yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=10_000,
    ).rstrip("\n")
    return f"---\n{body}\n---\n"


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def git_sha(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True, timeout=5,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Per-provider builders
# ---------------------------------------------------------------------------

def build_bin_skills(repo_root: Path, release_root: Path, rules: dict) -> dict:
    """Copy bin skills to the release. Bodies are portable across providers.
    Companion files travel only when the provider's skill path is a folder
    (i.e. ends with /SKILL.md — only true for claude-code today)."""
    stats = {"built": 0, "skipped": 0, "warnings": []}

    src_root = repo_root / "cli" / "bin" / "skills"
    if not src_root.is_dir():
        return stats

    skill_template = rules["consumer_paths"]["skill"]
    has_skill_folder = skill_template.endswith("/SKILL.md")

    for skill_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        slug = skill_dir.name
        src_md = skill_dir / "SKILL.md"
        if not src_md.is_file():
            stats["warnings"].append(f"{slug}: SKILL.md missing")
            stats["skipped"] += 1
            continue

        dst = release_root / skill_template.format(slug=slug)
        atomic_write(dst, src_md.read_text(encoding="utf-8"))

        # Companion files only travel when the skill destination has a
        # dedicated <slug>/ folder (skill_template ending in /SKILL.md).
        if has_skill_folder:
            for child in skill_dir.rglob("*"):
                if child.is_file() and child.name != "SKILL.md":
                    rel = child.relative_to(skill_dir)
                    target = dst.parent / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(child, target)

        stats["built"] += 1

    return stats


def build_bin_agents(repo_root: Path, release_root: Path, rules: dict) -> dict:
    """Compose each agent's frontmatter from metadata.yml + provider rules,
    write to release."""
    stats = {"built": 0, "skipped": 0, "warnings": []}

    src_root = repo_root / "cli" / "bin" / "agents"
    if not src_root.is_dir():
        return stats

    agent_template = rules["consumer_paths"]["agent"]
    fm_rules = rules["agent_frontmatter"]

    for agent_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        slug = agent_dir.name
        metadata = read_yaml(agent_dir / "metadata.yml")
        body_path = agent_dir / f"{slug}.md"

        if not body_path.is_file():
            stats["warnings"].append(f"{slug}: body file missing")
            stats["skipped"] += 1
            continue
        if not metadata.get("description"):
            stats["warnings"].append(f"{slug}: metadata.yml missing description")
            stats["skipped"] += 1
            continue

        # Compose frontmatter : name + description from metadata.yml,
        # provider extras, then resolve `capabilities:` (generic) into the
        # provider's native tools/permission representation.
        fm: dict = {}
        if fm_rules.get("emit_name", True):
            fm["name"] = metadata.get("name", slug)
        fm["description"] = metadata["description"]
        fm.update(fm_rules.get("extra") or {})
        caps = metadata.get("capabilities") or []
        if not isinstance(caps, list):
            stats["warnings"].append(f"{slug}: metadata.yml::capabilities must be a list")
            caps = []
        fm.update(render_tools(caps, rules))

        body = body_path.read_text(encoding="utf-8")
        content = dump_frontmatter(fm) + "\n" + body
        dst = release_root / agent_template.format(slug=slug)
        atomic_write(dst, content)
        stats["built"] += 1

    return stats


def build_bundles(repo_root: Path, release_root: Path, provider: str, rules: dict) -> dict:
    """For each bundle whose `providers:` list includes the current provider :
    compose per-skill frontmatter, copy hooks (flattened), strip the
    `providers:` field from config.yaml. Regenerate the catalogue with the
    built-only filter."""
    stats = {"built": 0, "skipped": []}

    src_root = repo_root / "cli" / "bundles"
    if not src_root.is_dir():
        return stats

    dst_root = release_root / ".smith" / "bundles"

    for bundle_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        bundle_name = bundle_dir.name
        cfg_src = bundle_dir / "config.yaml"
        if not cfg_src.is_file():
            stats["skipped"].append({"name": bundle_name, "reason": "no-config-yaml"})
            continue
        cfg = read_yaml(cfg_src)
        providers = cfg.get("providers", []) or []
        if provider not in providers:
            stats["skipped"].append({"name": bundle_name, "reason": "provider-not-supported"})
            continue

        bundle_dst = dst_root / bundle_name

        # config.yaml — strip `providers:` (release is already provider-scoped).
        cfg_clean = {k: v for k, v in cfg.items() if k != "providers"}
        atomic_write(
            bundle_dst / "config.yaml",
            dump_yaml(cfg_clean),
        )

        # skills — frontmatter is composed from metadata.yml ONLY ; provider-
        # native keys (e.g. claude-code `user-invocable`) are resolved from
        # generic property slugs declared in metadata.yml via
        # provider.yaml::build.skill_property_map.
        for skill in cfg.get("skills", []) or []:
            slug = skill["name"] if isinstance(skill, dict) else str(skill)
            skill_dir = bundle_dir / "skills" / slug
            body_path = skill_dir / f"{slug}.md"
            metadata = read_yaml(skill_dir / "metadata.yml")

            if not body_path.is_file():
                continue

            fm: dict = {}
            if "name" in metadata:
                fm["name"] = metadata["name"]
            if "description" in metadata:
                fm["description"] = metadata["description"]
            fm.update(render_skill_properties(metadata, rules))

            content = dump_frontmatter(fm) + "\n" + body_path.read_text(encoding="utf-8")
            atomic_write(bundle_dst / "skills" / slug / "SKILL.md", content)

        # hooks — flatten hooks/<provider>/ → hooks/ (release is provider-scoped).
        hooks_src = bundle_dir / "hooks" / provider
        if hooks_src.is_dir():
            hooks_dst = bundle_dst / "hooks"
            hooks_dst.mkdir(parents=True, exist_ok=True)
            for hook_file in sorted(hooks_src.rglob("*")):
                if hook_file.is_file():
                    rel = hook_file.relative_to(hooks_src)
                    target = hooks_dst / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(hook_file, target)

        stats["built"] += 1

    # catalog — filter to built bundles, drop `providers` field.
    catalog_src = src_root / "index.yaml"
    if catalog_src.is_file():
        catalog = read_yaml(catalog_src)
        built_names = {
            p.name for p in (release_root / ".smith" / "bundles").iterdir()
            if p.is_dir()
        }
        catalog["bundles"] = [
            {k: v for k, v in entry.items() if k != "providers"}
            for entry in catalog.get("bundles", [])
            if entry.get("name") in built_names
        ]
        atomic_write(
            release_root / ".smith" / "bundles" / "index.yaml",
            dump_yaml(catalog),
        )

    return stats


def _compose_skill_md(body_path: Path, metadata: dict, rules: dict) -> str:
    """Frontmatter (name + description + provider-mapped properties) + body."""
    fm: dict = {}
    if "name" in metadata:
        fm["name"] = metadata["name"]
    if "description" in metadata:
        fm["description"] = metadata["description"]
    fm.update(render_skill_properties(metadata, rules))
    return dump_frontmatter(fm) + "\n" + body_path.read_text(encoding="utf-8")


def _copy_tree_verbatim(src: Path, dst: Path) -> None:
    """Recursive verbatim copy. Skips silently if src is absent."""
    if not src.is_dir():
        return
    dst.mkdir(parents=True, exist_ok=True)
    for child in sorted(src.rglob("*")):
        if child.is_file():
            rel = child.relative_to(src)
            target = dst / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(child, target)


def _build_framework_template(ver_dir: Path, ver_dst: Path, cfg: dict, rules: dict) -> None:
    """framework/<name>/<version>/ — many skills under skills/<source-slug>/.
    Release dir is renamed to `metadata.yml::name` so it matches what the
    consumer-installed skill will be called."""
    cfg_clean = {k: v for k, v in cfg.items() if k != "providers"}
    atomic_write(
        ver_dst / "config.yaml",
        dump_yaml(cfg_clean),
    )
    for skill in cfg.get("skills", []) or []:
        source_slug = skill["name"] if isinstance(skill, dict) else str(skill)
        skill_dir = ver_dir / "skills" / source_slug
        body_path = skill_dir / f"{source_slug}.md"
        if not body_path.is_file():
            continue
        metadata = read_yaml(skill_dir / "metadata.yml")
        installed_name = metadata.get("name") or source_slug
        atomic_write(
            ver_dst / "skills" / installed_name / "SKILL.md",
            _compose_skill_md(body_path, metadata, rules),
        )


def _build_bootstrap_template(ver_dir: Path, ver_dst: Path, cfg: dict, rules: dict) -> None:
    """bootstrap/<name>/<version>/ — exactly one skill under skill/. Release
    dir is renamed to `metadata.yml::name` (same iso rule as framework). Plus
    optional sidecar trees (assets/, templates/, scripts/) copied verbatim."""
    cfg_clean = {k: v for k, v in cfg.items() if k != "providers"}
    atomic_write(
        ver_dst / "config.yaml",
        dump_yaml(cfg_clean),
    )
    skill_dir = ver_dir / "skill"
    if skill_dir.is_dir():
        metadata = read_yaml(skill_dir / "metadata.yml")
        installed_name = metadata.get("name") or skill_dir.name
        body_candidates = list(skill_dir.glob("*.md"))
        body_path = body_candidates[0] if body_candidates else None
        if body_path and body_path.is_file():
            atomic_write(
                ver_dst / "skill" / installed_name / "SKILL.md",
                _compose_skill_md(body_path, metadata, rules),
            )
    # Sidecar buckets — copied verbatim to release.
    for bucket in ("assets", "templates", "scripts"):
        _copy_tree_verbatim(ver_dir / bucket, ver_dst / bucket)


CATEGORY_BUILDERS = {
    "framework": _build_framework_template,
    "bootstrap": _build_bootstrap_template,
}


def _filter_catalog_yaml(catalog_src: Path, built_keys: set, key_fields: tuple, list_field: str) -> dict:
    """Filter a YAML catalogue (bundles/config.yaml,
    templates/<cat>/index.yaml) to built entries only, drop `providers`."""
    catalog = read_yaml(catalog_src)
    catalog[list_field] = [
        {k: v for k, v in entry.items() if k != "providers"}
        for entry in catalog.get(list_field, [])
        if tuple(entry.get(f) for f in key_fields) in built_keys
    ]
    return catalog


def build_templates(repo_root: Path, release_root: Path, provider: str, rules: dict) -> dict:
    """Walks every template category (framework / bootstrap / …) under
    cli/templates/<category>/ and applies the matching builder. Each category
    is self-contained : its own builder + its own index.yaml."""
    stats = {"built": 0, "skipped": []}

    src_root = repo_root / "cli" / "templates"
    if not src_root.is_dir():
        return stats

    for category, builder in CATEGORY_BUILDERS.items():
        cat_src = src_root / category
        if not cat_src.is_dir():
            continue
        cat_dst = release_root / ".smith" / "templates" / category

        built_keys: set = set()
        for name_dir in sorted(p for p in cat_src.iterdir() if p.is_dir()):
            for ver_dir in sorted(p for p in name_dir.iterdir() if p.is_dir()):
                name = name_dir.name
                version = ver_dir.name
                cfg_src = ver_dir / "config.yaml"
                if not cfg_src.is_file():
                    stats["skipped"].append(
                        {"category": category, "name": name, "version": version, "reason": "no-config-yaml"}
                    )
                    continue
                cfg = read_yaml(cfg_src)
                # Templates apply to every provider — no per-provider filter
                # at this layer. (Bundles still gate on `providers:` because
                # some bundles ship platform-specific hooks.)
                builder(ver_dir, cat_dst / name / version, cfg, rules)
                built_keys.add((name, version))
                stats["built"] += 1

        # Per-category index — filter to built entries, drop `providers`.
        cat_index = cat_src / "index.yaml"
        if cat_index.is_file():
            if category == "framework":
                filtered = _filter_catalog_yaml(cat_index, built_keys, ("framework", "version"), "templates")
            else:  # bootstrap
                filtered = _filter_catalog_yaml(cat_index, built_keys, ("name", "version"), "bootstraps")
            atomic_write(
                cat_dst / "index.yaml",
                dump_yaml(filtered),
            )

    return stats


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_provider(repo_root: Path, provider: str, rules: dict) -> dict:
    release_root = repo_root / "cli" / "releases" / provider
    if release_root.exists():
        shutil.rmtree(release_root)
    release_root.mkdir(parents=True)

    t0 = time.time()

    # Single source of truth for consumer-side install paths — copied
    # verbatim from provider.yaml::build.consumer_paths.
    atomic_write(
        release_root / ".smith" / "paths.yaml",
        dump_yaml(rules["consumer_paths"]),
    )

    bin_skills_stats = build_bin_skills(repo_root, release_root, rules)
    bin_agents_stats = build_bin_agents(repo_root, release_root, rules)
    bundles_stats = build_bundles(repo_root, release_root, provider, rules)
    templates_stats = build_templates(repo_root, release_root, provider, rules)

    elapsed_ms = int((time.time() - t0) * 1000)

    manifest = {
        "provider": provider,
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "smith_cli_sha": git_sha(repo_root),
        "duration_ms": elapsed_ms,
        "bin": {
            "skills": bin_skills_stats,
            "agents": bin_agents_stats,
        },
        "bundles": bundles_stats,
        "templates": templates_stats,
    }
    manifest_yaml = yaml.safe_dump(
        manifest,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
        width=10_000,
    )
    atomic_write(release_root / ".smith" / "release.yaml", manifest_yaml)
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description="Smith release builder")
    ap.add_argument("--provider", help="Build a single provider (default : all)")
    ap.add_argument("--clean", action="store_true", help="Explicit clean flag (default behaviour anyway)")
    ap.add_argument("--repo-root", default=None, help="Override repo root (default : cwd)")
    args = ap.parse_args()

    repo_root = Path(args.repo_root or Path.cwd()).resolve()
    providers_dir = repo_root / "cli" / "providers"
    if not providers_dir.is_dir():
        print(f"error: cli/providers/ not found under {repo_root}", file=sys.stderr)
        return 2

    available = sorted(
        p.name
        for p in providers_dir.iterdir()
        if p.is_dir() and p.name != "specs"
    )
    if args.provider:
        if args.provider not in available:
            print(
                f"error: provider '{args.provider}' not found "
                f"(available : {', '.join(available)})",
                file=sys.stderr,
            )
            return 2
        targets = [args.provider]
    else:
        targets = available

    print(f"smith-build : {len(targets)} provider(s) → {', '.join(targets)}")
    print(f"  repo root : {repo_root}")
    print()

    for provider in targets:
        rules = load_provider_build_config(repo_root, provider)
        manifest = build_provider(repo_root, provider, rules)

        print(
            f"  {provider:<14} : "
            f"bin-skills={manifest['bin']['skills']['built']}"
            f"/{manifest['bin']['skills']['built'] + manifest['bin']['skills']['skipped']}, "
            f"bin-agents={manifest['bin']['agents']['built']}, "
            f"bundles={manifest['bundles']['built']}, "
            f"templates={manifest['templates']['built']}, "
            f"{manifest['duration_ms']}ms"
        )

    print()
    print("OK — manifests : cli/releases/<provider>/.smith/release.yaml")
    return 0


if __name__ == "__main__":
    sys.exit(main())
