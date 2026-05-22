---
name: smith-angular-standards
description: Angular 21 coding standards — strict TypeScript, signals, signal stores, separation of .html/.ts, standalone components, zoneless.
---


# Skill — Angular 21 patterns

Cardinal quality bar lives in `.claude/rules/angular/`. This skill carries the patterns specific to Smith — component shape, signal store contract, routing, forms.

## Component conventions

- **Standalone only**, **`templateUrl` + `styleUrl`** (never inline `template:`), **OnPush** is the default — keep it.
- **Signal-based APIs**: `input()` / `input.required()` / `output()`. Avoid `@Input` / `@Output` decorators in new code.
- **Selector** `app-<feature>-<name>` (kebab-case), files `<name>.component.{ts,html}`. > 250 lines is a smell.
- Every input/output/method has TSDoc.

```typescript
// users-list.component.ts
import { Component, input, output, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { TranslocoModule } from '@jsverse/transloco';

import { User } from '@app/api';

/**
 * Renders a list of users for selection in workspace administration screens.
 * Dumb component: no HTTP, no business rules — receives signals via inputs.
 */
@Component({
  selector: 'app-users-list',
  standalone: true,
  imports: [CommonModule, TranslocoModule],
  templateUrl: './users-list.component.html',
  styleUrl: './users-list.component.scss',
})
export class UsersListComponent {
  readonly users = input.required<readonly User[]>();
  readonly query = input<string>('');

  /** Emitted when a user row is selected. */
  readonly selected = output<User>();

  protected readonly filtered = computed(() =>
    this.users().filter(u => u.email.includes(this.query()))
  );
}
```

## Signal usage

- **State** → `signal()`. **Derivations** → `computed()`. **Side-effects** → `effect()` (or `afterNextRender` for DOM-only).
- **Async data at the boundary** → `toSignal(observable$)` or Angular 21 `rxResource()`.
- **No `subscribe()` in components** — convert to signal at the boundary, or use the `async` pipe. Stores may `subscribe` for imperative create/update/delete.
- **Immutable updates**: `signal.update(arr => [...arr, item])` — never `arr.push`.

## Signal store — mandatory pattern

Every feature has a store. The store injects one or more **TIER 2 HTTP clients** from `src/app/http-clients/` — never `HttpClient`, never imports a service from `@app/api` (DTO types are fine). Components never call HTTP at all.

```typescript
// features/workspaces/workspaces.store.ts
import { Injectable, computed, inject, signal } from '@angular/core';

import { WorkspacesHttpClient } from '@app/http-clients/workspaces.http-client';
import { WorkspaceDto } from '@app/api';

/**
 * Holds workspaces state for the current user.
 * Components read signals, never call HTTP directly.
 */
@Injectable({ providedIn: 'root' })
export class WorkspacesStore {
  private readonly http = inject(WorkspacesHttpClient);

  private readonly _selectedId = signal<string | null>(null);
  private readonly _workspaces = signal<readonly WorkspaceDto[]>([]);
  private readonly _loading = signal(false);
  private readonly _error = signal<string | null>(null);

  readonly workspaces = this._workspaces.asReadonly();
  readonly loading = this._loading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly selected = computed(() =>
    this._workspaces().find(w => w.id === this._selectedId()) ?? null
  );

  load(): void {
    this._loading.set(true);
    this._error.set(null);

    this.http.list().subscribe({
      next: (list) => this._workspaces.set(list),
      error: (e) => {
        this._error.set(toErrorMessage(e));
        this._loading.set(false);
      },
      complete: () => this._loading.set(false),
    });
  }

  select(id: string): void {
    this._selectedId.set(id);
  }
}
```

Rules:

- Private writable signals (`_x`), public `readonly` signals exposed via `.asReadonly()`.
- Public mutators are explicit methods (`load()`, `select()`, `add()`). Never expose setters.
- Inject only **TIER 2** clients from `src/app/http-clients/`. Never `HttpClient`, never a generated service from `@app/api`. See `smith-angular-openapi-client` for the TIER 1/2/3 architecture.
- Public methods return `void` (or `Observable<T>` for streams the caller composes). Never `Promise`.
- One store per feature. > 200 lines → split by concern.
- Multiple features can share the same TIER 2 client (shared by backend resource, not duplicated per consumer).

## Routing

- Lazy-loaded by feature: `loadChildren: () => import('./features/users/users.routes')`.
- Guards (`CanActivateFn`) live in `core/guards/`.
- Path-based locale prefix only when the design requires it; otherwise Transloco runtime switch is enough.

## Forms

- **Reactive forms** with typed `FormGroup<{}>`.
- Angular 21 Signal Forms (preview) allowed in greenfield features, must include unit tests covering validation.

## i18n & HTTP

User-visible text via Transloco — see `smith-angular-i18n-transloco`. HTTP architecture (TIER 1/2/3, generation, error handling) — see `smith-angular-openapi-client`.
