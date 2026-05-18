---
name: db
description: Run `.claude/skills/db/scripts/db.py` against the local Postgres container in a dedicated Haiku sub-agent — instead of burning Opus context on psql output and python tracebacks. Trigger with `/db <subcommand> [args]` (e.g. `/db users`, `/db count projects`, `/db inspect users "role='ADMIN'" --limit 5`, `/db set-role x@y.z USER --yes`). Use whenever the user asks to inspect or mutate local data — anything where the parent session only needs the verdict, not the full output. Schema changes are out of scope (they go through Liquibase).
---

# Skill — `/db`

This skill exists for one reason : **`.claude/skills/db/scripts/db.py` doesn't need Opus.** Running it is a deterministic shell call followed by reading a psql table. Doing that in the parent session would dump rows and tracebacks into the Opus context window for no reasoning gain. Instead, this skill dispatches the `db-runner` agent (model : Haiku) and waits for its concise verdict.

The skill is **just a wrapper around `.claude/skills/db/scripts/db.py`** — it adds nothing beyond credential plumbing and the Haiku offload.

## How to invoke

The user types `/db <subcommand> [args]`. Take everything after `/db` as the args to forward. Subcommands available (full reference in `.claude/skills/db/scripts/db.py --help`) :

| Kind | Subcommand | Notes |
| --- | --- | --- |
| inspect | `users` / `workspaces` / `projects` | no args |
| inspect | `count <table>` | row count |
| inspect | `describe <table>` | `\d+` |
| inspect | `inspect <table> [where] [--limit N] [-x]` | SELECT * |
| inspect | `verify-local-admin` | LOCAL mode health check |
| mutate  | `set-role <email> <ADMIN\|USER> --yes` | |
| mutate  | `rename-workspace <public_id> <title> --yes` | |
| mutate  | `truncate <table> --yes` | irreversible |
| mutate  | `sql "<stmt>" [--yes] [-x]` | escape hatch |

If the user gives no args, ask which subcommand they want — `/db` alone is not actionable.

## Connection params

The parent session passes the credentials. Defaults match the local docker-compose stack and apply when nothing is specified :

- `--user smith` (or `$SMITH_DB_USER`)
- `--password smith` (or `$SMITH_DB_PASSWORD` — unused with the default container, forwarded as `PGPASSWORD` otherwise)
- `--db smith` (or `$SMITH_DB_NAME`)
- `--container smith-postgres` (or `$SMITH_DB_CONTAINER`)

Connection flags must come **before** the subcommand on the command line. If the user did not override them, do not invent values — let the script use its defaults.

## What you do

1. **Do not run `.claude/skills/db/scripts/db.py` yourself in the parent session.** That defeats the entire purpose of this skill.
2. **Dispatch the `db-runner` agent** via the Agent tool, in the foreground (you need its result before continuing). Set :
   - `subagent_type: "db-runner"`
   - `description` : 3–5 words, e.g. `"db users on local"`, `"db set-role to USER"`.
   - `prompt` : a self-contained instruction containing
     - the exact command line to run (e.g. `python3 .claude/skills/db/scripts/db.py users` or `python3 .claude/skills/db/scripts/db.py --user smith --db smith set-role x@y.z USER --yes`),
     - a one-line reminder that the working directory is the repo root,
     - the report shape (✅ OK / ❌ FAIL headline + relevant rows or error message ; no full output).
3. **Relay the agent's report** to the user verbatim, or with a one-line top summary. Do not paraphrase failure messages — copy them.

## Example dispatch prompt

```
Run `python3 .claude/skills/db/scripts/db.py users` once and report.

Working directory : repo root.

Report shape :
- One line : ✅ OK or ❌ FAIL.
- On OK : paste the table as-is (it is small).
- On FAIL : quote the error block from the script (container not running, psql error, …) — no full traceback.
```

## What you do NOT do

- Don't read `.claude/skills/db/scripts/db.py` in the parent session "to double-check" — the runner has Read/Glob/Grep if it needs them.
- Don't fix bugs in the script. If the runner reports the script itself is broken, hand the diagnostic to the user ; the user decides whether to dispatch a developer agent.
- Don't dispatch the runner more than once per turn. If the user wants a re-run, they ask.
- Don't run schema-changing SQL through `/db sql`. `CREATE`, `ALTER`, `DROP`, `CREATE INDEX`, … are forbidden — they belong in a Liquibase changeset. If the user requests one, refuse and tell them to add a changeset under `backend/smith-database/src/main/resources/db/changelog/`.
- Don't auto-add `--yes` to a mutation the user did not explicitly request as a mutation. If `--yes` is missing on a mutation subcommand, ask the user to confirm before forwarding.

## Why this skill exists

Multi-line psql tables and python tracebacks in the parent context cost real tokens and crowd out the work you're actually paid to think about. Offloading the run to Haiku trades pennies for a clean Opus context, and it's strictly faster end-to-end.
