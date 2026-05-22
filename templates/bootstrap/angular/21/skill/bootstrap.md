# Skill — bootstrap an Angular 21 project

Use this skill when the user asks to scaffold a new Angular 21 frontend
from scratch — the project root is empty (or contains only `.smith/`)
and the user wants a working `npm run build` baseline.

## How to invoke

The user types something like "bootstrap a new Angular app",
"set up an Angular frontend", "create a new SPA called X".

## What you do

### Phase 0 — Pre-flight (ask, don't guess)

Ask the user via `AskUserQuestion` (or inline questions) :

1. **Package name** (npm). Default : `<project-name>` from the current
   directory's base name, kebab-cased. Use `--name` if passed.
2. **Routing** : on / off. Default `on` — modern apps almost always
   have routes.
3. **Tailwind v4** : on / off. Default `on` — matches the project's
   sibling Angular skills (design-system, etc.) which assume Tailwind.
4. **i18n with Transloco** : on / off. Default `on`. If yes, ask which
   languages (default `fr` + `en`, `fr` is the default lang).
5. **OpenAPI client** : on / off. Default `off`. If yes, ask for the
   path to the spec (`backend/openapi/openapi.json` is the common
   default).
6. **Test stack** : Vitest (default, Angular 21 baseline) — only
   confirm.
7. **Auth shell** : on / off. Default `off`. If yes, scaffold a
   stub `login.page.ts` + auth guard.

### Phase 1 — Generate the project tree

Atomic writes. Tree (single-app, no monorepo yet) :

```
<project-root>/
├── .gitignore
├── README.md
├── package.json
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.spec.json
├── angular.json
├── vitest.config.ts
├── postcss.config.js                  # if Tailwind on
├── tailwind.config.js                 # if Tailwind on
├── public/
│   └── i18n/                          # if Transloco on
│       ├── fr.json                    # `{ "app": { "title": "{{project name}}" } }`
│       └── en.json
├── src/
│   ├── index.html
│   ├── main.ts                        # bootstrapApplication(AppComponent, appConfig)
│   ├── styles.css                     # `@import "tailwindcss";` if Tailwind on
│   └── app/
│       ├── app.ts                     # standalone root component
│       ├── app.html
│       ├── app.config.ts              # providers (router + transloco + http)
│       ├── app.routes.ts              # empty array if routing off, redirect-to-home otherwise
│       ├── core/                      # guards, interceptors (created when needed)
│       └── features/
│           └── home/
│               ├── home.page.ts
│               └── home.page.html
└── e2e/                               # ASK before scaffolding — only if user wants Playwright
```

### Phase 2 — `package.json` essentials

- Engines : `"node": ">=22"`, `"npm": ">=11"`.
- Dependencies :
  - `@angular/core`, `@angular/common`, `@angular/router` (if routing),
    `@angular/forms`, `@angular/platform-browser` — all at `21.2.0`.
  - `rxjs` 7.8.x.
  - `tslib` 2.x.
  - `tailwindcss` 4.1.x + `@tailwindcss/postcss` 4.1.x (if Tailwind).
  - `@jsverse/transloco` 8.x (if i18n).
- DevDependencies :
  - `@angular/cli`, `@angular/build`, `@angular/compiler-cli` 21.2.0.
  - `typescript` 5.5+.
  - `vitest` 3.x + `@vitest/coverage-v8`.
  - `@testing-library/angular`, `@testing-library/dom`.
  - `@playwright/test` (if e2e on).
