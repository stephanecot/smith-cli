---
name: ia-stats
description: Print the current contents of IA_STATS.MD (running totals per agent / tool + last 50 events). Read-only — the file is maintained automatically by the ia-stats hooks (Claude Code) or VS Code tasks (Copilot). Trigger with `/ia-stats`.
user-invocable: false
model: small
---

# Skill — `/ia-stats`

This skill is read-only. It does NOT compute anything ; the file
`IA_STATS.MD` is updated automatically by the events / tasks
shipped by the `ia-stats` bundle (Claude Code hooks on the Claude
Code side ; VS Code tasks on the Copilot side).

## How to invoke

The user types `/ia-stats` (no args).

## What you do

1. Read `IA_STATS.MD` at the project root.
2. If the file does not exist, tell the user the tracker has not
   recorded any event yet — that's expected on a fresh project until
   the first sub-agent dispatch or tool call.
3. Otherwise print the file verbatim. Don't paraphrase the tables.

## What you do NOT do

- Don't edit `IA_STATS.MD` from the parent session. The hooks / tasks
  own that file.
- Don't dispatch any sub-agent ; this skill is observation-only.
- Don't compute aggregates that aren't already in the file (no "tokens
  per day" rollups — that's a feature request for the script, not for
  this skill).

## Why this skill exists

`IA_STATS.MD` is verbose. Reading the raw markdown directly in chat
is fine, but a slash command makes it discoverable from the slash-
command dropdown without remembering the file name.
