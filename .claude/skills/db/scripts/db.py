#!/usr/bin/env python3
"""Skillsator — local DB toolkit.

Quick data-only operations against the local Postgres container, without
the heavy hammer of dropping the DB. Schema changes still go through
Liquibase changesets in `backend/smith-database/...` — never use this tool
to mutate schema.

Connects via `docker exec smith-postgres psql` so no host-side psql install
is needed ; the container must be running (`docker compose -f
deploy/local/docker-compose.yml up -d`).

Connection (optional, before the subcommand) :
  --user <role>        Postgres role        (default: smith ; $SMITH_DB_USER)
  --password <pwd>     PGPASSWORD forwarded (default: $SMITH_DB_PASSWORD)
  --db <name>          database name        (default: smith ; $SMITH_DB_NAME)
  --container <name>   docker container     (default: smith-postgres ; $SMITH_DB_CONTAINER)

Examples
--------
  # quick inspections (no confirmation needed)
  python3 .claude/skills/db/scripts/db.py users
  python3 .claude/skills/db/scripts/db.py workspaces
  python3 .claude/skills/db/scripts/db.py projects
  python3 .claude/skills/db/scripts/db.py count projects
  python3 .claude/skills/db/scripts/db.py describe users
  python3 .claude/skills/db/scripts/db.py inspect users "role = 'ADMIN'" --limit 5
  python3 .claude/skills/db/scripts/db.py verify-local-admin

  # mutations (need --yes or interactive confirmation)
  python3 .claude/skills/db/scripts/db.py set-role cottin@smith.local USER --yes
  python3 .claude/skills/db/scripts/db.py rename-workspace 01900000-0000-7002-8000-000000000001 "Skillsator Demo" --yes
  python3 .claude/skills/db/scripts/db.py truncate ai_call_log --yes
  python3 .claude/skills/db/scripts/db.py sql "UPDATE users SET role='ADMIN' WHERE email='x@y.z'" --yes

  # explicit credentials (parent agent forwarding via the /db skill)
  python3 .claude/skills/db/scripts/db.py --user smith --password smith --db smith users

The `sql` subcommand is the escape hatch for anything not covered by a
named subcommand. Prefer named subcommands when they exist — they document
the intent and validate inputs.
"""

from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from typing import Optional

DEFAULT_CONTAINER = "smith-postgres"
DEFAULT_USER = "smith"
DEFAULT_DB = "smith"


# ---------------------------------------------------------------------------
# Low-level psql wrapper
# ---------------------------------------------------------------------------
def _psql(args: argparse.Namespace, sql: str, *, capture: bool = False, expanded: bool = False) -> str:
    """Run a single SQL statement inside the container via docker exec.

    Connection params (`args.user`, `args.password`, `args.db`, `args.container`)
    are sourced from the parent parser so the caller — typically the `/db`
    skill — picks the credentials at invocation time. `--password` is forwarded
    via `PGPASSWORD` to support setups where the local socket does not run with
    `trust` auth ; the default container ignores it.
    """
    psql_args = ["psql", "-U", args.user, "-d", args.db]
    if expanded:
        psql_args += ["-x"]
    psql_args += ["-v", "ON_ERROR_STOP=1", "-c", sql]

    docker_cmd = ["docker", "exec", "-i"]
    if args.password:
        docker_cmd += ["-e", f"PGPASSWORD={args.password}"]
    docker_cmd += [args.container]
    cmd = docker_cmd + psql_args

    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        sys.stderr.write(f"psql failed (exit {proc.returncode})\n")
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        if proc.stdout:
            sys.stderr.write(proc.stdout)
        sys.exit(proc.returncode)
    if capture:
        return proc.stdout
    if proc.stdout:
        sys.stdout.write(proc.stdout)
    return ""


def _confirm(msg: str, yes: bool) -> None:
    """Interactive y/N gate ; bypassed by --yes."""
    if yes:
        return
    try:
        ans = input(f"⚠  {msg} [y/N] ").strip().lower()
    except EOFError:
        ans = ""
    if ans not in ("y", "yes"):
        print("aborted", file=sys.stderr)
        sys.exit(1)


def _q(value: str) -> str:
    """Escape single quotes for an SQL string literal.

    Adequate for our local-dev use case ; do NOT reuse this in production
    code paths where untrusted input could reach the DB.
    """
    return value.replace("'", "''")


