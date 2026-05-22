#!/usr/bin/env node
// dashboard-ai — zero-deps Node HTTP server.
//
// Discovers everything by scanning the consumer's filesystem from
// the templates declared in .smith/paths.yaml. No hardcoded list
// of providers, skills, or agents — re-shipping a new release
// with new providers or new skills does NOT require touching this
// file.

const http = require("node:http");
const fs   = require("node:fs");
const path = require("node:path");
const url  = require("node:url");

// ---------------------------------------------------------------------------
// CLI
// ---------------------------------------------------------------------------

function parseArgs(argv) {
  const out = { port: null, root: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--port") out.port = parseInt(argv[++i], 10);
    else if (a === "--root") out.root = argv[++i];
    else if (a === "--help") {
      console.log("usage: node server.js --port <n> --root <consumer-abs-path>");
      process.exit(0);
    }
  }
  if (!out.port || Number.isNaN(out.port)) { console.error("error: --port required"); process.exit(2); }
  if (!out.root) { console.error("error: --root required"); process.exit(2); }
  return out;
}

const args = parseArgs(process.argv.slice(2));
const ROOT = path.resolve(args.root);
const WEB_ROOT = path.join(__dirname, "web");

// ---------------------------------------------------------------------------
// Tiny YAML / frontmatter readers (only the shapes we need)
// ---------------------------------------------------------------------------

function readFlatYaml(file) {
  // Handles flat `key: value` shapes only — paths.yaml and frontmatter blocks.
  // null forms: `~`, `null`, empty. Quoted: '"…"' or "'…'".
  const lines = fs.readFileSync(file, "utf8").split(/\r?\n/);
  return parseFlatYamlLines(lines);
}

function parseFlatYamlLines(lines) {
  const out = {};
  for (const line of lines) {
    const m = line.match(/^([a-zA-Z_][a-zA-Z0-9_-]*)\s*:\s*(.*?)\s*(?:#.*)?$/);
    if (!m) continue;
    let val = m[2];
    if (val === "" || val === "~" || val === "null") val = null;
    else if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) val = val.slice(1, -1);
    else if (val === "true") val = true;
    else if (val === "false") val = false;
    out[m[1]] = val;
  }
  return out;
}

function readFrontmatter(file) {
  let content;
  try { content = fs.readFileSync(file, "utf8"); } catch { return {}; }
  if (!content.startsWith("---")) return {};
  const lines = content.split(/\r?\n/);
  const block = [];
  // skip the opening ---, collect until the closing ---
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim() === "---") break;
    block.push(lines[i]);
  }
  return parseFlatYamlLines(block);
}

function readJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); }
  catch { return fallback; }
}

// ---------------------------------------------------------------------------
// Path-template enumeration
// ---------------------------------------------------------------------------

function enumerateSlugs(rootDir, template) {
  // template = "<dir>/{slug}/<rest>" (folder-style — slug is a directory)
  //         or "<dir>/{slug}<ext>"   (flat-file style — slug is a filename stem)
  // We split on "{slug}", list the parent directory, and accept the entries
  // that match. The function is purely template-driven — no knowledge of
  // which provider, runtime, or convention is in play.
  if (!template || !template.includes("{slug}")) return [];
  const [prefix, suffix] = template.split("{slug}");
  // The directory we list is the path obtained by stripping the trailing
  // path segment of `prefix`. If suffix starts with "/", `prefix` ends
  // with the parent dir + trailing "/", so `path.dirname(prefix + "X")`
  // is exactly that parent.
  const parentRel = path.dirname(prefix + "X");
  const parentAbs = path.resolve(rootDir, parentRel);
  if (!fs.existsSync(parentAbs)) return [];

  const entries = [];
  const folderStyle = suffix.startsWith("/");
  for (const name of fs.readdirSync(parentAbs)) {
    const candidateAbs = path.resolve(rootDir, prefix + name + suffix);
    if (folderStyle) {
      // {slug}/<rest> — the entry under parent is a directory named after the slug.
      const stat = safeStat(path.join(parentAbs, name));
      if (!stat || !stat.isDirectory()) continue;
      if (!fs.existsSync(candidateAbs)) continue;
      entries.push({ slug: name, path: candidateAbs });
    } else {
      // {slug}<ext> — the entry under parent is a file ending with <ext>.
      if (suffix && !name.endsWith(suffix)) continue;
      const slug = suffix ? name.slice(0, -suffix.length) : name;
      if (!fs.existsSync(candidateAbs)) continue;
      const stat = safeStat(candidateAbs);
      if (!stat || !stat.isFile()) continue;
      entries.push({ slug, path: candidateAbs });
    }
  }
  // Stable ordering.
  entries.sort((a, b) => a.slug.localeCompare(b.slug));
  return entries;
}

