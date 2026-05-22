// dashboard-ai — React UI for the Smith project dashboard.
// Loaded as an ES module. Uses React + htm via CDN — no JSX, no Babel, no
// bundler. Pure DOM + React.createElement under the hood.

import htm from "https://unpkg.com/htm@3.1.1/dist/htm.module.js?module";

const html = htm.bind(React.createElement);
const { useEffect, useState, useMemo } = React;

const FILTERS = [
  { id: "all",     label: "All" },
  { id: "bin",     label: "Bin" },
  { id: "adapted", label: "Adapted" },
  { id: "bundle",  label: "Bundle" },
];

function App() {
  const [data, setData]     = useState(null);
  const [error, setError]   = useState(null);
  const [query, setQuery]   = useState("");
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetch("/api/dashboard")
      .then((r) => r.ok ? r.json() : r.json().then((b) => Promise.reject(b)))
      .then(setData)
      .catch((e) => setError(e));
  }, []);

  // Hooks MUST run unconditionally — never put a useMemo after an early
  // return, or the hook count changes between renders and React unmounts.
  const skills = useMemo(
    () => filterSkills(data?.skills || [], filter, query),
    [data, filter, query],
  );

  if (error) return html`<${ErrorBanner} error=${error} />`;
  if (!data)  return html`<div class="loading">Loading dashboard…</div>`;

  return html`
    <div class="layout">
      <${Header} project=${data.project} provider=${data.provider} generatedAt=${data.generated_at} />
      <${ProjectCard} project=${data.project} specs=${data.specifications} />
      <section class="section">
        <header class="section-header">
          <h2>Skills <span class="badge">${data.skills?.length ?? 0}</span></h2>
          <div class="controls">
            <input
              class="search"
              type="search"
              placeholder="Filter by name or description…"
              value=${query}
              onInput=${(e) => setQuery(e.target.value)}
            />
            <div class="pills">
              ${FILTERS.map((f) => html`
                <button
                  key=${f.id}
                  class=${`pill ${filter === f.id ? "pill-on" : ""}`}
                  onClick=${() => setFilter(f.id)}>${f.label}</button>
              `)}
            </div>
          </div>
        </header>
        <${SkillsGrid} skills=${skills} />
      </section>
      <section class="section">
        <header class="section-header">
          <h2>Agents <span class="badge">${data.agents?.length ?? 0}</span></h2>
        </header>
        <${AgentsGrid} agents=${data.agents || []} />
      </section>
      <section class="section">
        <header class="section-header">
          <h2>Bundles <span class="badge">${data.bundles?.length ?? 0}</span></h2>
        </header>
        <${BundlesGrid} bundles=${data.bundles || []} />
      </section>
    </div>
  `;
}

function filterSkills(skills, filter, query) {
  const q = query.trim().toLowerCase();
  return skills.filter((s) => {
    if (filter !== "all") {
      const source = s.source || "";
      if (filter === "bin"     && source !== "bin")           return false;
      if (filter === "adapted" && source !== "adapted")       return false;
      if (filter === "bundle"  && !source.startsWith("bundle:")) return false;
    }
    if (!q) return true;
    return (s.name || "").toLowerCase().includes(q)
        || (s.description || "").toLowerCase().includes(q);
  });
}

function Header({ project, provider, generatedAt }) {
  return html`
    <header class="topbar">
      <div class="topbar-left">
        <span class="logo">⚒</span>
        <div>
          <h1>${project?.name || "Smith Project"}</h1>
          <p class="subtitle">${project?.summary || project?.description || ""}</p>
        </div>
      </div>
      <div class="topbar-right">
        <span class="tag tag-provider">${provider || "?"}</span>
        <span class="meta">Generated ${formatDate(generatedAt)}</span>
      </div>
    </header>
  `;
}

