#!/usr/bin/env node
/**
 * append-ia-stats — Claude Code hook script (Node.js, cross-platform).
 *
 * Invoked by the SubagentStop and PostToolUse hooks declared in
 * ia-stats.hooks.json. Reads the event payload from stdin (JSON) and
 * appends a row to IA_STATS.MD at the consumer project's root.
 *
 * Runs identically on Windows, macOS, and Linux — the only requirement
 * is Node.js >= 16 (built-in `fs`, `path`, `process`, no `npm install`).
 * No Python, no jq, no bash, no PowerShell.
 *
 * Constraints :
 *   - Idempotent and side-effect-only ; never throws (errors go to stderr,
 *     exit code stays 0 so Claude Code does not disable the hook).
 *   - Best-effort concurrency safety via O_EXCL lockfile rename.
 *   - Trims the activity log to the last 50 entries.
 *
 * Usage : node append-ia-stats.js --event SubagentStop|PostToolUse [--file PATH]
 */

'use strict';

const fs = require('fs');
const path = require('path');

const STATUS_FILE_DEFAULT = 'IA_STATS.MD';
const MAX_RECENT = 50;
const LOCK_RETRIES = 25;
const LOCK_SLEEP_MS = 20;

function parseArgs(argv) {
  const out = { event: null, file: STATUS_FILE_DEFAULT };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--event') out.event = argv[++i];
    else if (argv[i] === '--file') out.file = argv[++i];
  }
  return out;
}

function readStdin() {
  return new Promise(resolve => {
    let buf = '';
    if (process.stdin.isTTY) return resolve('');
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => { buf += chunk; });
    process.stdin.on('end', () => resolve(buf));
    process.stdin.on('error', () => resolve(buf));
  });
}

function safeParse(raw) {
  if (!raw || !raw.trim()) return null;
  try { return JSON.parse(raw); } catch { return null; }
}

function nowIso() {
  return new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
}

function extractRow(event, payload) {
  if (event === 'SubagentStop') {
    const usage = (payload && payload.usage) || {};
    return {
      kind: 'agent',
      name: (payload && (payload.subagent_type || payload.agent_id)) || 'unknown',
      tokens: Number(usage.total_tokens) || 0,
      durationMs: Number(payload && payload.duration_ms) || 0,
    };
  }
  if (event === 'PostToolUse') {
    return {
      kind: 'tool',
      name: (payload && payload.tool_name) || 'unknown',
      tokens: 0,
      durationMs: Number(payload && payload.duration_ms) || 0,
    };
  }
  return null;
}

function scaffold() {
  return [
    '<!-- managed by bundle ia-stats — do not edit by hand -->',
    '# IA stats',
    '',
    '## Running totals',
    '',
    '| Kind | Name | Calls | Total tokens | Last invoked (UTC) |',
    '|---|---|---:|---:|---|',
    '',
    '## Recent activity (last 50)',
    '',
    '| Timestamp (UTC) | Event | Name | Tokens | Duration (ms) |',
    '|---|---|---|---:|---:|',
  ].join('\n') + '\n';
}

/** Naive parser : reads totals + activity rows from the current file. */
function parseExisting(text) {
  const totals = new Map();
  const activity = [];
  if (!text || !text.trim()) return { totals, activity };
  let section = null;
  for (const line of text.split(/\r?\n/)) {
    if (line.startsWith('## Running totals')) { section = 'totals'; continue; }
    if (line.startsWith('## Recent activity')) { section = 'activity'; continue; }
    if (!line.startsWith('|') || line.startsWith('|---') || /Calls|Timestamp/.test(line)) continue;
    const cells = line.split('|').map(c => c.trim()).filter((_, i, arr) => i > 0 && i < arr.length - 1);
    if (section === 'totals' && cells.length === 5) {
      const [kind, name, calls, tokens, last] = cells;
      const cN = parseInt(calls, 10);
      const tN = parseInt(tokens, 10);
      if (!Number.isNaN(cN) && !Number.isNaN(tN)) {
        totals.set(`${kind}::${name}`, { kind, name, calls: cN, tokens: tN, last });
      }
    } else if (section === 'activity' && cells.length === 5) {
      const [ts, ev, name, tokens, dur] = cells;
      const tN = parseInt(tokens, 10);
      const dN = parseInt(dur, 10);
      if (!Number.isNaN(tN) && !Number.isNaN(dN)) {
        activity.push({ ts, event: ev, name, tokens: tN, durationMs: dN });
      }
    }
  }
  return { totals, activity };
}