function safeStat(p) { try { return fs.statSync(p); } catch { return null; } }

// ---------------------------------------------------------------------------
// Discovery — the actual dashboard payload
// ---------------------------------------------------------------------------

function discover() {
  const pathsYaml = path.join(ROOT, ".smith", "paths.yaml");
  if (!fs.existsSync(pathsYaml)) {
    throw Object.assign(new Error("paths.yaml not found"), {
      code: "paths-yaml-missing",
      hint: "Re-run /smith-bundle-install --name dashboard-ai to propagate paths.yaml into .smith/.",
    });
  }
  const paths = readFlatYaml(pathsYaml);

  const smithYaml      = readFlatYaml(path.join(ROOT, ".smith", "smith.yaml"));
  const architecture   = readJson(path.join(ROOT, ".smith", "architecture.json"), { project: {} });
  const config         = readJson(path.join(ROOT, ".smith", "config.json"),       {});

  // Build the cross-reference index: which slug came from which source ?
  // - "adapted"        : listed in config.skills[]
  // - "bundle:<slug>"  : listed in some config.bundles[].skills[]
  // - "bin"            : discovered on disk but absent from both indexes
  const adaptedSlugs = new Map(); // slug -> entry
  for (const s of config.skills || []) adaptedSlugs.set(s.name, s);

  const bundleOriginBySlug = new Map(); // slug -> bundle name
  for (const b of config.bundles || []) {
    for (const s of b.skills || []) bundleOriginBySlug.set(s.name, b.name);
  }

  // Skills.
  const skills = enumerateSlugs(ROOT, paths.skill).map((entry) => {
    const fm = readFrontmatter(entry.path);
    const source =
      adaptedSlugs.has(entry.slug)         ? "adapted" :
      bundleOriginBySlug.has(entry.slug)   ? `bundle:${bundleOriginBySlug.get(entry.slug)}` :
                                              "bin";

    // user_invocable: explicit frontmatter value wins, else default by
    // whether the provider exposes a slash command at all.
    let userInvocable;
    if (typeof fm["user-invocable"] === "boolean") userInvocable = fm["user-invocable"];
    else userInvocable = paths.skill_invocation != null;

    const invocation = (userInvocable && paths.skill_invocation)
      ? paths.skill_invocation.replace("{slug}", entry.slug)
      : null;

    return {
      name:           fm.name || entry.slug,
      description:    truncate(fm.description, 240),
      source,
      path:           path.relative(ROOT, entry.path),
      user_invocable: userInvocable,
      invocation,
    };
  });

  // Agents.
  const agents = enumerateSlugs(ROOT, paths.agent).map((entry) => {
    const fm = readFrontmatter(entry.path);
    const userInvocable = (paths.agent_invocation != null);
    const invocation = userInvocable
      ? paths.agent_invocation.replace("{slug}", entry.slug)
      : null;
    return {
      name:           fm.name || entry.slug,
      description:    truncate(fm.description, 240),
      path:           path.relative(ROOT, entry.path),
      user_invocable: userInvocable,
      invocation,
    };
  });

  // Bundles — already in config.json. Pass through the shape the UI expects.
  const bundles = (config.bundles || []).map((b) => ({
    name:         b.name,
    version:      b.version,
    tags:         b.tags || [],
    core:         b.core === true,
    installed_at: b.installed_at || null,
    skill_names:  (b.skills || []).map((s) => s.name),
    hook_names:   (b.hooks  || []).map((h) => h.name),
  })).sort((a, b) => a.name.localeCompare(b.name));

  return {
    version:        1,
    generated_at:   new Date().toISOString(),
    provider:       smithYaml.provider || config.provider || null,
    project:        architecture.project || {},
    specifications: {
      functional: config.specifications?.functional || null,
      technical:  config.specifications?.technical  || null,
      agents_md:  config.ai_memory_file || "AGENTS.md",
    },
    bundles,
    skills:  skills.sort((a, b) => a.name.localeCompare(b.name)),
    agents:  agents.sort((a, b) => a.name.localeCompare(b.name)),
  };
}

