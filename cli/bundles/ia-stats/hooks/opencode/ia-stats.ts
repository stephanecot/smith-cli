// OpenCode plugin — appends one row to IA_STATS.md per significant
// session event (tool execution, session idle). Mirrors the Claude Code
// `PostToolUse` + `SubagentStop` hooks and the Copilot VS Code task,
// using the shared `append-ia-stats.js` script also shipped under this
// hooks/opencode/ folder.
//
// The script's stdin contract is the **Claude Code event-payload shape**
// (`tool_name`, `subagent_type`, `usage.total_tokens`, `duration_ms`).
// OpenCode emits a different payload shape per event, so this plugin
// translates each OpenCode payload into the Claude Code shape before
// piping it on stdin. Translation keeps tool / agent identity accurate
// even when OpenCode does not surface token / duration metrics
// (degraded but non-broken — call counts and names stay correct).
//
// Install path (resolved by /smith-bundle-install):
//   <consumer>/.opencode/plugins/ia-stats.ts
// Sidecar script:
//   <consumer>/.opencode/plugins/append-ia-stats.js

import { spawn } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const scriptPath = resolve(here, "append-ia-stats.js");

function append(event: string, claudeShapedPayload: Record<string, unknown>): void {
  const child = spawn(
    "node",
    [scriptPath, "--event", event],
    { detached: true, stdio: ["pipe", "ignore", "ignore"] },
  );
  child.stdin?.write(JSON.stringify(claudeShapedPayload));
  child.stdin?.end();
  child.unref();
}

function translateToolExecuteAfter(payload: any): Record<string, unknown> {
  return {
    tool_name: payload?.tool ?? payload?.tool_name ?? "unknown",
    duration_ms: Number(
      payload?.duration_ms ??
      payload?.elapsed_ms ??
      (typeof payload?.started_at === "number" && typeof payload?.ended_at === "number"
        ? payload.ended_at - payload.started_at
        : 0),
    ) || 0,
  };
}

function translateSessionIdle(payload: any): Record<string, unknown> {
  return {
    subagent_type: payload?.agent_type ?? payload?.agent ?? payload?.session_id ?? "session",
    agent_id: payload?.session_id ?? "unknown",
    duration_ms: Number(payload?.duration_ms ?? 0) || 0,
    usage: { total_tokens: Number(payload?.usage?.total_tokens ?? 0) || 0 },
  };
}

export default async function iaStatsPlugin({ project }: { project: unknown }) {
  return {
    "tool.execute.after": async (payload: unknown) => {
      append("PostToolUse", translateToolExecuteAfter(payload));
    },
    "session.idle": async (payload: unknown) => {
      append("SubagentStop", translateSessionIdle(payload));
    },
  };
}