# ---------------------------------------------------------------------------
# Inspection commands (read-only, no confirmation)
# ---------------------------------------------------------------------------
def cmd_users(args: argparse.Namespace) -> None:
    _psql(
        args,
        "SELECT email, role, first_name, last_name, public_id "
        "FROM users ORDER BY role DESC, email;",
    )


def cmd_workspaces(args: argparse.Namespace) -> None:
    _psql(
        args,
        "SELECT w.public_id, w.title, "
        "       (SELECT count(*) FROM workspace_members m WHERE m.workspace_id = w.id) AS members "
        "FROM workspaces w ORDER BY w.title;",
    )


def cmd_projects(args: argparse.Namespace) -> None:
    _psql(
        args,
        "SELECT p.public_id, p.title, w.title AS workspace, p.git_operation_state, p.ai_target "
        "FROM projects p JOIN workspaces w ON w.id = p.workspace_id "
        "ORDER BY w.title, p.title;",
    )


def cmd_count(args: argparse.Namespace) -> None:
    _psql(args, f"SELECT count(*) AS rows FROM {args.table};")


def cmd_describe(args: argparse.Namespace) -> None:
    # \d+ requires the meta-command path, not -c. Use -P pager=off + STDIN.
    docker_cmd = ["docker", "exec", "-i"]
    if args.password:
        docker_cmd += ["-e", f"PGPASSWORD={args.password}"]
    docker_cmd += [args.container]
    cmd = docker_cmd + [
        "psql", "-U", args.user, "-d", args.db,
        "-P", "pager=off",
    ]
    proc = subprocess.run(
        cmd, input=f"\\d+ {args.table}\n", capture_output=True, text=True, check=False
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr or proc.stdout or "")
        sys.exit(proc.returncode)
    sys.stdout.write(proc.stdout)


def cmd_inspect(args: argparse.Namespace) -> None:
    where = f"WHERE {args.where}" if args.where else ""
    _psql(args, f"SELECT * FROM {args.table} {where} LIMIT {args.limit};", expanded=args.expanded)


def cmd_verify_local_admin(args: argparse.Namespace) -> None:
    """Health check : LOCAL mode prerequisites in the DB."""
    print("=== local-admin user ===")
    _psql(
        args,
        "SELECT email, role, public_id FROM users "
        "WHERE email = 'local-admin@smith.local';",
    )
    print("=== local-admin workspace memberships ===")
    _psql(
        args,
        "SELECT w.public_id, w.title, wm.role FROM workspace_members wm "
        "JOIN users u ON u.id = wm.user_id "
        "JOIN workspaces w ON w.id = wm.workspace_id "
        "WHERE u.email = 'local-admin@smith.local' "
        "ORDER BY w.title;",
    )


# ---------------------------------------------------------------------------
# Mutation commands (require --yes or interactive confirm)
# ---------------------------------------------------------------------------
def cmd_set_role(args: argparse.Namespace) -> None:
    _confirm(f"UPDATE users SET role={args.role!r} WHERE email={args.email!r}?", args.yes)
    _psql(
        args,
        f"UPDATE users SET role = '{_q(args.role)}' "
        f"WHERE email = '{_q(args.email)}' "
        f"RETURNING email, role;",
    )


def cmd_rename_workspace(args: argparse.Namespace) -> None:
    _confirm(
        f"UPDATE workspaces SET title={args.new_title!r} WHERE public_id={args.public_id!r}?",
        args.yes,
    )
    _psql(
        args,
        f"UPDATE workspaces SET title = '{_q(args.new_title)}' "
        f"WHERE public_id = '{_q(args.public_id)}' "
        f"RETURNING public_id, title;",
    )


def cmd_truncate(args: argparse.Namespace) -> None:
    _confirm(
        f"TRUNCATE {args.table} CASCADE? (irreversible — all rows deleted)",
        args.yes,
    )
    _psql(args, f"TRUNCATE {args.table} CASCADE;")
    print(f"truncated {args.table}", file=sys.stderr)


def cmd_sql(args: argparse.Namespace) -> None:
    stmt = args.statement.strip().rstrip(";")
    is_read_only = stmt.lower().startswith(("select", "with", "explain", "show"))
    if not is_read_only:
        _confirm(f"execute SQL: {stmt!r}?", args.yes)
    _psql(args, stmt + ";", expanded=args.expanded)


