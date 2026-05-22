// Example OpenCode plugin demonstrating four common patterns:
//   1. Block a destructive bash command before it runs (tool.execute.before).
//   2. Auto-lint after a file edit (file.edited).
//   3. Log every sub-agent stop to AGENT_STATUS.md (session.idle).
//   4. Show a TUI toast when a permission is denied (permission.replied).
//
// File path: .opencode/plugins/example-hook.ts
// Loaded automatically by OpenCode at startup.

import { spawn } from "node:child_process";
import { appendFile } from "node:fs/promises";
import { resolve } from "node:path";

export default async function exampleHook({ project, $ }) {
  const projectRoot = project.directory;
  const statusFile = resolve(projectRoot, "AGENT_STATUS.md");

  return {
    // 1. Block `rm -rf` and friends before the bash tool executes them.
    "tool.execute.before": async ({ tool, input }) => {
      if (tool !== "bash") return;
      const cmd: string = input?.command ?? "";
      if (/\brm\s+-rf\b/.test(cmd) || /\bsudo\b/.test(cmd)) {
        return {
          decision: "block",
          reason: `Blocked dangerous bash command: ${cmd}`,
        };
      }
    },

    // 2. Run the project's linter after any file edit.
    //    Fire-and-forget — we don't want to block the agent on lint output.
    "file.edited": async ({ file_path }) => {
      if (!/\.(ts|tsx|js|jsx)$/.test(file_path)) return;
      spawn("npx", ["eslint", "--fix", file_path], {
        cwd: projectRoot,
        detached: true,
        stdio: "ignore",
      }).unref();
    },

    // 3. Append a one-line entry to AGENT_STATUS.md every time a session
    //    goes idle. Useful for an at-a-glance audit trail.
    "session.idle": async ({ session_id, agent }) => {
      const line = `- ${new Date().toISOString()} — ${agent ?? "primary"} idled (session ${session_id})\n`;
      await appendFile(statusFile, line, "utf8");
    },

    // 4. Surface a TUI toast when the user denies a permission, so a
    //    later turn can see why a tool call failed.
    "permission.replied": async ({ tool, decision, reason }) => {
      if (decision !== "deny") return;
      await $`opencode toast "Denied ${tool}${reason ? `: ${reason}` : ""}"`;
    },
  };
}
