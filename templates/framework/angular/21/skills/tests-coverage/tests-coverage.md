
# Skill — Angular tests & coverage (≥ 80%)

Angular 21 ships **Vitest** as default (Karma is gone).

## Coverage targets

- **Lines** ≥ 80%, **branches** ≥ 70%, **functions** ≥ 80%, **statements** ≥ 80% per project.

Configured in `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['src/test-setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      include: ['src/app/**/*.ts'],
      exclude: [
        'src/app/api/**',                 // generated OpenAPI client
        'src/**/*.routes.ts',
        'src/**/*.config.ts',
        'src/**/index.ts',
        'src/**/*.spec.ts',
        'src/main.ts',
      ],
      thresholds: { lines: 80, branches: 70, functions: 80, statements: 80 },
    },
  },
});
```

Add `@vitest/coverage-v8` as a devDependency.

## What to test, by layer

| Layer | What | How |
|---|---|---|
| Pure functions / utils | All branches | Plain Vitest `describe/it/expect` |
| Pipes | Transform output for inputs | `expect(pipe.transform(x)).toBe(y)` |
| Signals & stores | State transitions, computed values | Direct calls + `expect(store.signal()).toEqual(...)` |
| Services / interceptors | HTTP behavior | Mock `HttpClient` or use `provideHttpClientTesting()` |
| Dumb components | Render + emits | `@analogjs/vitest-angular` or `@testing-library/angular` |
| Smart components / pages | Wire-up store ↔ view | Same as dumb + spy on store methods |
| i18n | Translation key presence | Snapshot of compiled template via Transloco test harness |

## Conventions

- **Naming**: `<feature>.<unit>.spec.ts` next to the file under test.
- **AAA**: Arrange / Act / Assert blocks.
- **No `setTimeout`** — use `fakeAsync`/`tick` or async/await.
- **Testing Library** preferred for component tests (queries by role, label, text — not by selector). It mirrors how users interact.
- **Mock at boundaries**:
  - **Store tests** stub the **TIER 2 HTTP client**. Stores must not depend on generated services in tests — proves the architecture holds.
  - **TIER 2 client tests** stub the generated TIER 1 service.
  - Never stub `HttpClient` directly when a generated service exists.
- **Reactivity primitives in tests follow production hierarchy**: signals first, Observables second, Promises only when nothing else fits. Assert on signals (`store.workspaces()`); return Observables from mocks (`mockReturnValue(of(...))`). `firstValueFrom` only when the SUT exposes Observable APIs (acceptable in tests).
- **One assertion concept per test**.
- **Deterministic**: no real network, no real time. Inject `Clock`-like services or use Vitest fake timers.
- **Snapshot tests** allowed for stable HTML structures (cards, badges) — never for whole page templates.

## Signal store test pattern

The store depends on TIER 2 HTTP clients — that's the seam to mock. Mocked methods return Observables; assertions read signals.

```typescript
import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';

import { WorkspacesStore } from './workspaces.store';
import { WorkspacesHttpClient } from '@app/http-clients/workspaces.http-client';

describe('WorkspacesStore', () => {
  let store: WorkspacesStore;
  let http: { list: ReturnType<typeof vi.fn> };

  beforeEach(() => {
    http = { list: vi.fn() };
    TestBed.configureTestingModule({
      providers: [
        WorkspacesStore,
        { provide: WorkspacesHttpClient, useValue: http },
      ],
    });
    store = TestBed.inject(WorkspacesStore);
  });

  it('load_populatesWorkspacesAndClearsLoading', () => {
    http.list.mockReturnValue(of([{ id: '1', name: 'Smith' }]));
    store.load();

    expect(store.workspaces()).toEqual([{ id: '1', name: 'Smith' }]);
    expect(store.loading()).toBe(false);
    expect(store.error()).toBeNull();
  });

  it('load_onError_exposesErrorMessage', () => {
    http.list.mockReturnValue(throwError(() => new Error('boom')));
    store.load();

    expect(store.error()).toBe('boom');
    expect(store.loading()).toBe(false);
  });
});
```

For TIER 2 client tests, follow the same pattern: stub the generated `*Service` from `@app/api`, assert with `firstValueFrom(client.method())`. `firstValueFrom` is acceptable here because the SUT returns Observable.

## Component test pattern (Testing Library)

```typescript
import { render, screen } from '@testing-library/angular';
import { UsersListComponent } from './users-list.component';

describe('UsersListComponent', () => {
  it('filters users by query', async () => {
    await render(UsersListComponent, {
      inputs: { users: [{ id: '1', email: 'a@b.c' }, { id: '2', email: 'd@e.f' }], query: 'a@' },
    });

    expect(screen.getByText('a@b.c')).toBeInTheDocument();
    expect(screen.queryByText('d@e.f')).toBeNull();
  });

  it('emits selected when row is clicked', async () => {
    const onSelected = vi.fn();
    await render(UsersListComponent, {
      inputs: { users: [{ id: '1', email: 'a@b.c' }] },
      on: { selected: onSelected },
    });
    await userEvent.click(screen.getByText('a@b.c'));

    expect(onSelected).toHaveBeenCalledWith({ id: '1', email: 'a@b.c' });
  });
});
```

## Run

```bash
cd frontend
npm test                          # vitest run
npm test -- --watch               # local dev
npm test -- --coverage            # writes report under coverage/
```

## Done criteria

The agent must not declare an Angular change complete until:

1. `npm run lint` passes.
2. `npm test -- --coverage` is green and thresholds (80/70/80/80) are met.
3. New components have at least one render test + one interaction test.
4. New store methods have at least one happy-path test + one error-path test.
5. New OpenAPI-generated services don't need direct tests, but every store method that calls them does.