function render(totals, activity) {
  const totalsRows = [...totals.values()]
    .sort((a, b) => (a.kind.localeCompare(b.kind) || a.name.localeCompare(b.name)))
    .map(r => `| ${r.kind} | ${r.name} | ${r.calls} | ${r.tokens} | ${r.last} |`);
  const recent = activity.slice(-MAX_RECENT)
    .map(r => `| ${r.ts} | ${r.event} | ${r.name} | ${r.tokens} | ${r.durationMs} |`);
  return [
    '<!-- managed by bundle ia-stats — do not edit by hand -->',
    '# IA stats',
    '',
    '## Running totals',
    '',
    '| Kind | Name | Calls | Total tokens | Last invoked (UTC) |',
    '|---|---|---:|---:|---|',
    ...totalsRows,
    '',
    '## Recent activity (last 50)',
    '',
    '| Timestamp (UTC) | Event | Name | Tokens | Duration (ms) |',
    '|---|---|---|---:|---:|',
    ...recent,
  ].join('\n') + '\n';
}

/** Best-effort cross-platform lock via O_EXCL on a sibling .lock file. */
async function withLock(target, fn) {
  const lockPath = target + '.lock';
  let fd = null;
  for (let i = 0; i < LOCK_RETRIES; i++) {
    try {
      fd = fs.openSync(lockPath, 'wx');
      break;
    } catch (e) {
      if (e.code === 'EEXIST') {
        await new Promise(r => setTimeout(r, LOCK_SLEEP_MS));
        continue;
      }
      throw e;
    }
  }
  try {
    await fn();
  } finally {
    if (fd !== null) {
      try { fs.closeSync(fd); } catch {}
      try { fs.unlinkSync(lockPath); } catch {}
    }
  }
}

function atomicWrite(target, content) {
  const tmp = target + '.tmp';
  fs.writeFileSync(tmp, content, { encoding: 'utf8' });
  fs.renameSync(tmp, target);
}

async function main() {
  const { event, file } = parseArgs(process.argv.slice(2));
  if (!event) {
    process.stderr.write('[ia-stats] missing --event\n');
    return 0;
  }
  const raw = await readStdin();
  const payload = safeParse(raw);
  const row = extractRow(event, payload);
  if (!row) return 0;

  const target = path.resolve(file);
  const dir = path.dirname(target);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  if (!fs.existsSync(target)) atomicWrite(target, scaffold());

  await withLock(target, () => {
    const current = fs.readFileSync(target, 'utf8');
    const { totals, activity } = parseExisting(current);
    const key = `${row.kind}::${row.name}`;
    const now = nowIso();
    const slot = totals.get(key) || { kind: row.kind, name: row.name, calls: 0, tokens: 0, last: '' };
    slot.calls += 1;
    slot.tokens += row.tokens;
    slot.last = now;
    totals.set(key, slot);
    activity.push({ ts: now, event, name: row.name, tokens: row.tokens, durationMs: row.durationMs });
    atomicWrite(target, render(totals, activity));
  });

  return 0;
}

main()
  .then(code => process.exit(code))
  .catch(err => {
    process.stderr.write(`[ia-stats] append failed: ${err && err.message ? err.message : err}\n`);
    process.exit(0);
  });
