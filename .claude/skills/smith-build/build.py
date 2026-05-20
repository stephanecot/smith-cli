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
import json
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


def build_bundles(repo_root: Path, release_root: Path, provider: str) -> dict:
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
            yaml.safe_dump(cfg_clean, sort_keys=False, default_flow_style=False, allow_unicode=True, width=10_000),
        )

        # skills
        for skill in cfg.get("skills", []) or []:
            slug = skill["name"] if isinstance(skill, dict) else str(skill)
            skill_dir = bundle_dir / "skills" / slug
            body_path = skill_dir / f"{slug}.md"
            metadata = read_yaml(skill_dir / "metadata.yml")
            provider_fm = read_yaml(skill_dir / f"{provider}.yml")

            if not body_path.is_file():
                continue

            fm: dict = {}
            fm.update(metadata)
            fm.update(provider_fm)

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
    catalog_src = src_root / "config.json"
    if catalog_src.is_file():
        catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
        built_names = {
            p.name for p in (release_root / ".smith" / "bundles").iterdir()
            if p.is_dir()
        }
        catalog["bundles"] = [
            {k: v for k, v in entry.items() if k != "providers"}
            for entry in catalog.get("bundles", [])
            if entry.get("name") in built_names
        ]
        atomic_write(release_root / ".smith" / "bundles" / "config.json", json.dumps(catalog, indent=2) + "\n")

    return stats


def build_templates(repo_root: Path, release_root: Path, provider: str) -> dict:
    """Same shape as build_bundles, for framework templates."""
    stats = {"built": 0, "skipped": []}

    src_root = repo_root / "cli" / "templates"
    if not src_root.is_dir():
        return stats

    dst_root = release_root / ".smith" / "templates"

    for fw_dir in sorted(p for p in src_root.iterdir() if p.is_dir()):
        for ver_dir in sorted(p for p in fw_dir.iterdir() if p.is_dir()):
            framework = fw_dir.name
            version = ver_dir.name
            cfg_src = ver_dir / "config.yaml"
            if not cfg_src.is_file():
                stats["skipped"].append(
                    {"framework": framework, "version": version, "reason": "no-config-yaml"}
                )
                continue
            cfg = read_yaml(cfg_src)
            providers = cfg.get("providers", []) or []
            if provider not in providers:
                stats["skipped"].append(
                    {"framework": framework, "version": version, "reason": "provider-not-supported"}
                )
                continue

            ver_dst = dst_root / framework / version
            cfg_clean = {k: v for k, v in cfg.items() if k != "providers"}
            atomic_write(
                ver_dst / "config.yaml",
                yaml.safe_dump(cfg_clean, sort_keys=False, default_flow_style=False, allow_unicode=True, width=10_000),
            )

            for skill in cfg.get("skills", []) or []:
                slug = skill["name"] if isinstance(skill, dict) else str(skill)
                skill_dir = ver_dir / "skills" / slug
                body_path = skill_dir / "template.md"
                metadata = read_yaml(skill_dir / "metadata.yml")
                provider_fm = read_yaml(skill_dir / f"{provider}.yml")

                if not body_path.is_file():
                    continue

                fm: dict = {}
                fm.update(metadata)
                fm.update(provider_fm)

                content = dump_frontmatter(fm) + "\n" + body_path.read_text(encoding="utf-8")
                atomic_write(ver_dst / "skills" / slug / "SKILL.md", content)

            stats["built"] += 1

    # catalog — filter to built frameworks, drop `providers` field.
    catalog_src = src_root / "index.json"
    if catalog_src.is_file():
        catalog = json.loads(catalog_src.read_text(encoding="utf-8"))
        built = {
            (fw_dir.name, ver_dir.name)
            for fw_dir in (release_root / ".smith" / "templates").iterdir() if fw_dir.is_dir()
            for ver_dir in fw_dir.iterdir() if ver_dir.is_dir()
        }
        catalog["templates"] = [
            {k: v for k, v in entry.items() if k != "providers"}
            for entry in catalog.get("templates", [])
            if (entry.get("framework"), entry.get("version")) in built
        ]
        atomic_write(release_root / ".smith" / "templates" / "index.json", json.dumps(catalog, indent=2) + "\n")

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
        yaml.safe_dump(rules["consumer_paths"], sort_keys=False, default_flow_style=False, allow_unicode=True, width=10_000),
    )

    bin_skills_stats = build_bin_skills(repo_root, release_root, rules)
    bin_agents_stats = build_bin_agents(repo_root, release_root, rules)
    bundles_stats = build_bundles(repo_root, release_root, provider)
    templates_stats = build_templates(repo_root, release_root, provider)

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
