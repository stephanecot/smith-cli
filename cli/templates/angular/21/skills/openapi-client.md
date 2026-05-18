
# Skill — Angular HTTP clients from OpenAPI (no improvisation)

The frontend consumes a backend artifact: **`backend/openapi/openapi.json`** (and `.yaml`). That file is the **single source of truth** — the frontend never re-fetches `/v3/api-docs` from a running backend.

**This skill never triggers backend builds.** The contract is produced by the `smith-backend-developer` agent (`mvn -f backend/pom.xml -Popenapi verify`). If `backend/openapi/openapi.json` is missing or stale, **stop and delegate** — do not run Maven from this skill.

## Tooling

- Generator: [`@openapitools/openapi-generator-cli`](https://www.npmjs.com/package/@openapitools/openapi-generator-cli) — pinned in `frontend/devDependencies`.
- Generator type: `typescript-angular` (Angular 21-compatible).

```bash
cd frontend
npm install -D @openapitools/openapi-generator-cli
```

## Three-tier HTTP architecture

```
component  →  store (signals)  →  HTTP client (hand-written, shared)  →  generated OpenAPI service (auto)  →  HttpClient  →  backend
                                  ────────────────────────────────────    ─────────────────────────────────
                                  TIER 2 — one per backend resource       TIER 1 — regenerated, never edited
```

| Tier | Lives in | Owned by | What it does |
|---|---|---|---|
| 1. Generated services | `frontend/src/app/api/` | the generator (do not edit) | Wraps `HttpClient` with typed methods + DTO interfaces matching the backend contract. |
| 2. HTTP client (shared) | `frontend/src/app/http-clients/<resource>.http-client.ts` | the team (hand-written) | Thin façade over the generated service. **One client per backend resource / OpenAPI tag**, shared across features. The **only** place a store reaches for HTTP. May translate generated DTOs into domain models, normalize errors, compose endpoints. |
| 3. Store | `frontend/src/app/features/<feature>/<feature>.store.ts` | the team (hand-written) | Holds signals. Calls one or more TIER 2 clients. Never imports from `@app/api` services, never injects `HttpClient`. |

**Rules**:

- TIER 2 clients are organized by **backend resource** (mirroring the OpenAPI tag), not by frontend feature: `Workspaces` → `workspaces.http-client.ts`. One generated `*Service` ↔ one TIER 2 `*HttpClient`.
- A feature store may inject **multiple** TIER 2 clients.
- TIER 2 is the only Angular code allowed to import services from `@app/api`. Stores may import generated **DTO types** for typing, never services.
- Components depend on stores only.
- TIER 2 always returns `Observable`. Stores expose signals. Full reactivity hierarchy in `smith-angular-standards` and `.claude/rules/angular/code-quality.md`.

## Workflow

### Precondition — `backend/openapi/openapi.json` exists and is current

If missing or stale, **stop and delegate to `smith-backend-developer`**.

### Step 1 — frontend regenerates TIER 1 from the existing contract

```bash
cd frontend
npm run api:generate
```

This runs `scripts/generate-api-client.mjs`, which:

1. Resolves the contract path (default `../backend/openapi/openapi.json`, override via `OPENAPI_SPEC=path`).
2. Fails fast with a clear error pointing to the Java agent when the file is missing.
3. Invokes `openapi-generator-cli` with `typescript-angular`, output `src/app/api/`.

```javascript
// frontend/scripts/generate-api-client.mjs
import { execSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';

const SPEC_PATH = resolve(process.env.OPENAPI_SPEC ?? '../backend/openapi/openapi.json');

if (!existsSync(SPEC_PATH)) {
  console.error(
    `OpenAPI contract not found at ${SPEC_PATH}.\n` +
      'Ask the backend agent (java-springboot-developer) to regenerate it. ' +
      'This script never invokes Maven on its own.',
  );
  process.exit(1);
}

execSync(
  'npx openapi-generator-cli generate ' +
    `-i "${SPEC_PATH}" -g typescript-angular -o src/app/api ` +
    '--additional-properties=' +
    [
      'ngVersion=21.0.0',
      'providedIn=root',
      'fileNaming=kebab-case',
      'enumPropertyNaming=UPPERCASE',
      'modelPropertyNaming=camelCase',
      'withInterfaces=true',
      'useSingleRequestParameter=true',
      'taggedUnions=true',
      'stringEnums=true',
    ].join(','),
  { stdio: 'inherit' },
);
```

`package.json`: `"api:generate": "node scripts/generate-api-client.mjs"`. No "online" mode — the contract is always loaded from disk. CI is reproducible because `backend/openapi/` is committed.

### Step 2 — provide the generated module

```typescript
// app.config.ts
import { provideHttpClient } from '@angular/common/http';
import { ApiModule, Configuration } from './api';

export const appConfig: ApplicationConfig = {
  providers: [
    provideHttpClient(/* + interceptors */),
    importProvidersFrom(ApiModule.forRoot(() =>
      new Configuration({ basePath: environment.apiBaseUrl })
    )),
  ],
};
```

### Step 3 — write the shared TIER 2 HTTP client

A small hand-written class wrapping the generated service for one backend resource.

```typescript
// frontend/src/app/http-clients/workspaces.http-client.ts
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { WorkspacesService, WorkspaceDto } from '@app/api'; // <-- TIER 1, generated

/**
 * HTTP-level façade over the generated WorkspacesService.
 * Single client for the Workspaces backend resource — every store that needs
 * workspace data injects this class. @app/api services are imported only here.
 */
@Injectable({ providedIn: 'root' })
export class WorkspacesHttpClient {

  private readonly api = inject(WorkspacesService); // generated

  list(): Observable<readonly WorkspaceDto[]> {
    return this.api.listWorkspaces();
  }

  getById(id: string): Observable<WorkspaceDto> {
    return this.api.getWorkspace({ id });
  }

  create(payload: CreateWorkspacePayload): Observable<WorkspaceDto> {
    return this.api.createWorkspace({ createWorkspaceRequest: payload });
  }
}
```

What belongs in TIER 2:

- **One method per logical operation** stores need. Domain verbs (`list`, `getById`, `create`) — not generator-style names (`workspacesGet`, `workspacesIdGet`).
- **Cross-endpoint composition** when it improves ergonomics (e.g., fetch workspace + members in parallel, return one Observable).
- **Domain-model translation** when the team decouples UI from generated DTO shapes.
- **Error normalization** — convert generator errors to a stable `SmithApiError` shape.
- **Always Observables.** Never `Promise`, never plain values.

Not here: signals/state (store's job), direct `HttpClient` calls (the generated service already wraps it — if you reach for `HttpClient`, the endpoint is missing from the spec).

### Step 4 — consume in the store (TIER 3)

The canonical store pattern (explicit `subscribe` + signal writes for imperative `load()` / `create()` / `update()` / `delete()`) lives in `smith-angular-standards` § *Signal store*. For **read-on-mount data keyed on a signal**, prefer the declarative `rxResource` idiom — eliminates manual `subscribe`, gives loading/error signals for free:

```typescript
import { Injectable, computed, inject, signal } from '@angular/core';
import { rxResource } from '@angular/core/rxjs-interop';

import { WorkspacesHttpClient } from '@app/http-clients/workspaces.http-client';
import { WorkspaceDto } from '@app/api';

@Injectable({ providedIn: 'root' })
export class WorkspacesStore {

  private readonly http = inject(WorkspacesHttpClient);
  private readonly _refreshTick = signal(0);

  private readonly resource = rxResource({
    request: () => this._refreshTick(),
    loader: () => this.http.list(),
  });

  readonly workspaces = computed<readonly WorkspaceDto[]>(() => this.resource.value() ?? []);
  readonly loading = this.resource.isLoading;
  readonly error = computed(() => this.resource.error()?.message ?? null);

  refresh(): void {
    this._refreshTick.update(n => n + 1);
  }
}
```

Rule of thumb:
- **Read-on-mount + refresh** → `rxResource`.
- **Imperative side-effects** (create / update / delete that mutate state) → explicit `subscribe` (see `smith-angular-standards`).
- **Never** `firstValueFrom` / `await` to "simplify" — Promise is the lowest tier.

## Forbidden

- **Calling `HttpClient` directly for a documented endpoint.** If a method is missing from the generated service, add the endpoint to the OpenAPI spec and regenerate.
- **Importing services from `@app/api` outside TIER 2.** Only `*.http-client.ts` may import generated services. DTO types are fine anywhere.
- **Editing files under `frontend/src/app/api/` by hand.** Add `src/app/api/**` to `.eslintignore` and `.prettierignore`. CI verifies the directory matches a freshly generated snapshot.
- **Per-feature TIER 2 clients.** TIER 2 mirrors backend resources / OpenAPI tags, not features.
- **Returning Promises from TIER 2.** Always Observables. `firstValueFrom` only inside tests.
- **Generating from a live `/v3/api-docs` endpoint.** Only the committed `backend/openapi/openapi.json` is acceptable.

## Drift detection

```bash
cd frontend && npm run api:generate
git diff --exit-code src/app/api
```

Non-zero exit → the generated client is stale relative to the contract. Regenerate and commit. If the contract itself looks wrong, ask the backend agent.

## Done criteria

A frontend change consuming a backend endpoint is complete only if:

1. `backend/openapi/openapi.json` exists and contains the endpoint(s). If not, delegate to the Java agent.
2. `frontend/src/app/api/` is regenerated (`npm run api:generate`) — no manual edits.
3. The TIER 2 client exists in `frontend/src/app/http-clients/<resource>.http-client.ts` (one per backend resource).
4. TIER 2 has unit tests stubbing the generated service.
5. The TIER 3 store has unit tests stubbing the TIER 2 client.
6. The store exposes signals only — no `firstValueFrom` / `await` in production code.
7. No new `HttpClient` usage outside `frontend/src/app/api/` and global interceptors.
8. The PR diff shows the regenerated `src/app/api/` alongside the new/changed `http-clients/<resource>.http-client.ts`, the consuming store, and tests.