# ---------------------------------------------------------------------------
# CLI wiring
# ---------------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="db.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # Connection params — must be passed BEFORE the subcommand. Defaults match
    # the local docker-compose stack ; the `/db` skill is the canonical caller
    # and lets the parent agent override on a per-invocation basis.
    p.add_argument(
        "--user",
        default=os.environ.get("SMITH_DB_USER", DEFAULT_USER),
        help="Postgres role (default: %(default)s, or $SMITH_DB_USER)",
    )
    p.add_argument(
        "--password",
        default=os.environ.get("SMITH_DB_PASSWORD"),
        help="Postgres password forwarded as PGPASSWORD (default: $SMITH_DB_PASSWORD ; "
             "unused by docker exec on the default container)",
    )
    p.add_argument(
        "--db",
        default=os.environ.get("SMITH_DB_NAME", DEFAULT_DB),
        help="Database name (default: %(default)s, or $SMITH_DB_NAME)",
    )
    p.add_argument(
        "--container",
        default=os.environ.get("SMITH_DB_CONTAINER", DEFAULT_CONTAINER),
        help="Postgres container name targeted by docker exec "
             "(default: %(default)s, or $SMITH_DB_CONTAINER)",
    )
    sub = p.add_subparsers(dest="cmd", required=True, metavar="<command>")

    # ── inspections ────────────────────────────────────────────────────────
    sub.add_parser("users", help="list users").set_defaults(func=cmd_users)
    sub.add_parser("workspaces", help="list workspaces with member counts").set_defaults(
        func=cmd_workspaces
    )
    sub.add_parser("projects", help="list projects with workspace + state").set_defaults(
        func=cmd_projects
    )

    pc = sub.add_parser("count", help="count rows in a table")
    pc.add_argument("table")
    pc.set_defaults(func=cmd_count)

    pd = sub.add_parser("describe", help=r"\d+ on a table")
    pd.add_argument("table")
    pd.set_defaults(func=cmd_describe)

    pi = sub.add_parser("inspect", help="SELECT * FROM <table> [WHERE …] LIMIT N")
    pi.add_argument("table")
    pi.add_argument("where", nargs="?", default=None, help="WHERE clause without the keyword")
    pi.add_argument("--limit", type=int, default=20)
    pi.add_argument("-x", "--expanded", action="store_true", help="psql expanded format")
    pi.set_defaults(func=cmd_inspect)

    sub.add_parser(
        "verify-local-admin",
        help="health check: local-admin user + workspace membership exist",
    ).set_defaults(func=cmd_verify_local_admin)

    # ── mutations ──────────────────────────────────────────────────────────
    sr = sub.add_parser("set-role", help="UPDATE users.role for an email")
    sr.add_argument("email")
    sr.add_argument("role", choices=["ADMIN", "USER"])
    sr.add_argument("--yes", "-y", action="store_true")
    sr.set_defaults(func=cmd_set_role)

    rw = sub.add_parser("rename-workspace", help="UPDATE workspaces.title by public_id")
    rw.add_argument("public_id")
    rw.add_argument("new_title")
    rw.add_argument("--yes", "-y", action="store_true")
    rw.set_defaults(func=cmd_rename_workspace)

    tr = sub.add_parser("truncate", help="TRUNCATE <table> CASCADE")
    tr.add_argument("table")
    tr.add_argument("--yes", "-y", action="store_true")
    tr.set_defaults(func=cmd_truncate)

    sq = sub.add_parser("sql", help="execute arbitrary SQL (escape hatch)")
    sq.add_argument("statement", help="SQL statement (single-quoted on the shell)")
    sq.add_argument("--yes", "-y", action="store_true")
    sq.add_argument("-x", "--expanded", action="store_true")
    sq.set_defaults(func=cmd_sql)

    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_parser().parse_args(argv)
    # Sanity check : the container must be running.
    container_check = subprocess.run(
        ["docker", "ps", "--filter", f"name={args.container}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if args.container not in container_check.stdout:
        sys.stderr.write(
            f"❌ container {args.container!r} is not running.\n"
            f"   Start it with:  docker compose -f deploy/local/docker-compose.yml up -d\n"
        )
        return 1
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