function ProjectCard({ project, specs }) {
  if (!project) return null;
  const groups = [
    ["Languages",   project.languages],
    ["Runtimes",    project.runtimes],
    ["Frameworks",  project.frameworks],
    ["Build tools", project.build_tools],
    ["Test tools",  project.test_tools],
    ["Infra",       project.infra_tools],
    ["Databases",   project.databases],
  ];
  return html`
    <section class="card project">
      <h2>Project</h2>
      <p class="muted">${project.description || ""}</p>
      <dl class="stack">
        ${groups.map(([label, items]) => html`
          <div class="stack-row" key=${label}>
            <dt>${label}</dt>
            <dd>${
              !items || items.length === 0
                ? html`<span class="empty">—</span>`
                : items.map((it) => html`<span class="chip" key=${it.name}>${it.name}${it.version ? ` ${it.version}` : ""}</span>`)
            }</dd>
          </div>
        `)}
      </dl>
      ${specs && html`
        <div class="specs">
          ${specs.functional && html`<span class="spec-link">📄 ${specs.functional}</span>`}
          ${specs.technical && html`<span class="spec-link">📄 ${specs.technical}</span>`}
          ${specs.agents_md && html`<span class="spec-link">🤖 ${specs.agents_md}</span>`}
        </div>
      `}
    </section>
  `;
}

function SkillsGrid({ skills }) {
  if (skills.length === 0) {
    return html`<p class="empty-state">No skills match your filter.</p>`;
  }
  return html`
    <div class="grid">
      ${skills.map((s) => html`<${SkillCard} key=${s.name} skill=${s} />`)}
    </div>
  `;
}

function SkillCard({ skill }) {
  const sourceLabel = skill.source?.startsWith("bundle:")
    ? `bundle · ${skill.source.slice("bundle:".length)}`
    : skill.source || "—";
  return html`
    <article class="card skill-card">
      <header>
        <h3>${skill.name}</h3>
        <span class=${`badge badge-${(skill.source || "").split(":")[0] || "unknown"}`}>${sourceLabel}</span>
      </header>
      <p class="desc">${skill.description || html`<span class="empty">(no description)</span>`}</p>
      ${skill.user_invocable && skill.invocation ? html`
        <div class="invocation">
          <span class="invocation-label">Invoke</span>
          <code>${skill.invocation}</code>
          <button class="copy" title="Copy to clipboard" onClick=${() => copy(skill.invocation)}>copy</button>
        </div>
      ` : html`
        <div class="invocation invocation-disabled" title="Not user-invocable for this provider">
          <span class="invocation-label">Internal</span>
        </div>
      `}
      <footer><span class="path" title=${skill.path}>${skill.path}</span></footer>
    </article>
  `;
}

function AgentsGrid({ agents }) {
  if (agents.length === 0) {
    return html`<p class="empty-state">No agents installed.</p>`;
  }
  return html`
    <div class="grid">
      ${agents.map((a) => html`
        <article class="card agent-card" key=${a.name}>
          <header>
            <h3>${a.name}</h3>
            <span class="badge badge-agent">agent</span>
          </header>
          <p class="desc">${a.description || html`<span class="empty">(no description)</span>`}</p>
          <footer><span class="path" title=${a.path}>${a.path}</span></footer>
        </article>
      `)}
    </div>
  `;
}

function BundlesGrid({ bundles }) {
  if (bundles.length === 0) {
    return html`<p class="empty-state">No bundles installed.</p>`;
  }
  return html`
    <div class="grid">
      ${bundles.map((b) => html`
        <article class="card bundle-card" key=${b.name}>
          <header>
            <h3>${b.name}</h3>
            <div class="badges">
              <span class="badge badge-version">v${b.version}</span>
              ${b.core && html`<span class="badge badge-core">core</span>`}
            </div>
          </header>
          <div class="tags">
            ${(b.tags || []).map((t) => html`<span class="chip chip-tag" key=${t}>${t}</span>`)}
          </div>
          <p class="muted">Installed ${formatDate(b.installed_at)}</p>
          <ul class="bundle-skills">
            ${(b.skill_names || []).map((s) => html`<li key=${s}><code>${s}</code></li>`)}
          </ul>
        </article>
      `)}
    </div>
  `;
}

function ErrorBanner({ error }) {
  return html`
    <div class="error">
      <h2>Dashboard data unavailable</h2>
      <p>${error.message || "unknown error"}</p>
      ${error.path && html`<p class="muted">Looked for : <code>${error.path}</code></p>`}
      <p class="muted">Re-run <code>/dashboard-ai</code> after fixing the issue.</p>
    </div>
  `;
}

function formatDate(iso) {
  if (!iso) return "—";
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function copy(value) {
  if (!navigator.clipboard) return;
  navigator.clipboard.writeText(value).catch(() => {});
}

ReactDOM.createRoot(document.getElementById("root")).render(html`<${App} />`);