- Scripts :
  - `"start": "ng serve"` — dev server (don't auto-run from the skill).
  - `"build": "ng build"`.
  - `"test": "vitest"`.
  - `"lint": "ng lint"` (only when `@angular-eslint` is added —
    otherwise omit).

### Phase 3 — `angular.json`

Single application called `<project-name>`, project root `src/`,
output `dist/<project-name>`, builder `@angular/build:application`,
zoneless config (Angular 21 default), `inlineStyleLanguage: css`,
`assets: ["public"]`, server hash `none`.

### Phase 4 — `tsconfig.json` family

- `strict: true`, `noImplicitOverride: true`,
  `noPropertyAccessFromIndexSignature: true`,
  `noFallthroughCasesInSwitch: true`,
  `noImplicitReturns: true`, `target: ES2022`, `module: ES2022`,
  `useDefineForClassFields: false`, `experimentalDecorators: true`.
- `tsconfig.app.json` extends root, `types: []`, `compilerOptions.outDir`.
- `tsconfig.spec.json` extends root, `types: ["vitest/globals"]`.

### Phase 5 — Root component + app config

`src/app/app.ts` :

```typescript
import { Component, ChangeDetectionStrategy } from '@angular/core';
import { RouterOutlet } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './app.html',
})
export class AppComponent {}
```

`src/app/app.config.ts` declares the provider stack — router (with
the routes from `app.routes.ts`), `provideHttpClient(withFetch())`,
Transloco providers (if i18n on), zoneless change detection
(`provideExperimentalZonelessChangeDetection()`).

`src/main.ts` bootstraps with `bootstrapApplication(AppComponent, appConfig)`.

### Phase 6 — Home page stub

`src/app/features/home/home.page.ts` standalone component with
OnPush + the project title. `home.page.html` shows `{{ projectName }}`
in an `<h1>` and a one-line welcome.

If Transloco is on, the title comes from `'app.title' | transloco` and
`fr.json` / `en.json` carry `{"app":{"title":"{{project name}}"}}`.

### Phase 7 — Tailwind v4 (if on)

`src/styles.css` :

```css
@import "tailwindcss";
```

`postcss.config.js` :

```js
module.exports = { plugins: { '@tailwindcss/postcss': {} } };
```

No `tailwind.config.js` needed for v4 unless the user wants custom
theme tokens — scaffold an empty `tailwind.config.js` only if asked.

### Phase 8 — Vitest

`vitest.config.ts` with `setupFiles: ['src/test-setup.ts']`,
`globals: true`, `environment: 'jsdom'`,
`coverage: { reporter: ['text','html','json','json-summary'] }`.

`src/test-setup.ts` imports `@analogjs/vitest-angular/setup-zone` (or
the Angular-21 zoneless equivalent).

### Phase 9 — `.gitignore` + `README.md`

`.gitignore` : standard Node + Angular ignores (`node_modules/`,
`dist/`, `coverage/`, `.angular/`, `.idea/`, `.vscode/`,
`.DS_Store`, `*.log`).

`README.md` : project title, install (`npm ci`), run (`npm start`),
build (`npm run build`), test (`npm test`), and a pointer to
`.smith/TECHNICAL_SPECIFICATION.MD` when `/smith-generate-docs` runs.

### Phase 10 — Smoke check

Run `npm ci && npm run build` once (via the consumer's `/npm` skill
if the `npm` Smith bundle is installed ; otherwise Bash). Report :
- One-line headline : `npm run build` ✅ PASS or ❌ FAIL.
- If FAIL : quote the first build error only (file:line + message).

## Quality bar

- Every generated file must be **valid TypeScript / valid JSON** and
  the project must **build cleanly** with `npm run build`.
- Angular 21 baselines : **standalone components** everywhere
  (no NgModules), **OnPush** change detection by default, **signals**
  preferred over RxJS for component state, **zoneless** change
  detection enabled in `app.config.ts`.
- Strict TypeScript (every `strict` flag on in `tsconfig.json`).
- If Tailwind is on : no custom CSS in feature components, no
  `style:` inline rules — Tailwind utilities only.
- If Transloco is on : no hard-coded UI strings ; every label goes
  through `| transloco`. Languages are kept in parity (same keys in
  `fr.json` and `en.json`).

## What you do NOT do

- Don't invent application features the user didn't ask for. Bootstrap
  produces a runnable empty SPA with the home page ; features come
  later.
- Don't add a state library (NgRx, NgXs, Akita, …). Smith's Angular
  conventions use signal stores — not a third-party state library.
- Don't add a UI kit (Angular Material, PrimeNG, Taiga UI, …). The
  Smith stack relies on Tailwind + a hand-rolled design system per
  the `angular-design-system` skill.
- Don't auto-commit. The user reviews the tree before deciding what
  goes into the first commit.
- Don't start the dev server (`ng serve` / `npm start`). `npm run build`
  is enough to validate the scaffold.

## Reporting back

```
✅ Angular 21 project scaffolded at {{project-root}}.
   Package      : {{name}}@0.0.1
   Routing      : {{on|off}}
   Tailwind v4  : {{on|off}}
   Transloco    : {{on|off}} ({{fr,en}})
   OpenAPI      : {{on|off}}
   npm build    : ✅ PASS

Next : run `/smith-generate-docs` to write the functional + technical specs.
```
