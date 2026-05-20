# {{project_name}} — Technical specification

<!--
  MACRO TEMPLATE — filled by `smith-technical-doc-writer` during
  `/smith-generate-docs`. Each `{{placeholder}}` is substituted by the
  agent with content derived from the project source. Section headers
  are fixed ; the agent never invents new top-level sections, never
  removes existing ones. Missing content → "_Not applicable_".
-->

## 1. Architecture

{{architecture_overview_paragraph}}

```mermaid
{{architecture_mermaid}}
```

<!--
  Two-to-three paragraph high-level overview, then a Mermaid diagram
  if a clean one can be inferred. If not, omit the fenced block (never
  fabricate edges).
-->

## 2. Modules

{{modules_table}}

<!--
  | Module | Purpose | Outgoing deps |
  |---|---|---|
  | {{name}} | {{1-sentence}} | {{intra-project + external}} |

  One row per top-level module. Names quoted in prose MUST match real
  symbols — grep to verify before writing.
-->

## 3. Inbound interfaces

{{inbound_interfaces_list}}

<!--
  Per interface family : REST (base URL + OpenAPI doc path + auth),
  gRPC, GraphQL, CLI, scheduled jobs, webhooks. If absent → "_Not applicable_".
-->

## 4. Persistence

{{persistence_description}}

<!--
  Detect the persistence layer (JPA + Liquibase / Mongo / DynamoDB / SQLite
  / none). Provide an ER-like description of main entities — bulleted
  list or Mermaid `erDiagram` block. Include the dual-id pattern if used.
-->

## 5. Cross-cutting concerns

- **Auth** — {{auth_summary}}
- **Logging** — {{logging_summary}}
- **Metrics** — {{metrics_summary}}
- **Caching** — {{caching_summary}}
- **Async** — {{async_summary}}

<!--
  One line per concern. Omit a line entirely if not applicable to this
  project (e.g. no caching layer).
-->

## 6. Build + CI

- **Build tool** — {{build_tool_name}} {{build_tool_version}}
- **CI** — {{ci_platform}} ; key workflows : {{ci_workflows_list}}
- **Local dev** — `{{local_dev_command}}`

## 7. Known gaps

{{known_gaps_list}}

<!--
  Bullet list of architectural smells, deferred decisions, partition
  plans, missing tests, etc. that surfaced during the scan. Be honest —
  this is the section a senior engineer reads first.
-->