function truncate(s, n) {
  if (s == null) return null;
  if (s.length <= n) return s;
  return s.slice(0, n - 1) + "…";
}

// ---------------------------------------------------------------------------
// Snapshot writer (one-shot at startup — fulfils the "produce a JSON file"
// part of the bundle brief without forcing the AI to compose it).
// ---------------------------------------------------------------------------

function writeSnapshot() {
  try {
    const snapshot = discover();
    const file = path.join(ROOT, ".smith", "dashboard.json");
    fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file + ".tmp", JSON.stringify(snapshot, null, 2));
    fs.renameSync(file + ".tmp", file);
  } catch (err) {
    // Non-fatal — log and keep going. The live endpoint will surface the
    // real error to the user.
    console.error(`[snapshot] ${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// HTTP server — static UI + JSON endpoints
// ---------------------------------------------------------------------------

const MIME = {
  ".html": "text/html; charset=utf-8",
  ".js":   "application/javascript; charset=utf-8",
  ".mjs":  "application/javascript; charset=utf-8",
  ".css":  "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg":  "image/svg+xml",
  ".png":  "image/png",
  ".ico":  "image/x-icon",
};

function sendJson(res, status, payload) {
  const body = JSON.stringify(payload, null, 2);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(body),
    "cache-control": "no-store",
  });
  res.end(body);
}

function serveStatic(req, res, urlPath) {
  let rel = urlPath === "/" ? "/index.html" : urlPath;
  rel = rel.replace(/^\/+/, "");
  const absolute = path.resolve(WEB_ROOT, rel);
  if (!absolute.startsWith(WEB_ROOT + path.sep) && absolute !== WEB_ROOT) {
    res.writeHead(403); res.end("forbidden"); return;
  }
  fs.stat(absolute, (err, stat) => {
    if (err || !stat.isFile()) { res.writeHead(404); res.end("not found"); return; }
    const ext = path.extname(absolute).toLowerCase();
    res.writeHead(200, {
      "content-type": MIME[ext] || "application/octet-stream",
      "content-length": stat.size,
      "cache-control": "no-store",
    });
    fs.createReadStream(absolute).pipe(res);
  });
}

const server = http.createServer((req, res) => {
  const p = (url.parse(req.url, true).pathname) || "/";

  if (p === "/api/dashboard") {
    try { sendJson(res, 200, discover()); }
    catch (err) {
      sendJson(res, 500, { error: err.code || "discovery-failed", message: err.message, hint: err.hint || null });
    }
    return;
  }

  if (p === "/api/health") {
    return sendJson(res, 200, { status: "ok", root: ROOT });
  }

  serveStatic(req, res, p);
});

server.on("error", (err) => {
  if (err.code === "EADDRINUSE") { console.error(`error: port ${args.port} already in use`); process.exit(3); }
  console.error(`server error: ${err.message}`); process.exit(1);
});

server.listen(args.port, "127.0.0.1", () => {
  writeSnapshot();
  // Skill body captures this line — keep the format stable.
  console.log(`Dashboard ready → http://127.0.0.1:${args.port}`);
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => server.close(() => process.exit(0)));
}
