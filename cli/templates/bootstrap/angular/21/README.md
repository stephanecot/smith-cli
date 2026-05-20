# Bootstrap — Angular 21

Bootstrap template for **Angular 21**. Generates a runnable Angular 21
SPA from scratch — package, routing, optional Tailwind v4 / Transloco /
OpenAPI client — then runs `npm run build` as a smoke check.

## What ships here

```
bootstrap/angular/21/
├── config.yaml         # bootstrap metadata + assets / templates / scripts lists
├── README.md
├── CHANGELOG.md
├── skill/
│   ├── bootstrap.md    # the orchestrator body (uses {{placeholder}} markers)
│   └── metadata.yml    # name: smith-angular-bootstrap + description (+ optional model / user-invocable)
├── assets/             # (empty) — verbatim files copied into the consumer
├── templates/          # (empty) — real templates with placeholders (HTML, …)
└── scripts/            # (empty) — helper scripts (Node, …)
```

## Stack targeted

- Angular 21 (zoneless, signals, standalone APIs).
- TypeScript 5+.
- Optional : Tailwind v4, Transloco i18n, OpenAPI client.

After scaffold, pair with `framework/angular/21` (standards,
tests-coverage, design-system, i18n-transloco, openapi-client) for
post-scaffold quality + conventions.
